#!/bin/bash
# Custom status line for Claude Code
# Displays model name and current directory

# Read JSON input from stdin
input=$(cat)

# Extract values using jq
MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
DIR_NAME=$(basename "$DIR")

# Output status line (first line of stdout)
echo "[$MODEL] 📁 $DIR_NAME"
