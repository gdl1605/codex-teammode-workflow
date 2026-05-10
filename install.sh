#!/usr/bin/env bash
# install.sh - copy codex-teammode-workflow into a target project and print the bootstrap prompt.
#
# Usage:
#   ./install.sh [--dry-run] [--force] [--no-clipboard] [target-project]
#
# After running, paste the printed prompt into Codex or Claude Code in the
# target project. The agent will adapt the workflow to that repo.

set -euo pipefail

FORCE=0
DRY_RUN=0
CLIPBOARD=1
TARGET_RAW="."
TARGET_SET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      FORCE=1
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    --no-clipboard)
      CLIPBOARD=0
      ;;
    -h|--help)
      sed -n '1,16p' "$0"
      exit 0
      ;;
    -*)
      echo "error: unknown option '$1'." >&2
      exit 1
      ;;
    *)
      if [[ "$TARGET_SET" -eq 1 ]]; then
        echo "error: only one target project path is allowed." >&2
        exit 1
      fi
      TARGET_RAW="$1"
      TARGET_SET=1
      ;;
  esac
  shift
done

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$(cd "$TARGET_RAW" 2>/dev/null && pwd || true)"

if [[ -z "$TARGET" ]]; then
  echo "error: target directory '$TARGET_RAW' does not exist." >&2
  exit 1
fi

if [[ "$TARGET" == "$KIT_ROOT" ]]; then
  echo "error: target is this workflow repo. Pass a different directory." >&2
  exit 1
fi

DEST="$TARGET/codex-teammode-workflow"

PAYLOAD=(
  "BOOTSTRAP_PROMPT.md"
  "MANIFEST.md"
  "CURRENT_DOCS_STRUCTURE.md"
  "README.md"
  "README.zh-CN.md"
  "CONCEPTS.md"
  "FAQ.md"
  "CONTRIBUTING.md"
  "SECURITY.md"
  "CODE_OF_CONDUCT.md"
  "SUPPORT.md"
  "ROADMAP.md"
  "RELEASE_NOTES.md"
  "CHANGELOG.md"
  "LICENSE"
  "workflow-kernel"
  "docs-structure-template"
  "examples"
)

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run: would copy codex-teammode-workflow into: $DEST"
  echo "Payload:"
  for item in "${PAYLOAD[@]}"; do
    echo "  - $item"
  done
  exit 0
fi

if [[ -e "$DEST" ]]; then
  if [[ "$FORCE" -eq 1 ]]; then
    rm -rf "$DEST"
  else
    echo "warning: $DEST already exists." >&2
    read -r -p "Overwrite? [y/N] " ans
    case "$ans" in
      y|Y|yes|YES) rm -rf "$DEST" ;;
      *) echo "aborted."; exit 1 ;;
    esac
  fi
fi

mkdir -p "$DEST"

for item in "${PAYLOAD[@]}"; do
  cp -R "$KIT_ROOT/$item" "$DEST/"
done

echo
echo "Copied codex-teammode-workflow into: $DEST"
echo

if [[ "$CLIPBOARD" -eq 1 ]]; then
  if command -v pbcopy >/dev/null 2>&1; then
    pbcopy < "$KIT_ROOT/BOOTSTRAP_PROMPT.md"
    echo "Bootstrap prompt copied to clipboard (macOS pbcopy)."
  elif command -v wl-copy >/dev/null 2>&1; then
    wl-copy < "$KIT_ROOT/BOOTSTRAP_PROMPT.md"
    echo "Bootstrap prompt copied to clipboard (wl-copy)."
  elif command -v xclip >/dev/null 2>&1; then
    xclip -selection clipboard < "$KIT_ROOT/BOOTSTRAP_PROMPT.md"
    echo "Bootstrap prompt copied to clipboard (xclip)."
  else
    echo "No clipboard tool found (pbcopy / wl-copy / xclip). Prompt printed below."
  fi
else
  echo "Clipboard copy skipped (--no-clipboard). Prompt printed below."
fi

echo
echo "--- Bootstrap prompt (paste into Codex or Claude Code) ------------------------"
cat "$KIT_ROOT/BOOTSTRAP_PROMPT.md"
echo "--- end of bootstrap prompt ---------------------------------------------------"
echo
echo "Next steps:"
echo "  1. cd $TARGET"
echo "  2. Open Codex or Claude Code in this directory."
echo "  3. Paste the prompt above as your first message."
echo "  4. The agent will stop at human_acceptance_required for you to review."
