#!/usr/bin/env bash
# Durable execution launcher for AdaL + Pi over SSH / Termius.
# Keeps the Mac/VPS awake (caffeinate on macOS), creates a persistent 3-window
# tmux session ("vultr-hack"), and survives SSH disconnects, laptop lid closes
# (when plugged in), or phone network switches.
#
# Usage:
#   ./scripts/durable-tmux.sh          # create or attach to tmux session "vultr-hack"
#   tmux attach -t vultr-hack          # from Termius on your phone

set -euo pipefail

SESSION="vultr-hack"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Attaching to existing durable tmux session '$SESSION'..."
  exec tmux attach -t "$SESSION"
fi

echo "Creating durable tmux session '$SESSION' in $REPO_DIR..."

# Window 0: adal (Engineer mode, persistent TUI)
tmux new-session -d -s "$SESSION" -n "adal" -c "$REPO_DIR"
if command -v caffeinate >/dev/null 2>&1; then
  tmux send-keys -t "$SESSION:adal" "caffeinate -dimsu zsh" C-m
fi
tmux send-keys -t "$SESSION:adal" "clear && echo '=== Window 0: AdaL (run: adal --agent-mode engineer) ==='" C-m

# Window 1: pi (Persistent session ID so pi -c / --session-id always resumes)
tmux new-window -t "$SESSION" -n "pi" -c "$REPO_DIR"
tmux send-keys -t "$SESSION:pi" "clear && echo '=== Window 1: Pi (run: pi --session-id vultr-eval-gym @docs/adal/NEXT_SESSION_PROMPT.md) ==='" C-m

# Window 2: server & logs (FastAPI + selftest + cloudflared tunnel)
tmux new-window -t "$SESSION" -n "ops" -c "$REPO_DIR"
tmux send-keys -t "$SESSION:ops" "clear && echo '=== Window 2: Ops / Server / Tunnel ===' && git status -sb" C-m

tmux select-window -t "$SESSION:adal"
exec tmux attach -t "$SESSION"
