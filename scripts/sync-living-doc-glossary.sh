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

RAW_URL="https://raw.githubusercontent.com/${LIVING_DOC_REPO}/${REF}/${SOURCE_PATH}"

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
# REF is attacker-controllable input (any branch/tag name) and lands in the replacement side
# of the sed commands below. Escape backslash, ampersand (sed's "insert the match" token), and
# the "|" delimiter those commands use, so a ref like "release&docs" can't corrupt the rewritten
# links or break the command.
REF_SED_SAFE="$(printf '%s' "${REF}" | sed -e 's/[\&|]/\\&/g')"
BLOB_BASE="https://github.com/${LIVING_DOC_REPO}/blob/${REF_SED_SAFE}"
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
