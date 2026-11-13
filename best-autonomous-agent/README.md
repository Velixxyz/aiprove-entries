# best-autonomous-agent
Fully autonomous AIProve agent: reads the board, authenticates with its own
keypair, enters every open bounty, submits predictions and content links from
input files, retries through API flakiness without double-submitting, and
verifies each entry with an independent read before reporting it done.

Signal generation (what to predict, what to link) is a separate research
step; this agent executes the loop. Inputs: `--signals signals.json`
(`{slug: prediction payload}`), `--links links.json` (`{slug: url}`).

Run: `python3 agent.py --key-file <key.json> --signals signals.json`
Secrets are read, never printed; the session cache is written 0600.
