"""Stop only the native Watchman instance owned by this launcher."""
import os
import signal
from pathlib import Path

root = Path.home() / ".local/share/bursarbridge-watchman"
pidfile = root / "watchman.pid"
if pidfile.exists():
    pid = int(pidfile.read_text())
    if Path(f"/proc/{pid}/exe").resolve() == (root / "watchman-v1.2.2-native").resolve():
        os.kill(pid, signal.SIGTERM)
    pidfile.unlink(missing_ok=True)
