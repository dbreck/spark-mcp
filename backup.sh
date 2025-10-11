#!/bin/bash
# Quick backup before making changes
VERSION=$(grep "Version:" src/index.ts | head -1 | sed 's/.*Version: //' | sed 's/ .*//')
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
git add .
git commit -m "Backup: v$VERSION - $TIMESTAMP"
echo "✓ Backed up to commit $(git rev-parse --short HEAD)"
