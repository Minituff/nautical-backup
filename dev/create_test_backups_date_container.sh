#!/usr/bin/env bash
# Creates backdated test backup folders in date/container format:
#   destination/<date>/<container>/
#
# Usage: ./create_test_backups_date_container.sh [N_DAYS] [CONTAINER]
# Defaults: N_DAYS=30, CONTAINER=watchtower

set -euo pipefail

N_DAYS="${1:-30}"
CONTAINER="${2:-watchtower}"
CONTAINER2="${3:-test-container-2}"
DEST="$(dirname "$0")/destination"

echo "Creating $N_DAYS days of test backups in date/container format"
echo "  Destination : $DEST"
echo "  Container   : $CONTAINER"
echo ""

for i in $(seq 0 "$((N_DAYS - 1))"); do
    folder=$(date -d "$i days ago" +%Y-%m-%d)
    target="$DEST/$folder/$CONTAINER"
    target2="$DEST/$folder/$CONTAINER2"
    mkdir -p "$target"
    mkdir -p "$target2"
    echo "  Created: $folder/$CONTAINER and $folder/$CONTAINER2"
    echo "$DEST/$folder" >> "$target/test-file.txt"
    echo "$DEST/$folder" >> "$target2/test-file.txt"
done

echo ""
echo "Done. $N_DAYS folder(s) created."
