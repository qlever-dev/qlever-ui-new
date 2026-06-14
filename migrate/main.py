#!/usr/bin/env python3
"""Dump qlue-ui state from external sources into the on-disk dir-mode layout.

Subcommands:
  configs         Fetch backend configs from a qlue-ui API and write one
                  <slug>.yaml per endpoint.
  examples        Migrate example queries from a legacy qlever-ui Django
                  SQLite DB into examples/<slug>/example-NNN.rq files.
  shared-queries  Migrate shared queries (backend_link) from a legacy
                  qlever-ui Django SQLite DB into the qlue-ui shared_query
                  table.
"""

import argparse
import hashlib
import sqlite3
import sys
from datetime import date
from io import StringIO
from pathlib import Path

import requests
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

DEFAULT_BASE_URL = "https://qlue-ls.com/api/backends/"
DEFAULT_CONFIGS_DIR = Path("config.d")
DEFAULT_EXAMPLES_DIR = Path("examples")

# Frontmatter format used by backend/src/api/example_store.py.
_FRONTMATTER_PREFIX = "#+"
_TITLE_KEY = "title"


# ── configs ────────────────────────────────────────────────────────────────


def make_block_strings(obj):
    """Recursively convert any multiline strings to LiteralScalarString (|-) style."""
    if isinstance(obj, str):
        obj = obj.replace("\r\n", "\n")
        # Remove empty lines
        obj = "\n".join(line for line in obj.split("\n") if line.strip())
        if "\n" in obj:
            return LiteralScalarString(obj)
        return obj
    elif isinstance(obj, dict):
        return {k: make_block_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_block_strings(item) for item in obj]
    return obj


def fetch_backends(base_url):
    resp = requests.get(base_url)
    resp.raise_for_status()
    return resp.json()


def fetch_backend_detail(api_url):
    resp = requests.get(api_url)
    resp.raise_for_status()
    return resp.json()


def restructure(data):
    """Restructure the data as needed. Edit this function to your liking.

    Output keys must match qlue-ui's `SparqlEndpointConfiguration` schema —
    unknown fields are now rejected at load (extra=forbid). In particular:
    `default` (not `is_default`), `query_templates` (not `completion_templates`)."""
    result = {
        "name": data["name"],
        "url": data["url"],
        "default": data["is_default"],
        "sort_key": data["sort_key"],
        "engine": data["engine"],
        "map_view_url": data["map_view_url"],
        "prefix_map": data["prefix_map"],
        "query_templates": {
            "subject_completion": data["subject_completion"],
            "predicate_completion_context_sensitive": data[
                "predicate_completion_context_sensitive"
            ],
            "predicate_completion_context_insensitive": data[
                "predicate_completion_context_insensitive"
            ],
            "object_completion_context_sensitive": data[
                "object_completion_context_sensitive"
            ],
            "object_completion_context_insensitive": data[
                "object_completion_context_insensitive"
            ],
            "values_completion_context_sensitive": data[
                "values_completion_context_sensitive"
            ],
            "values_completion_context_insensitive": data[
                "values_completion_context_insensitive"
            ],
            "hover": data["hover"],
        },
    }
    return result


def cmd_configs(args):
    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching backends from {args.base_url} ...", file=sys.stderr)
    backends = fetch_backends(args.base_url)
    print(f"Found {len(backends)} backends.", file=sys.stderr)

    yaml = YAML()
    yaml.default_flow_style = False

    for b in backends:
        slug = b["slug"]
        print(f"  Fetching detail for {slug} ...", file=sys.stderr)
        detail = fetch_backend_detail(b["api_url"])
        block = make_block_strings(restructure(detail))
        target = out_dir / f"{slug}.yaml"
        with target.open("w") as f:
            yaml.dump(block, f)
        print(f"    wrote {target}", file=sys.stderr)


# ── examples ───────────────────────────────────────────────────────────────


def _build_example_content(name: str, query: str) -> str:
    """Render a .rq file body with `#+ title: <name>` frontmatter. Matches the
    format produced by backend/src/api/example_store.py so the migrated files
    round-trip through `name_of` cleanly."""
    yaml = YAML(typ="safe")
    yaml.default_flow_style = False
    buf = StringIO()
    yaml.dump({_TITLE_KEY: name}, buf)
    dumped = buf.getvalue().rstrip("\n")
    frontmatter = "\n".join(
        f"{_FRONTMATTER_PREFIX} {line}" if line else _FRONTMATTER_PREFIX
        for line in dumped.splitlines()
    )
    return f"{frontmatter}\n\n{query}"


def cmd_examples(args):
    db_path: Path = args.db
    out_dir: Path = args.output_dir

    if not db_path.is_file():
        sys.exit(f"DB file not found: {db_path}")

    print(f"Reading examples from {db_path} ...", file=sys.stderr)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT b.slug, e.name, e.query "
            "FROM backend_example e JOIN backend_backend b ON e.backend_id = b.id "
            "ORDER BY b.slug, e.sortKey, e.id"
        ).fetchall()
    finally:
        conn.close()

    by_slug: dict[str, list[tuple[str, str]]] = {}
    for slug, name, query in rows:
        # Legacy DB stores some entries with Windows line endings — normalize.
        name = name.replace("\r\n", "\n")
        query = query.replace("\r\n", "\n")
        by_slug.setdefault(slug, []).append((name, query))

    total = 0
    for slug, items in sorted(by_slug.items()):
        slug_dir = out_dir / slug
        slug_dir.mkdir(parents=True, exist_ok=True)
        for i, (name, query) in enumerate(items, start=1):
            target = slug_dir / f"example-{i:03d}.rq"
            target.write_text(_build_example_content(name, query))
        print(f"  wrote {len(items):>3} examples to {slug_dir}/", file=sys.stderr)
        total += len(items)
    print(
        f"Migrated {total} examples across {len(by_slug)} endpoints.", file=sys.stderr
    )


# ── shared queries ─────────────────────────────────────────────────────────


def _normalize_query(query: str) -> str:
    """Match backend/src/api/query_store.py's normalization so the hash agrees
    with what `save()` would compute for the same input."""
    return query.replace("\r\n", "\n").replace("\r", "\n")


def _hash_query(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()


def cmd_shared_queries(args):
    source: Path = args.db
    target: Path = args.target_db

    if not source.is_file():
        sys.exit(f"Source DB not found: {source}")
    if not target.is_file():
        sys.exit(
            f"Target DB not found: {target}. Start qlue-ui once so it creates "
            f"the shared_query schema, then re-run."
        )

    print(f"Reading backend_link from {source} ...", file=sys.stderr)
    src_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    try:
        rows = src_conn.execute(
            "SELECT identifier, content FROM backend_link ORDER BY id"
        ).fetchall()
    finally:
        src_conn.close()

    if not rows:
        print("No rows in backend_link; nothing to migrate.", file=sys.stderr)
        return

    normalized = [(ident, _normalize_query(content)) for ident, content in rows]

    tgt_conn = sqlite3.connect(target)
    try:
        if (
            tgt_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='shared_query'"
            ).fetchone()
            is None
        ):
            sys.exit(
                f"Target DB {target} has no `shared_query` table. Start qlue-ui "
                f"once so it creates the schema, then re-run."
            )

        existing_ids = {
            r[0] for r in tgt_conn.execute("SELECT id FROM shared_query").fetchall()
        }
        conflicts = [ident for ident, _ in normalized if ident in existing_ids]
        if conflicts:
            preview = "\n".join(f"  - {c}" for c in conflicts[:20])
            tail = (
                f"\n  ... ({len(conflicts) - 20} more)" if len(conflicts) > 20 else ""
            )
            sys.exit(
                f"Aborting: {len(conflicts)} identifier(s) already exist in target:\n"
                f"{preview}{tail}"
            )

        today = date.today().isoformat()
        with tgt_conn:
            tgt_conn.executemany(
                "INSERT INTO shared_query (id, query, query_hash, creation_date) "
                "VALUES (?, ?, ?, ?)",
                [(ident, q, _hash_query(q), today) for ident, q in normalized],
            )
    finally:
        tgt_conn.close()

    print(f"Migrated {len(normalized)} shared queries into {target}.", file=sys.stderr)


# ── CLI ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cfg = sub.add_parser("configs", help="Dump backend configs as <slug>.yaml files")
    p_cfg.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_CONFIGS_DIR,
        help=f"Directory to write <slug>.yaml files into (default: {DEFAULT_CONFIGS_DIR})",
    )
    p_cfg.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"qlue-ui backends API URL (default: {DEFAULT_BASE_URL})",
    )
    p_cfg.set_defaults(func=cmd_configs)

    p_ex = sub.add_parser(
        "examples", help="Migrate examples from a legacy qlever-ui SQLite DB"
    )
    p_ex.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_EXAMPLES_DIR,
        help=f"Directory to write examples/<slug>/example-NNN.rq into (default: {DEFAULT_EXAMPLES_DIR})",
    )
    p_ex.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Path to the qleverui.sqlite3 database",
    )
    p_ex.set_defaults(func=cmd_examples)

    p_sq = sub.add_parser(
        "shared-queries",
        help="Migrate shared queries from a legacy qlever-ui SQLite DB",
    )
    p_sq.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Path to the source qleverui.sqlite3 database",
    )
    p_sq.add_argument(
        "--target-db",
        type=Path,
        required=True,
        help="Path to the qlue-ui shared queries SQLite DB (must already exist)",
    )
    p_sq.set_defaults(func=cmd_shared_queries)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
