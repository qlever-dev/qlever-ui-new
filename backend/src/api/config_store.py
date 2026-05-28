import yaml
import hashlib
import asyncio
import logging
from pathlib import Path
from typing import Any, Callable
from .models import validate_config

logger = logging.getLogger("uvicorn.error")

PRESETS_DIR = Path(__file__).parent / "presets"


class _Dumper(yaml.Dumper):
    pass


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        # YAML's literal block style (`|` / `|-`) silently falls back to a
        # quoted+escaped form when any line has trailing whitespace. Strip it so
        # multiline strings always emit cleanly.
        cleaned = "\n".join(line.rstrip() for line in data.split("\n"))
        return dumper.represent_scalar("tag:yaml.org,2002:str", cleaned, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str_representer)


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge overlay into base. Per-key for dict values, full replace
    for everything else. Neither input is mutated."""
    out = dict(base)
    for key, value in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _load_presets(presets_dir: Path) -> dict[str, dict[str, Any]]:
    if not presets_dir.is_dir():
        return {}
    presets: dict[str, dict[str, Any]] = {}
    for path in sorted(presets_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_bytes()) or {}
        if not isinstance(data, dict):
            raise ValueError(
                f"Preset {path.name} must be a YAML mapping, got {type(data).__name__}"
            )
        presets[path.stem] = data
    return presets


def _baseline(
    preset_names: list[str], presets: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Resolve a chain of presets without any endpoint-level overrides."""
    merged: dict[str, Any] = {}
    for name in preset_names:
        if name not in presets:
            raise ValueError(f"Unknown preset: {name!r}")
        merged = _deep_merge(merged, presets[name])
    return merged


def _resolve(raw: dict[str, Any], presets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Merge listed presets left-to-right, then the endpoint's own fields on top.
    Returns the resolved dict (including `preset` as informational metadata)."""
    preset_names = raw.get("preset") or []
    merged = _baseline(preset_names, presets)
    own = {k: v for k, v in raw.items() if k != "preset"}
    merged = _deep_merge(merged, own)
    merged["preset"] = list(preset_names)
    return merged


def _minimize(
    raw: dict[str, Any], presets: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Strip override values that exactly match what the preset chain provides.
    Per-key for dict values, equality for scalars. `preset` itself is preserved."""
    preset_names = raw.get("preset") or []
    baseline = _baseline(preset_names, presets)
    out: dict[str, Any] = {}
    if preset_names:
        out["preset"] = list(preset_names)
    for key, value in raw.items():
        if key == "preset":
            continue
        baseline_value = baseline.get(key)
        if isinstance(value, dict):
            bdict = baseline_value if isinstance(baseline_value, dict) else {}
            diff = {k: v for k, v in value.items() if bdict.get(k) != v}
            if diff:
                out[key] = diff
        else:
            if value != baseline_value:
                out[key] = value
    return out


class ConfigStore:
    """Thread/async-safe wrapper around the in-memory YAML data.

    Two layers:
      * `_raw` mirrors disk verbatim (with `preset:` references and explicit
        overrides). It is the source of truth and what gets persisted.
      * `_resolved` is the merged form returned to API consumers.
    """

    def __init__(self, filepath: Path, presets_dir: Path = PRESETS_DIR) -> None:
        self._raw: dict[str, dict[str, Any]] = {}
        self._resolved: dict[str, dict[str, Any]] = {}
        self._presets: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._file_hash: str = ""
        self._file_path = filepath
        self._presets_dir = presets_dir

    async def load(self) -> int:
        async with self._lock:
            self._presets = _load_presets(self._presets_dir)
            logger.info(
                f"Loaded {len(self._presets)} preset{'s' if len(self._presets) != 1 else ''}: "
                f"{', '.join(sorted(self._presets)) or '—'}"
            )
            if self._file_path.exists():
                raw_bytes = self._file_path.read_bytes()
                self._file_hash = hashlib.sha256(raw_bytes).hexdigest()
                parsed = yaml.safe_load(raw_bytes) or {}
                if not isinstance(parsed, dict):
                    raise ValueError("Top-level config must be a YAML mapping")
                self._raw = parsed
                self._resolved = self._resolve_all(self._raw)
                return len(self._resolved)
            self._raw = {}
            self._resolved = {}
            self._file_hash = ""
            return 0

    def _resolve_all(self, raw: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        resolved_unvalidated = {
            slug: _resolve(block, self._presets) for slug, block in raw.items()
        }
        return validate_config(resolved_unvalidated)

    async def get_all(self) -> dict[str, Any]:
        """Return the resolved view. DO NOT mutate the result."""
        async with self._lock:
            return self._resolved

    async def create(self, slug: str, config: dict[str, Any]):
        async with self._lock:
            if slug in self._raw:
                raise ValueError(f"config with slug {slug} already exists.")
            minimized = _minimize(config, self._presets)
            new_raw = {**self._raw, slug: minimized}
            new_resolved = self._resolve_all(new_raw)
            # NOTE: Make sure only one config is the "default" endpoint.
            if new_resolved[slug].get("default"):
                for other in new_raw:
                    if other != slug:
                        new_raw[other]["default"] = False
                new_resolved = self._resolve_all(new_raw)
            self._raw = new_raw
            self._resolved = new_resolved
            self._persist()

    async def patch(
        self, slug: str, apply: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> dict[str, Any]:
        """Read-modify-write an endpoint atomically.

        *apply* receives the current stored raw dict and must return the new raw
        dict. Raises KeyError if the slug does not exist. Rolls back on failure.
        """
        async with self._lock:
            if slug not in self._raw:
                raise KeyError(slug)
            prev_raw = self._raw[slug]
            prev_resolved = self._resolved[slug]
            new_raw_block = _minimize(apply(prev_raw), self._presets)
            new_raw = {**self._raw, slug: new_raw_block}
            try:
                new_resolved = self._resolve_all(new_raw)
                self._raw = new_raw
                self._resolved = new_resolved
                self._persist()
            except Exception:
                self._raw[slug] = prev_raw
                self._resolved[slug] = prev_resolved
                raise
            return self._resolved[slug]

    def _persist(self) -> None:
        """Atomically write the raw state back to the YAML file."""
        raw = yaml.dump(
            self._raw,
            Dumper=_Dumper,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        tmp = self._file_path.with_suffix(".tmp")
        tmp.write_text(raw)
        tmp.replace(self._file_path)
        self._file_hash = hashlib.sha256(raw.encode()).hexdigest()
