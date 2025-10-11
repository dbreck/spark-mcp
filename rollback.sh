#!/bin/bash
# Rollback to last working version
if [ -z "$1" ]; then
  echo "Available working versions:"
  git tag -l "*-working" | sort -V
  echo ""
  echo "Usage: ./rollback.sh <version>"
  echo "Example: ./rollback.sh v1.5.2-working"
  exit 1
fi

VERSION=$1
echo "⚠️  This will discard all uncommitted changes and reset to $VERSION"
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  git reset --hard "$VERSION"
  echo "✓ Rolled back to $VERSION"
else
  echo "Cancelled"
fi
