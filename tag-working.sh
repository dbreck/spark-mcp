#!/bin/bash
# Tag current state as working version
if [ -z "$1" ]; then
  echo "Usage: ./tag-working.sh <version>"
  echo "Example: ./tag-working.sh 1.5.3"
  exit 1
fi

VERSION=$1
git tag -a "v$VERSION-working" -m "v$VERSION: Working version"
git push origin "v$VERSION-working"
echo "✓ Tagged and pushed v$VERSION-working"
