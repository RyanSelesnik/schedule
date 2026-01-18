#!/bin/bash
# Quick sync script - commit and push all changes
# Usage: ./scripts/sync.sh [commit message]

cd "$(dirname "$0")/.." || exit 1

# Default commit message
MSG="${1:-Update progress}"

# Check if there are changes
if [[ -z $(git status -s) ]]; then
    echo "Nothing to sync - working tree clean"
    exit 0
fi

# Show what will be committed
echo "Changes to sync:"
git status -s
echo ""

# Commit and push
git add -A
git commit -m "$MSG

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
git push

echo ""
echo "Synced successfully!"
