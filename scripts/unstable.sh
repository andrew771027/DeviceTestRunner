#!/bin/bash

COUNTER_FILE="$RUN_ARTIFACT_DIR/retry_counter.txt"

if [ ! -f "COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi

COUNT=$(cat "$COUNTER_FILE")
COUNT=$((COUNT + 1))

echo "$COUNT" > "$COUNTER_FILE"

echo "Attempt $COUNT"

if [ "$COUNT" -lt 3 ]; then
    echo "Temporary failure" >&2
    exit 1
fi

echo "Command succeeded"

exit 0
