"""Bound public PDF work; this is resource isolation, not a malware sandbox."""

import hashlib
import json
import subprocess
import sys
import threading
from io import BytesIO
from pathlib import Path

SLOTS = threading.BoundedSemaphore(2)


def extract_public_text(content):
    from .engine import DomainError, require

    require(
        0 < len(content) <= 5 * 1024 * 1024, "DOCUMENT_SIZE", "File must be between 1 byte and 5 MiB", 413
    )
    if not content.startswith(b"%PDF"):
        require(len(content) <= 12000, "DOCUMENT_SIZE", "Public text documents are limited to 12 KB", 413)
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            raise DomainError("INVALID_DOCUMENT", "PDF or UTF-8 text required", 422) from None
    if sys.platform != "linux":
        # The public deployment is Linux. Local Windows/macOS public smoke tests
        # parse only the trusted, bundled synthetic fixtures, not arbitrary PDFs.
        from .fixtures import FIXTURES, pdf

        trusted = {hashlib.sha256(pdf(kind)).digest() for kind in FIXTURES}
        samples = Path(__file__).resolve().parents[3] / "apps/web/public/samples"
        trusted.update(hashlib.sha256(path.read_bytes()).digest() for path in samples.glob("*.pdf"))
        require(
            hashlib.sha256(content).digest() in trusted,
            "PUBLIC_PDF_LINUX_REQUIRED",
            "Use the synthetic sample PDFs; arbitrary public PDF parsing requires Linux",
            422,
        )
        from pypdf import PdfReader

        return "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(content)).pages)
    require(SLOTS.acquire(blocking=False), "DOCUMENT_BUSY", "Document processing is busy; retry shortly", 429)
    try:
        try:
            process = subprocess.run(
                [sys.executable, str(Path(__file__).resolve())],
                input=content,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=5,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise DomainError("DOCUMENT_PARSE_LIMIT", "Document exceeds public parsing limits", 422) from None
        require(
            process.returncode == 0 and len(process.stdout) <= 700000,
            "DOCUMENT_PARSE_LIMIT",
            "Cannot parse document within public limits",
            422,
        )
        result = json.loads(process.stdout)
        require(
            isinstance(result.get("text"), str) and len(result["text"]) <= 100000,
            "INVALID_DOCUMENT",
            "Invalid parsed document",
            422,
        )
        return result["text"]
    finally:
        SLOTS.release()


if __name__ == "__main__":
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    from pypdf import PdfReader

    try:
        content = sys.stdin.buffer.read(5 * 1024 * 1024 + 1)
        if len(content) > 5 * 1024 * 1024:
            raise ValueError()
        reader = PdfReader(BytesIO(content), strict=True)
        if len(reader.pages) > 20:
            raise ValueError()
        parts, size = [], 0
        for page in reader.pages:
            text = page.extract_text() or ""
            size += len(text)
            if size > 100000:
                raise ValueError()
            parts.append(text)
        print(json.dumps({"text": "\n".join(parts)}))
    except Exception:
        raise SystemExit(1) from None
