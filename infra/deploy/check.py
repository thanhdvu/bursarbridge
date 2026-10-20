"""Run an operator check with private env loaded as data, without shell expansion."""

import argparse
import os
from pathlib import Path

from dotenv import dotenv_values


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["hosted", "judge"])
    parser.add_argument("--env-file", default="/etc/bursarbridge/api.env")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    values = dotenv_values(args.env_file, interpolate=False)
    environment = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/var/lib/bursarbridge", "LANG": "C.UTF-8", **{k: v for k, v in values.items() if v is not None}}
    if os.getuid() == 0:
        import pwd
        user = pwd.getpwnam("bursarbridge")
        os.setgroups([])
        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)
    executable = str(root / "services/api/.venv/bin/python")
    os.chdir(root / "services/api")
    command = [executable, "-m", "bursarbridge.cli"] + (["conversation-eval", "--provider", "hosted"] if args.command == "hosted" else ["judge"])
    os.execve(executable, command, environment)
