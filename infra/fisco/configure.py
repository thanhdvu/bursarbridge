"""Enable Web3 consistently before first boot; all RPC ports bind loopback."""
from pathlib import Path
import configparser

root = Path(__file__).parent / "nodes" / "127.0.0.1"
for i in range(4):
    path = root / f"node{i}" / "config.ini"
    config = configparser.ConfigParser(inline_comment_prefixes=(";",))
    config.read(path)
    for section in ("rpc", "p2p"):
        if section in config:
            config[section]["listen_ip"] = "127.0.0.1"
    config["web3_rpc"]["enable"] = "true"
    config["web3_rpc"]["listen_port"] = str(8545 + i)
    config["web3_rpc"]["listen_ip"] = "127.0.0.1"
    config["web3_rpc"]["enable_cors"] = "false"
    with path.open("w", newline="\n") as out:
        config.write(out)
