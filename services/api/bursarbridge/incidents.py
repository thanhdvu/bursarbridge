"""Thread-scoped advisory case continuity. No banking authority or extracted parameters."""

import re

from .conversation import normalize


def scam_case(s, user, thread):
    refs = [thread.get("_scamReviewId")]
    # Older server-generated assistant cards already carry a review reference.
    for message in reversed(thread["messages"]):
        if message["role"] == "assistant":
            refs += [
                e.get("data", {}).get("id")
                for e in reversed(message.get("events", []))
                if e.get("kind") == "approval_required"
            ]
    for ref in refs:
        row = s["approvals"].get(ref)
        if (
            row
            and row.get("_riskOnly")
            and row["_family"] == user["familyId"]
            and row.get("_threadId") in {None, thread["threadId"]}
        ):
            return row
    return None


def separate_report(text):
    """A clearly separate reported encounter, not a hypothetical or another question.

    New attachments/amounts alone are additional evidence, not a second incident.
    This heuristic affects only grouping of non-executable reviews.
    """
    t = normalize(text)
    if re.search(r"\b(?:lo|nho|suppose)\b", t) or re.search(r"(?:전화|연락).{0,8}면", t):
        return False
    if any(normalize(w) in t for w in ("what if", "if another", "nếu", "giả sử", "如果", "假如", "만약")):
        return False
    if any(w in t for w in ("万一", "要是", "假设", "혹시")):
        return False
    separate = bool(
        re.search(
            r"\b(?:another|different|separate|new)\s+(?:\w+\s+){0,2}(?:caller|call|incident|person|scam|case)\b",
            t,
        )
    ) or any(
        normalize(w) in t
        for w in (
            "vụ khác",
            "người khác",
            "cuộc gọi khác",
            "chuyện khác",
            "另一个",
            "另一件",
            "另外一个",
            "다른 사람",
            "다른 사건",
            "별개의",
        )
    )
    reported = any(
        normalize(w) in t
        for w in (
            "called",
            "contacted",
            "demanded",
            "received",
            "reported",
            "gọi",
            "nhắn",
            "yêu cầu",
            "bắt",
            "打电话",
            "打来",
            "联系",
            "要求",
            "전화",
            "연락",
            "요구",
        )
    )
    return separate and reported
