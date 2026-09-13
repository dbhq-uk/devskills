#!/bin/bash
# Install every skill in this pack into ~/.claude/skills/ as a live symlink.
#
# A SKILL.md references its scripts via ${CLAUDE_SKILL_DIR}, which Claude Code
# substitutes to the skill's own directory for personal, project, and plugin
# installs alike. So this script symlinks the whole skill directory into
# ~/.claude/skills/ - every edit (scripts AND SKILL.md) is immediately live,
# with no per-file rewrite. Re-run only when you add a new skill directory.
#
# It does not run any skill's setup for you. This is a pack, and launching one
# member's interactive credential prompt on install of the whole pack is
# surprising - the setup commands are printed at the end instead.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$HOME/.claude/skills"

echo "=== devskills installer (Claude Code) ==="
echo

# --- Dependencies ---
# A warning, not a failure: each skill needs its own subset, so a missing tool
# blocks that one skill rather than the install.
MISSING=""
command -v jq >/dev/null 2>&1      || MISSING="$MISSING jq(jira)"
command -v curl >/dev/null 2>&1    || MISSING="$MISSING curl(jira)"
command -v python3 >/dev/null 2>&1 || MISSING="$MISSING python3(gitview)"
command -v git >/dev/null 2>&1     || MISSING="$MISSING git(gitview)"
if [ -n "$MISSING" ]; then
  echo "Missing, with the skill that needs it:$MISSING"
  echo "The rest of the pack still installs."
else
  echo "Dependencies OK."
fi
echo

# --- Install each skill in this pack as a full-directory symlink ---
mkdir -p "$SKILLS_ROOT"
for src in "$SCRIPT_DIR"/skills/*/; do
  src="${src%/}"
  name="$(basename "$src")"
  target="$SKILLS_ROOT/$name"
  echo "Installing '$name' -> $target"
  rm -rf "$target"            # replace any prior copy or partial-symlink install
  ln -sfn "$src" "$target"    # whole-directory symlink; ${CLAUDE_SKILL_DIR} resolves it
  chmod +x "$src"/scripts/*.sh 2>/dev/null || true
done

echo
echo "Installed as directory symlinks - all edits (scripts and SKILL.md) are live."

# --- Setup scripts, if any skill has one ---
SETUPS="$(find "$SCRIPT_DIR"/skills -type f -name '*-setup.sh' | sort)"
if [ -n "$SETUPS" ]; then
  echo
  echo "These skills need credentials before first use:"
  while IFS= read -r setup; do
    name="$(basename "$(dirname "$(dirname "$setup")")")"
    echo "  $name:  $SKILLS_ROOT/$name/scripts/$(basename "$setup")"
  done <<< "$SETUPS"
fi

echo
echo "Done. Try: 'survey the branches in this repo' or 'what Jira projects can I see'"
