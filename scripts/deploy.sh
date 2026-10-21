#!/bin/sh
set -e

cd "$(dirname "$0")/.."

CONTEXT=martin
URL=http://raspy.local/

echo "Deploying $(git branch --show-current) @ $(git rev-parse --short HEAD) to $CONTEXT"
[ -z "$(git status --porcelain --untracked-files=no)" ] || echo "Warning: uncommitted changes will be deployed too"

docker --context "$CONTEXT" compose up -d --build
docker --context "$CONTEXT" image prune -f
docker --context "$CONTEXT" compose ps

curl -s -o /dev/null --retry 30 --retry-all-errors --retry-delay 2 -w "$URL -> %{http_code}\n" "$URL"
