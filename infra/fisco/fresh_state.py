"""Called only by explicit evidence regeneration, after stopping this team's nodes.

Retain the previous synthetic ledgers; never recursively delete arbitrary paths.
"""
from pathlib import Path
from datetime import datetime, timezone

root = (Path(__file__).resolve().parent / "nodes" / "127.0.0.1").resolve()
suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
for index in range(4):
    target = (root / f"node{index}" / "data").resolve()
    if not target.is_relative_to(root) or target.name != "data":
        raise RuntimeError("Refusing out-of-workspace target")
    if target.exists():
        target.rename(target.with_name("data-evidence-backup-" + suffix))
print("Previous team-operated synthetic chain data retained as timestamped backups")
