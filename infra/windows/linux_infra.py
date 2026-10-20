"""Dedicated WSL infrastructure. No development nodes, keys or data are shared."""

import argparse
import configparser
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path.home() / ".local/share/bursarbridge-live"


def pids(binary):
    found = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if (proc / 'exe').resolve() == binary.resolve():
                found.append(int(proc.name))
        except OSError:
            pass
    return found


def alive(binary):
    return next(iter(pids(binary)), None)


def main(action, checkout):
    ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    fisco = ROOT / 'fisco'
    watchman = ROOT / 'watchman'
    if action == 'stop':
        # Signal only verified executable paths in this dedicated live directory.
        for binary in [fisco / 'nodes/127.0.0.1/fisco-bcos', watchman / 'watchman']:
            while pid := alive(binary):
                os.kill(pid, signal.SIGTERM)
                for _ in range(50):
                    if not Path(f'/proc/{pid}').exists():
                        break
                    time.sleep(.1)
                else:
                    raise RuntimeError('Live infrastructure did not stop; no unverified process killed')
        return
    fisco.mkdir(exist_ok=True)
    builder = fisco / 'build_chain.sh'
    if not builder.exists():
        url = 'https://raw.githubusercontent.com/FISCO-BCOS/FISCO-BCOS/v3.17.1/tools/BcosAirBuilder/build_chain.sh'
        builder.write_bytes(urllib.request.urlopen(url, timeout=30).read())
        (fisco / 'builder-source.json').write_text(json.dumps({
            'source': url, 'sha256': hashlib.sha256(builder.read_bytes()).hexdigest()
        }, indent=2))
    nodes = fisco / 'nodes'
    if not (nodes / '127.0.0.1/node0/config.ini').exists():
        subprocess.run(['bash', str(builder), '-l', '127.0.0.1:4', '-o', str(nodes),
                        '-p', '30310,18500', '-I', 'chain8', '-v', 'v3.17.1'],
                       cwd=fisco, check=True, timeout=600)
        for i in range(4):
            path = nodes / f'127.0.0.1/node{i}/config.ini'
            config = configparser.ConfigParser(inline_comment_prefixes=(';',))
            config.read(path)
            for section in ('rpc', 'p2p'):
                config[section]['listen_ip'] = '127.0.0.1'
            config['web3_rpc'].update(enable='true', listen_ip='127.0.0.1',
                                      listen_port=str(18545 + i), enable_cors='false')
            with path.open('w') as out:
                config.write(out)
    if len(pids(nodes / '127.0.0.1/fisco-bcos')) != 4:
        subprocess.run(['bash', str(nodes / '127.0.0.1/start_all.sh')], check=True, timeout=60)
    for _ in range(60):
        try:
            request = urllib.request.Request('http://127.0.0.1:18545',
                data=json.dumps({'jsonrpc': '2.0', 'method': 'eth_chainId', 'params': [], 'id': 1}).encode(),
                headers={'Content-Type': 'application/json'})
            if json.load(urllib.request.urlopen(request, timeout=2)).get('result'):
                break
        except OSError:
            pass
        time.sleep(1)
    else:
        raise RuntimeError('Dedicated live FISCO RPC did not become ready; inspect its node logs')
    watchman.mkdir(exist_ok=True)
    binary = watchman / 'watchman'
    if not binary.exists():
        # The architecture-aware installer is a build cache only, never the live service.
        subprocess.run(['python3', str(checkout / 'infra/watchman/install.py')], check=True, timeout=600)
        source = Path.home() / '.local/share/bursarbridge-watchman'
        shutil.copy2(source / 'watchman-v1.2.2-native', binary)
        shutil.copy2(source / 'build.json', watchman / 'build.json')
    if not alive(binary):
        config = watchman / 'watchman.yaml'
        config.write_text('''Watchman:
  Servers:
    BindAddress: "127.0.0.1:18084"
    AdminAddress: "127.0.0.1:19094"
    Pprof:
      Enabled: false
  Download:
    IncludedLists: [us_ofac]
    RefreshInterval: "12h"
''')
        with (watchman / 'watchman.log').open('ab') as log:
            p = subprocess.Popen([str(binary)], cwd=watchman, stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=log, start_new_session=True,
                                 env={'HOME': str(Path.home()), 'PATH': os.environ['PATH'],
                                      'APP_CONFIG': str(config), 'INCLUDED_LISTS': 'us_ofac'})
        (watchman / 'watchman.pid').write_text(str(p.pid))
    for _ in range(90):
        try:
            info = json.load(urllib.request.urlopen('http://127.0.0.1:18084/v2/listinfo', timeout=2))
            if set(info.get('lists', {})) == {'us_ofac'} and info['lists']['us_ofac'] > 0:
                break
        except OSError:
            pass
        time.sleep(1)
    else:
        raise RuntimeError('Dedicated Watchman government list did not become ready')
    print('Dedicated live FISCO and government-only Watchman started; dev services untouched')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'stop'])
    parser.add_argument('--checkout', type=Path, required=True)
    args = parser.parse_args()
    main(args.action, args.checkout)
