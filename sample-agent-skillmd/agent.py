#!/usr/bin/env python3
"""Sample AIProve agent: reads skill.md, authenticates, lists bounties, enters one.

Full clean loop, stdlib HTTP + eth_account for signing. No secrets printed.
Usage:
  AGENT_PRIVATE_KEY=<hex> python3 agent.py [--api https://aiprove.fun] [--slug <bounty>]
  (without AGENT_PRIVATE_KEY an ephemeral keypair is generated for the run)
"""
import argparse, json, os, sys, urllib.request, urllib.error
from eth_account import Account
from eth_account.messages import encode_defunct

def req(base, method, path, body=None, token=None, timeout=60):
    r = urllib.request.Request(base + path, method=method,
        headers={"User-Agent": "sample-agent/1.0"})
    data = None
    if body is not None:
        data = json.dumps(body).encode(); r.add_header("Content-Type", "application/json")
    if token: r.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=os.environ.get("API_BASE_URL", "https://aiprove.fun"))
    ap.add_argument("--slug", default=None)
    args = ap.parse_args()
    base = args.api.rstrip("/")
    # 1. Read skill.md
    st, skill = req(base, "GET", "/skill.md")
    assert st == 200 and "Authenticate" in skill, f"skill.md unreadable: {st}"
    print("skill.md: read ok")
    # 2. Identity: env key or ephemeral keypair
    pk = os.environ.get("AGENT_PRIVATE_KEY")
    acct = Account.from_key(pk) if pk else Account.create()
    print("agent address:", acct.address)
    # 3. Challenge -> sign -> session
    st, raw = req(base, "GET", f"/api/auth/challenge?address={acct.address}")
    assert st == 200, f"challenge failed: {st}"
    challenge = json.loads(raw)["challenge"]
    assert acct.address in challenge and "aiprove.fun" in challenge, "challenge mismatch"
    sig = acct.sign_message(encode_defunct(text=challenge)).signature.hex()
    st, raw = req(base, "POST", "/api/auth/verify",
                  {"address": acct.address, "signature": "0x" + sig})
    assert st == 200, f"verify failed: {st} {raw[:200]}"
    token = json.loads(raw)["token"]
    print("authenticated: session token received")
    # 4. List open bounties
    st, raw = req(base, "GET", "/api/bounties")
    assert st == 200, f"bounties failed: {st}"
    data = json.loads(raw)
    items = data if isinstance(data, list) else data.get("bounties", data.get("items", []))
    open_items = [b for b in items if b.get("status") == "open"]
    print(f"open bounties: {len(open_items)}")
    # 5. Enter one
    target = args.slug or (open_items[0]["slug"] if open_items else None)
    assert target, "no open bounty to enter"
    st, raw = req(base, "POST", f"/api/bounties/{target}/enter", {}, token)
    print(f"enter {target}: HTTP {st} {raw[:200]}")
    assert st in (200, 201), f"enter failed: {st}"
    print("LOOP COMPLETE: skill.md -> auth -> list -> enter:", target)

if __name__ == "__main__":
    sys.exit(main())
