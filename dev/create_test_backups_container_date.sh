#!/usr/bin/env bash
# Creates backdated test backup folders in container/date format:
#   destination/<container>/<date>/
#
# Usage: ./create_test_backups_container_date.sh [N_DAYS] [CONTAINER]
# Defaults: N_DAYS=30, CONTAINER=watchtower

set -euo pipefail

N_DAYS="${1:-30}"
CONTAINER="${2:-watchtower}"
DEST="$(dirname "$0")/destination"

echo "Creating $N_DAYS days of test backups in container/date format"
echo "  Destination : $DEST"
echo "  Container   : $CONTAINER"
echo ""

for i in $(seq 0 "$((N_DAYS - 1))"); do
    folder=$(date -d "$i days ago" +%Y-%m-%d)
    target="$DEST/$CONTAINER/$folder"
    mkdir -p "$target"
    echo "  Created: $CONTAINER/$folder"
done

echo ""
echo "Done. $N_DAYS folder(s) created."
