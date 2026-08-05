#!/usr/bin/env bash
# install.sh - copy codex-teammode-workflow into a target project and print the bootstrap prompt.
#
# Usage:
#   ./install.sh [options] [target-project]
#
# Options:
#   --dry-run                 Show workflow and optional skill targets only.
#   --force                   Replace an existing workflow package target.
#   --no-clipboard            Do not copy the bootstrap prompt.
#   --install-docs-review     Explicitly install the bundled docs-review skill.
#   --skill-root PATH         Skill parent directory (default: Codex user skills).
#   --force-skill             Back up and replace only an existing docs-review skill.
#
# After running, paste the printed prompt into Codex or Claude Code in the
# target project. The agent will adapt the workflow to that repo.

set -euo pipefail

FORCE=0
DRY_RUN=0
CLIPBOARD=1
INSTALL_DOCS_REVIEW=0
FORCE_SKILL=0
SKILL_ROOT_SET=0
SKILL_ROOT_RAW=""
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
    --install-docs-review)
      INSTALL_DOCS_REVIEW=1
      ;;
    --skill-root)
      if [[ $# -lt 2 ]]; then
        echo "error: --skill-root requires a path." >&2
        exit 1
      fi
      SKILL_ROOT_RAW="$2"
      SKILL_ROOT_SET=1
      shift
      ;;
    --force-skill)
      FORCE_SKILL=1
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

if [[ "$SKILL_ROOT_SET" -eq 1 && "$INSTALL_DOCS_REVIEW" -ne 1 ]]; then
  echo "error: --skill-root requires --install-docs-review." >&2
  exit 1
fi

if [[ "$FORCE_SKILL" -eq 1 && "$INSTALL_DOCS_REVIEW" -ne 1 ]]; then
  echo "error: --force-skill requires --install-docs-review." >&2
  exit 1
fi

if [[ -z "$TARGET" ]]; then
  echo "error: target directory '$TARGET_RAW' does not exist." >&2
  exit 1
fi

if [[ "$TARGET" == "$KIT_ROOT" ]]; then
  echo "error: target is this workflow repo. Pass a different directory." >&2
  exit 1
fi

DEST="$TARGET/codex-teammode-workflow"
SKILL_SOURCE="$KIT_ROOT/skills/docs-review"

if [[ "$DEST" == "$KIT_ROOT" ]]; then
  echo "error: target would overwrite this workflow repo. Pass another directory." >&2
  exit 1
fi

if [[ "$INSTALL_DOCS_REVIEW" -eq 1 ]]; then
  if [[ "$SKILL_ROOT_SET" -eq 0 ]]; then
    if [[ -n "${CODEX_HOME:-}" ]]; then
      SKILL_ROOT_RAW="$CODEX_HOME/skills"
    else
      SKILL_ROOT_RAW="${HOME:?HOME is required when CODEX_HOME is unset}/.codex/skills"
    fi
  fi
  if [[ "$SKILL_ROOT_RAW" != "/" ]]; then
    SKILL_ROOT_RAW="${SKILL_ROOT_RAW%/}"
  fi
  if [[ -z "$SKILL_ROOT_RAW" || "$SKILL_ROOT_RAW" == "/" ]]; then
    echo "error: skill root must not be empty or filesystem root." >&2
    exit 1
  fi
  if [[ "$SKILL_ROOT_RAW" == /* ]]; then
    SKILL_ROOT="$SKILL_ROOT_RAW"
  else
    SKILL_ROOT="$PWD/$SKILL_ROOT_RAW"
  fi
  SKILL_DEST="$SKILL_ROOT/docs-review"
  if [[ ! -d "$SKILL_SOURCE" ]]; then
    echo "error: bundled docs-review skill is missing: $SKILL_SOURCE" >&2
    exit 1
  fi
fi

PAYLOAD=(
  "BOOTSTRAP_PROMPT.md"
  "UPDATE_PROMPT.md"
  "UPDATE_MANIFEST.md"
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
  "skills"
)

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run: would copy codex-teammode-workflow into: $DEST"
  echo "Payload:"
  for item in "${PAYLOAD[@]}"; do
    echo "  - $item"
  done
  echo
  if [[ "$INSTALL_DOCS_REVIEW" -eq 1 ]]; then
    echo "Optional docs-review skill target: $SKILL_DEST"
    if [[ ! -e "$SKILL_DEST" ]]; then
      echo "Skill action: install"
    elif [[ -d "$SKILL_DEST" ]] && diff -qr "$SKILL_SOURCE" "$SKILL_DEST" >/dev/null; then
      echo "Skill action: no-op (already identical)"
    elif [[ "$FORCE_SKILL" -eq 1 ]]; then
      echo "Skill action: back up and replace exact docs-review target"
    else
      echo "Skill action: refuse (target differs; pass --force-skill to back up and replace)"
    fi
  else
    echo "Optional docs-review skill: not requested; no global skill directory would change."
  fi
  exit 0
fi

if [[ "$INSTALL_DOCS_REVIEW" -eq 1 && -e "$SKILL_DEST" ]]; then
  if [[ -d "$SKILL_DEST" ]] && diff -qr "$SKILL_SOURCE" "$SKILL_DEST" >/dev/null; then
    SKILL_ACTION="noop"
  elif [[ "$FORCE_SKILL" -eq 1 ]]; then
    SKILL_ACTION="replace"
  else
    echo "error: $SKILL_DEST exists and differs from the bundled docs-review skill." >&2
    echo "       Re-run with --force-skill to create a backup and replace only that directory." >&2
    exit 1
  fi
elif [[ "$INSTALL_DOCS_REVIEW" -eq 1 ]]; then
  SKILL_ACTION="install"
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

if [[ "$INSTALL_DOCS_REVIEW" -eq 1 ]]; then
  mkdir -p "$SKILL_ROOT"
  case "$SKILL_ACTION" in
    noop)
      echo "Docs Review skill already identical; no-op: $SKILL_DEST"
      ;;
    install)
      cp -R "$SKILL_SOURCE" "$SKILL_DEST"
      echo "Installed Docs Review skill into: $SKILL_DEST"
      ;;
    replace)
      SKILL_BACKUP_TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
      SKILL_BACKUP="$SKILL_ROOT/docs-review.backup.$SKILL_BACKUP_TIMESTAMP"
      SKILL_BACKUP_SUFFIX=1
      while [[ -e "$SKILL_BACKUP" ]]; do
        SKILL_BACKUP="$SKILL_ROOT/docs-review.backup.$SKILL_BACKUP_TIMESTAMP-$SKILL_BACKUP_SUFFIX"
        SKILL_BACKUP_SUFFIX=$((SKILL_BACKUP_SUFFIX + 1))
      done
      mv "$SKILL_DEST" "$SKILL_BACKUP"
      if cp -R "$SKILL_SOURCE" "$SKILL_DEST"; then
        echo "Backed up previous Docs Review skill to: $SKILL_BACKUP"
        echo "Installed Docs Review skill into: $SKILL_DEST"
      else
        if [[ -e "$SKILL_DEST" ]]; then
          SKILL_FAILED="$SKILL_ROOT/docs-review.failed.$SKILL_BACKUP_TIMESTAMP"
          mv "$SKILL_DEST" "$SKILL_FAILED"
          echo "warning: partial skill copy preserved at: $SKILL_FAILED" >&2
        fi
        mv "$SKILL_BACKUP" "$SKILL_DEST"
        echo "error: skill install failed; previous docs-review skill was restored." >&2
        exit 1
      fi
      ;;
  esac
fi

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
