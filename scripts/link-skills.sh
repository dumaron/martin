#!/usr/bin/env bash
# Expose the repo's vendor-neutral skills/ playbooks to AI tools that expect them
# in their own (gitignored) config directory. Safe to re-run.
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p .claude/skills
for skill in skills/*/; do
	ln -sfn "../../$skill" ".claude/skills/$(basename "$skill")"
done

mkdir -p .junie
ln -sfn ../AGENTS.md .junie/guidelines.md

echo "Linked .claude/skills/* -> skills/* and .junie/guidelines.md -> AGENTS.md"
