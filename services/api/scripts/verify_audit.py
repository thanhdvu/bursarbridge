"""Verify bundled audit chains, Merkle commitments, and optionally real FISCO receipts."""

import argparse
import csv
import json
from pathlib import Path

from bursarbridge.chain import Chain

parser = argparse.ArgumentParser()
parser.add_argument("--evidence", default="../../evidence")
parser.add_argument("--rpc")
args = parser.parse_args()
root = Path(args.evidence)
groups = {}
for line in (root / "agent_audit.jsonl").read_text(encoding="utf-8").splitlines():
    row = json.loads(line)
    groups.setdefault(row["runId"], []).append(row["entry"])
anchors = list(csv.DictReader((root / "anchors.csv").open(encoding="utf-8", newline="")))
count = 0
for run, entries in groups.items():
    selected = []
    for a in anchors:
        if a["runId"] == run:
            row = {k: v for k, v in a.items() if v != "" and k != "runId"}
            for key in ("firstSeq", "lastSeq", "blockNumber", "index"):
                if key in row:
                    row[key] = int(row[key])
            if not args.rpc and row["mode"] == "fisco":
                # Explicitly report offline mode; don't claim chain verification.
                row["mode"] = "local"
            selected.append(row)
    chain = Chain("fisco" if args.rpc else "local")
    if args.rpc:
        chain.rpc = args.rpc
    result = chain.verify({"audit": entries, "anchors": selected})
    if not result["ok"]:
        raise SystemExit(f"FAIL {run}: {result}")
    count += len(entries)
print(
    f"OK: {len(groups)} runs, {count} entries, {len(anchors)} anchors; "
    + (
        "on-chain receipts and roots verified"
        if args.rpc
        else "OFFLINE hashes/Merkle only; use --rpc for on-chain verification"
    )
)
