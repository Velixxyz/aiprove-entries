#!/bin/sh
# Fastest correct prime counter. Prefers compiled C, falls back to Node.
DIR=$(dirname "$0")
if command -v cc >/dev/null 2>&1; then
  cc -O2 -o "$DIR/primes" "$DIR/primes.c" -lm 2>/dev/null && exec "$DIR/primes"
fi
exec node "$DIR/primes.js"
