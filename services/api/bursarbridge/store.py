"""One transactional SQLite aggregate, serialized writes, and append-only audit mirror.

The DB and JSONL are independently verified. A mismatched mirror fails closed.
Single API worker only; SQLite handles cross-process compare-and-swap versioning.
"""

import json
import threading
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Column, Text
from sqlmodel import Field, Session, SQLModel, create_engine

from .security import canonical, digest


class Snapshot(SQLModel, table=True):
    id: int = Field(primary_key=True)
    payload: str = Field(sa_column=Column(Text, nullable=False))


class Store:
    def __init__(self, url, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.directory / "agent_audit.jsonl"
        self.ops_file = self.directory / "sandbox_ops.jsonl"
        self.engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30})
        SQLModel.metadata.create_all(self.engine)
        self.lock = threading.RLock()

    @contextmanager
    def transaction(self):
        with self.lock, Session(self.engine) as db:
            # Acquire DB write lock before reading, including across worker processes.
            from sqlalchemy import text

            db.exec(text("BEGIN IMMEDIATE"))
            row = db.get(Snapshot, 1)
            state = json.loads(row.payload) if row else {}
            old_count = len(state.get("audit", []))
            old_ops = len(state.get("operations", []))
            yield state
            if row:
                row.payload = canonical(state)
            else:
                row = Snapshot(id=1, payload=canonical(state))
            db.add(row)
            db.commit()
            new = state.get("audit", [])[old_count:]
            if new:
                with self.audit_file.open("a", encoding="utf-8", newline="\n") as out:
                    for entry in new:
                        out.write(canonical(entry) + "\n")
            ops = state.get("operations", [])[old_ops:]
            if ops:
                with self.ops_file.open("a", encoding="utf-8", newline="\n") as out:
                    for operation in ops:
                        out.write(canonical(operation) + "\n")

    def reset_mirrors(self):
        self.audit_file.write_text("", encoding="utf-8")
        self.ops_file.write_text("", encoding="utf-8")


def audit(s, actor, kind, summary, rules=(), **details):
    entries = s["audit"]
    entry = {
        "seq": len(entries) + 1,
        "at": s["now"],
        "actor": actor,
        "kind": kind,
        "summary": summary,
        "ruleIds": list(rules),
        "prevHash": entries[-1]["hash"] if entries else "0" * 64,
        "rulesVersion": s["rulesVersion"],
        "rulesHash": s["rulesHash"],
        **details,
    }
    entry["hash"] = digest(entry["prevHash"] + canonical(entry))
    entries.append(entry)
    return entry["seq"]


def merkle(hashes):
    if not hashes:
        return digest("")
    level = list(hashes)
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [digest(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def verify(entries):
    previous = "0" * 64
    for index, entry in enumerate(entries, 1):
        body = {k: v for k, v in entry.items() if k != "hash"}
        if (
            entry["seq"] != index
            or entry["prevHash"] != previous
            or digest(previous + canonical(body)) != entry["hash"]
        ):
            return {
                "ok": False,
                "entries": len(entries),
                "anchors": 0,
                "firstBadSeq": index,
                "detail": "Hash chain mismatch",
            }
        previous = entry["hash"]
    return {"ok": True, "entries": len(entries), "anchors": 0}
