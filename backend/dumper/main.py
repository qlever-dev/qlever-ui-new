#!/usr/bin/env python3
"""Fetch backend configs from API and dump as one `<slug>.yaml` per endpoint
into an output directory (qlue-ui dir-mode layout)."""

import argparse
import sys
from pathlib import Path

import requests
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

BASE_URL = "https://qlue-ls.com/api/backends/"
DEFAULT_OUTPUT_DIR = Path("config.d")


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


def fetch_backends():
    resp = requests.get(BASE_URL)
    resp.raise_for_status()
    return resp.json()


def fetch_backend_detail(api_url):
    resp = requests.get(api_url)
    resp.raise_for_status()
    return resp.json()


def restructure(data):
    """Restructure the data as needed. Edit this function to your liking.

    Output keys must match qlue-ui's `SparqlEndpointConfiguration` schema —
    unknown fields are silently dropped at load and the preset's values win.
    In particular: `default` (not `is_default`), `query_templates` (not
    `completion_templates`)."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to write <slug>.yaml files into (default: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()
    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching backends from {BASE_URL} ...", file=sys.stderr)
    backends = fetch_backends()
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


if __name__ == "__main__":
    main()
