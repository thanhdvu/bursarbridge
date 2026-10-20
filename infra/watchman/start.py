"""Start/reuse only this project's native Watchman process; logs stay outside Git."""
import json
import os
from pathlib import Path
import subprocess
import urllib.request

root = Path.home() / ".local/share/bursarbridge-watchman"
binary = root / "watchman-v1.2.2-native"
pidfile = root / "watchman.pid"
if not binary.exists():
    raise SystemExit("Run infra/watchman/install.py first")
if pidfile.exists():
    pid = int(pidfile.read_text())
    try:
        if Path(f"/proc/{pid}/exe").resolve() == binary.resolve():
            print("Native Watchman already running, pid", pid)
            raise SystemExit(0)
    except FileNotFoundError:
        pass
# A listener owned by another process is an error, never silently accepted as ours.
try:
    urllib.request.urlopen("http://127.0.0.1:8084/v2/listinfo", timeout=2)
except OSError:
    pass
else:
    raise SystemExit("Port 8084 is occupied by a different process; no duplicate started")
config = Path(__file__).resolve().with_name("watchman.yaml")
environment = {"HOME": str(Path.home()), "PATH": os.environ["PATH"], "APP_CONFIG": str(config), "INCLUDED_LISTS": "us_ofac"}
with (root / "watchman.log").open("ab") as log:
    process = subprocess.Popen([str(binary)], cwd=root, env=environment, stdin=subprocess.DEVNULL,
                               stdout=log, stderr=log, start_new_session=True)
pidfile.write_text(str(process.pid))
print("Started native Watchman, pid", process.pid, "log:", root / "watchman.log")
