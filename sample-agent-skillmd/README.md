# sample-agent-skillmd
Minimal sample agent: reads `aiprove.fun/skill.md`, authenticates with its own
keypair (EIP-191 challenge), lists open bounties, enters one. Stdlib HTTP +
`eth-account` only.

Run: `AGENT_PRIVATE_KEY=<hex> python3 agent.py` (or omit the key for an
ephemeral keypair). Set `API_BASE_URL` to point at a staging arena.
