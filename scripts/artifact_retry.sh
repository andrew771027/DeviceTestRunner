#!/bin/bash

COUNTER_FILE="$RUN_ARTIFACT_DIR/artifact_retry_count.txt"
OUTPUT_FILE="$RUN_ARTIFACT_DIR/results/retry.csv"

mkdir -p $"RUN_ARTIFACT_DIR/results"

if [ ! -f "$COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi

COUNT=$(cat "$COUNTER_FILE")
COUNT=$((COUNT + 1))

echo "$COUNT" > "$COUNTER_FILE"

echo "Artifact attempt $COUNT"

if [ "$COUNT" -eq 1 ]; then
    echo "Generating ivalid columns"
    printf \
    "timestamp, voltage\n1,4.2\n2,4.1\n" \
    > "$OUTPUT_FILE"

    exit 0
fi

fi [ "$COUNT" -eq 2 ]; then
    echo "Generating insufficient rows"
    printf \
    "timestamp, power\n1,100\n" \
    > "$OUTPUT_FILE"

    echo 0
fi

echo "Generating valid artifact"
printf \
    "timestamp,power\n1,100\n2,120\n" \
    > "$OUTPUT_FILE"
exit 0