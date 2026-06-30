#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SRC_DIR="$ROOT_DIR/skills/bug-check"
if [ "${AGENT_SKILLS_DIR:-}" = "" ]; then
  echo "Set AGENT_SKILLS_DIR to your agent runtime's skills directory." >&2
  exit 1
fi

SKILLS_DIR="$AGENT_SKILLS_DIR"
DEST_DIR="$SKILLS_DIR/bug-check"

if [ ! -f "$SRC_DIR/SKILL.md" ]; then
  echo "Missing skill source: $SRC_DIR/SKILL.md" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
rsync -a --delete --exclude ".DS_Store" "$SRC_DIR/" "$DEST_DIR/"

echo "Installed bug-check skill to $DEST_DIR"
echo "Restart or open a new agent session if the skill list was already loaded."
