"""Pinned native Watchman build in WSL/Linux, no Docker or libpostal required."""
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import tarfile
import urllib.request

VERSION = "v1.2.2"
GO_VERSION = "go1.27.2"
ARCHES = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}
arch = ARCHES.get(platform.machine().lower())
if platform.system() != "Linux" or arch is None:
    raise SystemExit("Watchman native installer supports Linux amd64 and arm64 only")
root = Path.home() / ".local/share/bursarbridge-watchman"
root.mkdir(parents=True, exist_ok=True)


def download(url, target):
    if not target.exists():
        urllib.request.urlretrieve(url, target)


binary = root / ("watchman-" + VERSION + "-native")
if binary.exists():
    with binary.open("rb") as executable:
        header = executable.read(20)
    if header[:4] != b"\x7fELF" or int.from_bytes(header[18:20], "little") != {"amd64": 62, "arm64": 183}[arch]:
        raise RuntimeError("Cached Watchman is not a Linux binary for this architecture; rebuild it")
if not binary.exists():
    # Go's official manifest supplies the archive checksum before extraction.
    releases = json.load(urllib.request.urlopen("https://go.dev/dl/?mode=json&include=all", timeout=30))
    release = next(r for r in releases if r["version"] == GO_VERSION)
    asset = next(f for f in release["files"] if f["os"] == "linux" and f["arch"] == arch and f["kind"] == "archive")
    archive = root / asset["filename"]
    download("https://go.dev/dl/" + asset["filename"], archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != asset["sha256"]:
        raise RuntimeError("Go archive checksum mismatch")
    toolchain = root / ("toolchain-" + arch)
    toolchain.mkdir(exist_ok=True)
    if not (toolchain / "go/bin/go").exists():
        with tarfile.open(archive) as source:
            for member in source.getmembers():
                if not (toolchain / member.name).resolve().is_relative_to(toolchain.resolve()):
                    raise RuntimeError("Unsafe archive path")
            source.extractall(toolchain, filter="data")
    source = root / "source"
    if not (source / "go.mod").exists():
        archive = root / "source.tar.gz"
        download(f"https://github.com/moov-io/watchman/archive/refs/tags/{VERSION}.tar.gz", archive)
        source.mkdir(exist_ok=True)
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                member.name = "/".join(member.name.split("/")[1:])
                if member.name and (source / member.name).resolve().is_relative_to(source.resolve()):
                    tar.extract(member, source, filter="data")
    environment = {**os.environ, "CGO_ENABLED": "0", "GOTOOLCHAIN": "auto", "GOOS": "linux", "GOARCH": arch}
    subprocess.run([str(toolchain / "go/bin/go"), "build", "-trimpath", "-ldflags", "-X github.com/moov-io/watchman.Version=" + VERSION, "-o", str(binary), "./cmd/server"],
                   cwd=source, env=environment, check=True)
    (root / "build.json").write_text(json.dumps({"watchman": VERSION, "go": release["version"],
        "goArchiveSha256": asset["sha256"], "binarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "cgo": False, "arch": arch, "source": f"https://github.com/moov-io/watchman/tree/{VERSION}"}, indent=2))
print("Native Watchman binary ready:", binary)
