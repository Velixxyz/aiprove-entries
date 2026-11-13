# fastest-primes
Read N (1..5,000,000) on stdin, print count of primes <= N.
Entry: `primes.c` (odd-only Sieve of Eratosthenes) + `primes.js` (same sieve in Node) + `run.sh` (compiles C with -O2 when cc exists, else Node).
Run: `echo 1000000 | sh run.sh` -> 78498
