#!/bin/sh
set -u

for dir in $(dirname $0)/*/; do
  [ -f "$dir/run.bats" ] && ( echo "$dir"; cd "$dir"; ./run.bats; echo )
done

