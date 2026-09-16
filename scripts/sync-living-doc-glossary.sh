#!/usr/bin/env bash
# sync-living-doc-glossary.sh — pull the canon glossary from AbsaOSS/living-doc and write the
# local copy that agentic-toolkit's skills load.
#
# The canon lives at living-doc's docs/guides/living-doc-glossary.md today. A later living-doc
# change relocates guides under docs/reference/ — when that lands, update SOURCE_PATH below (and
# the link-rewriting rules, which assume the source and its cross-references live under
# docs/guides/ and docs/examples/).
#
# Usage:
#   scripts/sync-living-doc-glossary.sh <living-doc-ref>
#
# <living-doc-ref> is any git ref in AbsaOSS/living-doc: a commit SHA (preferred, for
# reproducibility), a tag, or a branch name.
#
# Writes: skills/shared/references/living-doc-glossary.md
# Exits 1 if the ref is missing, the fetch fails, or the fetched file is empty.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${REPO_ROOT}/skills/shared/references/living-doc-glossary.md"
SOURCE_PATH="docs/guides/living-doc-glossary.md"
LIVING_DOC_REPO="AbsaOSS/living-doc"

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 <living-doc-ref>" >&2
  echo "  <living-doc-ref>: a commit SHA, tag, or branch in ${LIVING_DOC_REPO}" >&2
  exit 1
fi
REF="$1"

# Percent-encode REF for safe use inside a URL path segment, preserving '/' so refs that
# contain one (e.g. "feature/foo") still address the right nested path. REF is attacker/PR
# controlled (any branch, tag, or SHA in AbsaOSS/living-doc) and is dropped unescaped into
# both the curl fetch URL and the doc links rewritten below. Reserved URL characters such as
# '#' are delimiters — curl (and a browser, for the links below) treats everything from '#'
# onward as a fragment and never sends it — so a ref containing one silently truncates the
# request instead of failing loudly. Percent-encoding leaves only unreserved characters and
# '/' in the result, so the sed replacements further down need no separate escaping either.
url_encode_ref() {
  local LC_ALL=C ref="$1" i c encoded=""
  for (( i = 0; i < ${#ref}; i++ )); do
    c="${ref:i:1}"
    case "$c" in
      [a-zA-Z0-9._~-]|/) encoded+="$c" ;;
      *) encoded+=$(printf '%%%02X' "'$c") ;;
    esac
  done
  printf '%s' "$encoded"
}

REF_URL_SAFE="$(url_encode_ref "${REF}")"

RAW_URL="https://raw.githubusercontent.com/${LIVING_DOC_REPO}/${REF_URL_SAFE}/${SOURCE_PATH}"

TMP_FILE="$(mktemp)"
trap 'rm -f "${TMP_FILE}"' EXIT

echo "Fetching ${SOURCE_PATH} from ${LIVING_DOC_REPO}@${REF} ..." >&2
if ! curl -fsSL --connect-timeout 10 --max-time 30 --retry 2 "${RAW_URL}" -o "${TMP_FILE}"; then
  echo "Error: failed to fetch ${RAW_URL}" >&2
  echo "Check that the ref exists and ${SOURCE_PATH} is still the canon glossary path." >&2
  exit 1
fi

if [ ! -s "${TMP_FILE}" ]; then
  echo "Error: fetched file is empty — refusing to overwrite ${DEST}" >&2
  exit 1
fi

# Rewrite the canon's relative links to absolute living-doc URLs so the synced copy reads
# correctly from inside agentic-toolkit. Same-page anchors (#section) are left untouched.
# Known relative link shapes in the source file:
#   - "living-doc-header-types.md" / "living-doc-document-types.md" — sibling under docs/guides/
#   - "../examples/..."                                             — under docs/examples/
#
# REF_URL_SAFE is already percent-encoded (see above), so it contains only unreserved URL
# characters and '/' — none of which are special to sed's s|...|...| syntax — and can be
# dropped straight into the replacement text below with no separate escaping pass.
BLOB_BASE="https://github.com/${LIVING_DOC_REPO}/blob/${REF_URL_SAFE}"
sed -E \
  -e "s|\(living-doc-header-types\.md|(${BLOB_BASE}/docs/guides/living-doc-header-types.md|g" \
  -e "s|\(living-doc-document-types\.md|(${BLOB_BASE}/docs/guides/living-doc-document-types.md|g" \
  -e "s|\(\.\./examples/|(${BLOB_BASE}/docs/examples/|g" \
  "${TMP_FILE}" > "${TMP_FILE}.rewritten"
mv "${TMP_FILE}.rewritten" "${TMP_FILE}"

{
  echo "<!-- synced from ${LIVING_DOC_REPO}@${REF} — run scripts/sync-living-doc-glossary.sh ${REF} to refresh -->"
  echo
  cat "${TMP_FILE}"
} > "${DEST}"

echo "Wrote $(wc -l < "${DEST}") lines to ${DEST#${REPO_ROOT}/}" >&2
