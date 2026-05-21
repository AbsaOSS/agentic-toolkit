#!/usr/bin/env bash
# fetch_pr.sh — Fetch PR diff and changed file list using the gh CLI.
#
# Usage:
#   ./fetch_pr.sh <PR_NUMBER> [REPO]
#
# Examples:
#   ./fetch_pr.sh 42
#   ./fetch_pr.sh 42 owner/repo
#
# Output:
#   Prints the PR description, then the diff to stdout.
#   Writes the changed file list to /tmp/pr_files.txt for use by classify_sections.py.
#
# Requirements: gh CLI authenticated (gh auth status)

set -euo pipefail

PR="${1:?Usage: fetch_pr.sh <PR_NUMBER> [REPO]}"
REPO_ARGS=()
[ -n "${2:-}" ] && REPO_ARGS=("--repo" "$2")

echo "=== PR Description ==="
gh pr view "$PR" "${REPO_ARGS[@]}" --json title,body,author \
  --template '# {{.title}}
Author: {{.author.login}}

{{.body}}'

echo ""
echo "=== Changed Files ==="
gh pr view "$PR" "${REPO_ARGS[@]}" --json files \
  --jq '.files[].path' | tee /tmp/pr_files.txt

echo ""
echo "=== Diff ==="
gh pr diff "$PR" "${REPO_ARGS[@]}"
