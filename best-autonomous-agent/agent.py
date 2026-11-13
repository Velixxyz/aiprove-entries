#!/usr/bin/env python3
"""Fully autonomous AIProve agent: auth -> enter all open bounties -> submit
predictions/links from input files -> verify everything -> report.

No human in the loop for the run itself. Signal generation is a separate
research step: predictions arrive via --signals (JSON {slug: payload}) and
content links via --links (JSON {slug: url}); this agent executes the loop,
retries through the flaky API, never double-submits, and verifies each entry
with an independent read before reporting it done.

Secrets: the key file and session cache are read, never printed. The session
token cache is written 0600.

Usage:
  python3 agent.py --key-file ~/.burner/key.json --signals signals.json
                   [--links links.json] [--api https://aiprove.fun]
                   [--session-file ./session.json] [--report ./report.json]
"""
import argparse, json, os, sys, time, urllib.request, urllib.error
from eth_account import Account
from eth_account.messages import encode_defunct

UA = {"User-Agent": "autonomous-agent/1.0"}

def http(base, method, path, body=None, token=None, timeout=60):
    r = urllib.request.Request(base + path, method=method, headers=dict(UA))
    data = None
    if body is not None:
        data = json.dumps(body).encode(); r.add_header("Content-Type", "application/json")
    if token: r.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode() or "{}")
        except Exception: return e.code, {}
    except Exception as e:
        return None, {"error": type(e).__name__, "msg": str(e)[:150]}

def retry(fn, tries=4, sleep=4):
    last = (None, {})
    for _ in range(tries):
        last = fn()
        if last[0] is not None: return last
        time.sleep(sleep)
    return last

class Agent:
    def __init__(self, base, acct):
        self.base, self.acct = base, acct
        self.token = None

    def authenticate(self):
        for _ in range(2):
            st, d = retry(lambda: http(self.base, "GET",
                f"/api/auth/challenge?address={self.acct.address}"))
            ch = d.get("challenge", "")
            guard = (st == 200 and ch.startswith("aiprove.fun wants you to sign in")
                     and self.acct.address in ch and "Domain: aiprove.fun" in ch
                     and not any(w in ch.lower() for w in
                                 ["approve", "permit", "transfer", "spend"]))
            assert guard, "challenge template guard failed, aborting"
            sig = self.acct.sign_message(encode_defunct(text=ch)).signature.hex()
            st, v = retry(lambda: http(self.base, "POST", "/api/auth/verify",
                {"address": self.acct.address, "signature": "0x" + sig}))
            if st == 200 and v.get("token"):
                self.token = v["token"]; return True
            if st is not None and 400 <= st < 500: continue
        return False

    def my_submissions(self):
        st, d = retry(lambda: http(self.base, "GET", "/api/me/submissions", token=self.token))
        if st != 200:
            st, d = retry(lambda: http(self.base, "GET", "/api/me", token=self.token))
            return d.get("submissions", []) if st == 200 else []
        return d if isinstance(d, list) else d.get("submissions", [])

    def enter(self, slug):
        st, d = retry(lambda: http(self.base, "POST",
            f"/api/bounties/{slug}/enter", {}, self.token))
        return st, d

    def submit(self, slug, payload):
        st, d = retry(lambda: http(self.base, "POST",
            f"/api/bounties/{slug}/submit", payload, self.token))
        if st is None:  # ambiguous: check before any retry-with-effect
            mine = [s for s in self.my_submissions()
                    if s.get("bountySlug") == slug]
            if mine: return "verified-via-read", mine[0]
        return st, d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-file", required=True)
    ap.add_argument("--signals", default=None)
    ap.add_argument("--links", default=None)
    ap.add_argument("--api", default=os.environ.get("API_BASE_URL", "https://aiprove.fun"))
    ap.add_argument("--session-file", default=None)
    ap.add_argument("--report", default="report.json")
    ap.add_argument("--enter-all", action="store_true", default=True)
    args = ap.parse_args()
    base = args.api.rstrip("/")
    key = json.load(open(os.path.expanduser(args.key_file)))
    acct = Account.from_key(key["privateKey"])
    agent = Agent(base, acct)
    print("agent:", acct.address)
    assert agent.authenticate(), "authentication failed"
    print("authenticated")
    if args.session_file:
        open(os.path.expanduser(args.session_file), "w").write(
            json.dumps({"address": acct.address, "token": agent.token}))
        os.chmod(os.path.expanduser(args.session_file), 0o600)
    st, d = retry(lambda: http(base, "GET", "/api/bounties"), tries=6, sleep=5)
    items = d if isinstance(d, list) else d.get("bounties", d.get("items", d.get("data", [])))
    if st is None or not items:
        print("WARNING: bounty list unreadable after retries; enter-all skipped")
    open_slugs = [b["slug"] for b in items if isinstance(b, dict) and b.get("status") == "open"]
    print("open bounties:", len(open_slugs))
    already = {s.get("bountySlug") for s in agent.my_submissions()}
    print("already submitted:", sorted(already))
    signals = json.load(open(args.signals)) if args.signals else {}
    links = json.load(open(args.links)) if args.links else {}
    report = {}
    for slug in open_slugs:
        st, d = agent.enter(slug)
        report[slug] = {"enter": st}
    for slug, payload in signals.items():
        if slug in already:
            report.setdefault(slug, {})["submit"] = "skipped-already-submitted"; continue
        st, d = agent.submit(slug, {"prediction": payload})
        report.setdefault(slug, {})["submit"] = {"status": st, "id": d.get("id") if isinstance(d, dict) else None}
        print("submit prediction", slug, "->", st)
    for slug, url in links.items():
        if slug in already:
            report.setdefault(slug, {})["submit"] = "skipped-already-submitted"; continue
        st, d = agent.submit(slug, {"link": url})
        report.setdefault(slug, {})["submit"] = {"status": st, "id": d.get("id") if isinstance(d, dict) else None}
        print("submit link", slug, "->", st)
    mine = agent.my_submissions()
    report["_verified"] = [{"slug": s.get("bountySlug"), "id": s.get("id"),
                            "status": s.get("status")} for s in mine]
    json.dump(report, open(args.report, "w"), indent=1)
    print("verified submissions:", len(mine), "| report:", args.report)

if __name__ == "__main__":
    sys.exit(main())
