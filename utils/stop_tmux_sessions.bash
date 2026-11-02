#!/bin/bash

usage() {
    echo "  Add tmux session names as arguments"
}

# Get tmux_session_list from command-line argument
tmux_session_list=("$@")

# If inside tmux session, get the current session name
if [[ -n "$TMUX" ]]; then
  current_session=$(tmux display-message -p '#S')
fi

# Send Ctrl+C signal to each pane of each session
# (targeting a window only reaches its active pane, so list every pane)
for session in "${tmux_session_list[@]}"; do
  # Check if session exists
  if tmux has-session -t "$session" 2>/dev/null; then
    # Get the list of panes in all windows of the session
    panes=($(tmux list-panes -s -t "$session" -F "#{pane_id}"))
    # Iterate through each pane and send Ctrl+C
    for pane in "${panes[@]}"; do
      tmux send-keys -t "$pane" C-c
      sleep 0.1 # Add a small delay to allow the signal to be processed
    done
  fi
done

# Kill all tmux sessions from the list except for the current one
for session in "${tmux_session_list[@]}"; do
  if [[ "$session" != "$current_session" ]]; then
    tmux kill-session -t "$session" 2>/dev/null
  fi
done

# Kill the current tmux session, if in a tmux session
if [[ -n "$TMUX" ]]; then
  tmux kill-session -t "$current_session" 2>/dev/null
fi