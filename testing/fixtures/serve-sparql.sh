#!/usr/bin/env bash
# Boot a throwaway Oxigraph SPARQL endpoint seeded with the e2e test dataset.
# Loads dataset.ttl into a fresh temp store, then serves it read-only with CORS
# enabled (the browser fetches the endpoint cross-origin from localhost:5173).
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
port="${OXIGRAPH_PORT:-7878}"
store="$(mktemp -d)"
trap 'rm -rf "$store"' EXIT

oxigraph load --location "$store" --file "$here/dataset.ttl"
exec oxigraph serve-read-only \
  --location "$store" \
  --bind "127.0.0.1:${port}" \
  --cors
