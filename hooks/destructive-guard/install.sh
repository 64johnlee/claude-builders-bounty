#!/usr/bin/env bash
# Install destructive-guard into Claude Code hooks.
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
HOOK_SRC="$(cd "$(dirname "$0")" && pwd)/hook.py"
HOOK_DEST="$HOOK_DIR/destructive-guard.py"
SETTINGS="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$HOOK_SRC" "$HOOK_DEST"
chmod +x "$HOOK_DEST"

python3 - "$HOOK_DEST" "$SETTINGS" <<'PYEOF'
import json, sys
from pathlib import Path

hook_path, settings_path = sys.argv[1], Path(sys.argv[2])
cfg = json.loads(settings_path.read_text()) if settings_path.exists() else {}
pre = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": f"python3 {hook_path}"}]}
if not any(h.get("matcher") == "Bash" for h in pre):
    pre.append(entry)
settings_path.write_text(json.dumps(cfg, indent=2) + "\n")
PYEOF

echo "destructive-guard installed at $HOOK_DEST"
echo "Blocking: rm -rf | DROP TABLE | TRUNCATE | DELETE FROM (no WHERE) | git push --force"
echo "Log: ~/.claude/hooks/blocked.log"
