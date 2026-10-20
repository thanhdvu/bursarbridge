"""Owner-hosted test deployment. Task Scheduler owns the supervisor, not a coding job."""

import argparse
import contextlib
import ctypes
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values

TASK = 'BursarBridge-Live'
COMMAND_LOG = None
PORTS = {'edge': 18780, 'api': 18000, 'web': 13700}
SYSTEM_ENV = {'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE',
              'APPDATA', 'LOCALAPPDATA', 'PROGRAMDATA', 'COMSPEC', 'SYSTEMDRIVE',
              'HOMEDRIVE', 'HOMEPATH', 'USERNAME', 'USERDOMAIN', 'NUMBER_OF_PROCESSORS',
              'PROCESSOR_ARCHITECTURE', 'PSMODULEPATH'}
LLM_ENV = {'OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL', 'OPENAI_TIMEOUT_SECONDS',
           'OPENAI_REASONING_EFFORT', 'PUBLIC_LLM_DAILY_CALLS', 'PUBLIC_LLM_HOURLY_CALLS',
           'PUBLIC_AGENT_PER_MINUTE', 'PUBLIC_AGENT_PER_HOUR', 'PUBLIC_MAX_SANDBOXES',
           'PUBLIC_SANDBOX_IDLE_HOURS', 'PUBLIC_NEW_PER_IP_MINUTE', 'PUBLIC_NEW_PER_IP_HOUR', 'PUBLIC_NEW_GLOBAL_HOUR', 'PUBLIC_NEW_GLOBAL_DAY', 'PUBLIC_SANDBOX_PROTECT_MINUTES'}


def clean_env():
    return {k: v for k, v in os.environ.items() if k.upper() in SYSTEM_ENV}


def run(args, cwd=None, env=None, timeout=600):
    with contextlib.ExitStack() as stack:
        output = stack.enter_context(COMMAND_LOG.open('ab')) if COMMAND_LOG else None
        subprocess.run([str(a) for a in args], cwd=cwd, env=env or clean_env(),
                       stdout=output, stderr=output, check=True, timeout=timeout,
                       creationflags=subprocess.CREATE_NO_WINDOW)


def ps(script):
    run(['powershell.exe', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden', '-Command', script])


def ps_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def config(state):
    return json.loads((state / 'config.json').read_text(encoding='utf-8'))


def python(c):
    return Path(c['checkout']) / 'services/api/.venv/Scripts/python.exe'


def linux_path(path):
    p = Path(path).resolve().as_posix()
    if not re.fullmatch(r'[A-Za-z]:/[^\r\n]*', p):
        raise ValueError('A local Windows drive path is required')
    return '/mnt/' + p[0].lower() + p[2:]


def linux(state, action):
    c = config(state)
    args = ['wsl.exe', *(['-d', c['wslDistro']] if c.get('wslDistro') else []), '--',
            'python3', linux_path(state / 'tools/linux_infra.py'), action,
            '--checkout', linux_path(c['checkout'])]
    run(args, timeout=1200)


def api_env(state):
    return {**clean_env(), **{k: v for k, v in dotenv_values(state / 'api.env', interpolate=False).items() if v}}


def web_env(state=None):
    # No inherited API secrets, dotenv file or secret passed to Next's compiler.
    environment = clean_env()
    if state is not None:
        environment['PATH'] = str(state / 'tools') + os.pathsep + environment.get('PATH', '')
    return {**environment, 'NEXT_PUBLIC_API_MODE': 'live', 'NEXT_PUBLIC_API_URL': '/bbapi',
            'BB_API_ORIGIN': 'http://127.0.0.1:18000', 'NEXT_TELEMETRY_DISABLED': '1',
            'NODE_ENV': 'production'}


def caddy_env(state):
    return {**clean_env(), 'APPDATA': str(state / 'caddy-data'),
            'XDG_DATA_HOME': str(state / 'caddy-data'),
            'XDG_CONFIG_HOME': str(state / 'caddy-config')}


def wait(url, headers=None, seconds=120):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            r = httpx.get(url, headers=headers, timeout=3, trust_env=False)
            if r.status_code == 200:
                return r
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise RuntimeError('Live service readiness timeout')


def build(state):
    c = config(state)
    root = Path(c['checkout'])
    run(['uv', 'sync', '--frozen'], cwd=root / 'services/api')
    pnpm = shutil.which('pnpm.cmd')
    if not pnpm:
        raise RuntimeError('pnpm.cmd is required')
    if any(p.name != '.env.example' for p in (root / 'apps/web').glob('.env*')):
        raise RuntimeError('Refusing frontend dotenv files; keep LLM credentials in private api.env only')
    run([pnpm, 'install', '--frozen-lockfile'], cwd=root / 'apps/web', env=web_env(state))
    run([pnpm, 'build'], cwd=root / 'apps/web', env=web_env(state), timeout=1200)
    secrets = [v.encode() for k, v in dotenv_values(state / 'api.env', interpolate=False).items()
               if k.endswith('API_KEY') and v and len(v) > 8]
    for path in (root / 'apps/web/.next').rglob('*'):
        if path.is_file() and secrets:
            with path.open('rb') as artifact:
                tail = b''
                while block := artifact.read(1024 * 1024):
                    chunk = tail + block
                    if any(secret in chunk for secret in secrets):
                        raise RuntimeError('LLM key detected in web build; deployment refused')
                    tail = chunk[-max(map(len, secrets)):]
    run(['npm.cmd', 'ci'], cwd=root / 'contracts')
    run(['npm.cmd', 'run', 'compile'], cwd=root / 'contracts')
    runtime = root / 'services/api/runtime'
    runtime.mkdir(exist_ok=True)
    if not (runtime / 'chain-deployment.json').exists():
        run([python(c), 'scripts/deploy_chain.py'], cwd=root / 'services/api', env=api_env(state))


def install_caddy(state):
    tools = state / 'tools'
    binary = tools / 'caddy.exe'
    if binary.exists():
        return
    arch = {'amd64': 'amd64', 'x86_64': 'amd64', 'arm64': 'arm64', 'aarch64': 'arm64'}.get(platform.machine().lower())
    if not arch:
        raise ValueError('Unsupported Windows architecture')
    version = '2.11.7'
    base = f'https://github.com/caddyserver/caddy/releases/download/v{version}/'
    name = f'caddy_{version}_windows_{arch}.zip'
    checksums = urllib.request.urlopen(base + f'caddy_{version}_checksums.txt', timeout=30).read().decode()
    expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1] == name)
    archive = tools / name
    archive.write_bytes(urllib.request.urlopen(base + name, timeout=120).read())
    if hashlib.sha512(archive.read_bytes()).hexdigest() != expected:
        raise ValueError('Caddy release checksum mismatch')
    with zipfile.ZipFile(archive) as source:
        binary.write_bytes(source.read('caddy.exe'))
    (tools / 'caddy-source.json').write_text(json.dumps({'version': version, 'source': base + name, 'sha512': expected}, indent=2))


def prepare(args):
    global COMMAND_LOG
    state, root = args.state.resolve(), args.checkout.resolve()
    if (state / 'supervisor.ready').exists():
        raise RuntimeError('Live supervisor is active; use update, not install, to replace a running release')
    dev = Path(__file__).resolve().parents[2]
    if root == state or root in state.parents or state in root.parents or root == dev or dev in root.parents or state == dev or dev in state.parents:
        raise ValueError('Use separate live checkout and state directories, outside development')
    if not re.fullmatch(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}', args.hostname):
        raise ValueError('A fixed DNS hostname is required')
    marker = state / 'bursarbridge-live.marker'
    if state.exists() and any(state.iterdir()) and not marker.exists():
        raise ValueError('Refusing an existing directory that is not owned by this live launcher')
    state.mkdir(parents=True, exist_ok=True)
    marker.write_text('BursarBridge owner-hosted test state\n')
    # Current owner and SYSTEM only; no inherited shared-user key access.
    sid = subprocess.check_output(['whoami.exe', '/user', '/fo', 'csv', '/nh'], text=True).strip().split(',')[-1].strip('"')
    run(['icacls.exe', state, '/inheritance:r', '/grant:r', f'*{sid}:(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'])
    for folder in ('tools', 'logs', 'sandboxes'):
        (state / folder).mkdir(exist_ok=True)
    COMMAND_LOG = state / 'logs/commands.log'
    node = state / 'tools/node.exe'
    if not node.exists():
        source_node = shutil.which('node.exe')
        if not source_node:
            raise RuntimeError('Node.js is required')
        shutil.copy2(source_node, node)
        (state / 'tools/node-source.json').write_text(json.dumps({
            'version': subprocess.check_output([str(node), '--version'], text=True).strip(),
            'sha256': hashlib.sha256(node.read_bytes()).hexdigest(),
            'source': source_node,
        }, indent=2))
    for name in ('live.py', 'live.ps1', 'linux_infra.py', 'Caddyfile.template'):
        target = state / 'tools' / name
        if Path(__file__).parent / name != target:
            shutil.copy2(Path(__file__).parent / name, target)
    values = dotenv_values(args.env_file, interpolate=False) if args.env_file else (
        dotenv_values(state / 'api.env', interpolate=False) if (state / 'api.env').exists() else {}
    )
    private = {k: v for k, v in values.items() if k in LLM_ENV and v}
    private.setdefault('OPENAI_BASE_URL', 'http://127.0.0.1:8318/v1')
    if private['OPENAI_BASE_URL'].rstrip('/') != 'http://127.0.0.1:8318/v1':
        raise ValueError('This temporary test recipe uses only the owner proxy on 8318')
    private.setdefault('OPENAI_MODEL', 'gpt-6.1-sol')
    private.setdefault('OPENAI_TIMEOUT_SECONDS', '60')
    for key, default in [('PUBLIC_LLM_DAILY_CALLS', '300'), ('PUBLIC_LLM_HOURLY_CALLS', '60')]:
        private.setdefault(key, default)
    private.update(DEMO='1', PUBLIC_DEMO='1', PUBLIC_LOCAL_PROXY='1', LLM_PROVIDER='auto',
                   CHAIN_MODE='fisco', SCREENING_MODE='watchman',
                   PUBLIC_DATA_DIR=str(state / 'sandboxes'),
                   WEBAUTHN_RP_ID=args.hostname, WEBAUTHN_ORIGIN='https://' + args.hostname,
                   FISCO_RPC='http://127.0.0.1:18545', WATCHMAN_URL='http://127.0.0.1:18084')
    (state / 'api.env').write_text(''.join(k + '=' + json.dumps(v) + '\n' for k, v in private.items()), encoding='utf-8')
    distro = args.wsl_distro or subprocess.check_output(
        ['wsl.exe', '--', 'printenv', 'WSL_DISTRO_NAME'], text=True
    ).strip()
    c = {'checkout': str(root), 'hostname': args.hostname, 'wslDistro': distro, 'ports': PORTS}
    (state / 'config.json').write_text(json.dumps(c, indent=2))
    template = (state / 'tools/Caddyfile.template').read_text()
    for key, value in {'HOST': args.hostname, **{k.upper() + '_PORT': str(v) for k, v in PORTS.items()}}.items():
        template = template.replace('@@' + key + '@@', value)
    (state / 'Caddyfile').write_text(template, encoding='utf-8', newline='\n')
    if not root.exists():
        run(['git', 'clone', '--branch', 'main', '--single-branch',
             'https://github.com/thanhdvu/bursarbridge.git', root])
    remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=root, text=True).strip()
    if remote != 'https://github.com/thanhdvu/bursarbridge.git':
        raise RuntimeError('Refusing a checkout with an unrelated origin')
    run(['icacls.exe', root, '/inheritance:r', '/grant:r', f'*{sid}:(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'])
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip()
    if branch != 'main':
        raise RuntimeError('Live checkout must be main')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=root).strip():
        raise RuntimeError('Live checkout is dirty; refusing to overwrite local work')
    install_caddy(state)
    run([state / 'tools/caddy.exe', 'validate', '--config', state / 'Caddyfile', '--adapter', 'caddyfile'], env=caddy_env(state))
    linux(state, 'start')
    wait('http://127.0.0.1:18084/v2/listinfo', seconds=180)
    build(state)
    register(state)
    start(state)
    print('Live installation ready; no Cloudflare service/config was touched')


def register(state, logon=False):
    c = config(state)
    command = subprocess.list2cmdline([str(state / 'tools/live.py'), 'supervise', '--state', str(state)])
    # Interactive owner token keeps access to that owner's existing WSL distro;
    # Task Scheduler is independent of a Codex process/job and stores no password.
    trigger = "$trigger=New-ScheduledTaskTrigger -AtLogOn -User $user;" if logon else '$trigger=$null;'
    ps(f"$user=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name;"
       f"$a=New-ScheduledTaskAction -Execute {ps_literal(python(c))} -Argument {ps_literal(command)} -WorkingDirectory {ps_literal(Path(c['checkout']) / 'services/api')};"
       "$p=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited;"
       "$s=New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries;"
       + trigger + f"Register-ScheduledTask -TaskName '{TASK}' -Action $a -Principal $p -Settings $s "
       + ('-Trigger $trigger ' if logon else '') + '-Force | Out-Null')


def require_main(state):
    root = Path(config(state)['checkout'])
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root).strip()
    if branch != 'main' or dirty:
        raise RuntimeError('Live activation requires a clean main checkout, without development overlays')
    if 'PUBLIC_LOCAL_PROXY' not in (root / 'services/api/bursarbridge/public.py').read_text():
        raise RuntimeError('MAIN_RELEASE_REQUIRED: merge the Round 8 backend before activating the local proxy')


def start(state):
    # Build independently, but never activate a development overlay or bypass the guard.
    require_main(state)
    (state / 'stop.request').unlink(missing_ok=True)
    ps(f"Start-ScheduledTask -TaskName '{TASK}'")
    c = config(state)
    wait('http://127.0.0.1:18780/bbapi/health', {'Host': c['hostname']}, seconds=180)
    check(state)


def stop(state):
    (state / 'stop.request').touch()
    for _ in range(30):
        if not (state / 'supervisor.ready').exists():
            break
        pid = int((state / 'supervisor.ready').read_text())
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(0x100000, False, pid)
        if not handle:
            (state / 'supervisor.ready').unlink(missing_ok=True)
            break
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        exited = kernel.WaitForSingleObject(handle, 0) == 0
        kernel.CloseHandle(handle)
        if exited:
            (state / 'supervisor.ready').unlink(missing_ok=True)
            break
        time.sleep(1)
    else:
        raise RuntimeError('Supervisor did not stop; inspect logs; no unrelated PID killed')
    linux(state, 'stop')
    print('Dedicated live stack stopped; dev and tunnel untouched')


@contextlib.contextmanager
def lock(state, name):
    import msvcrt
    with (state / name).open('a+b') as handle:
        handle.seek(0)
        handle.write(b'0')
        handle.flush()
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


class Job:
    """Own all Windows children; closing this handle also terminates descendants."""

    def __init__(self):
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateJobObjectW.restype = ctypes.c_void_p
        kernel.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong]
        kernel.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        self.kernel, self.handle = kernel, kernel.CreateJobObjectW(None, None)
        # JOBOBJECT_EXTENDED_LIMIT_INFORMATION has 64-bit counters/pointers on Windows x64/arm64.
        class Basic(ctypes.Structure):
            _fields_ = [('process', ctypes.c_int64), ('job', ctypes.c_int64), ('flags', ctypes.c_ulong),
                        ('min', ctypes.c_size_t), ('max', ctypes.c_size_t), ('active', ctypes.c_ulong),
                        ('affinity', ctypes.c_size_t), ('priority', ctypes.c_ulong), ('scheduling', ctypes.c_ulong)]
        class Limits(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', ctypes.c_uint64 * 6), ('memory', ctypes.c_size_t * 4)]
        limits = Limits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.handle or not kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())

    def add(self, process):
        if not self.kernel.AssignProcessToJobObject(self.handle, int(process._handle)):
            process.terminate()
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        self.kernel.CloseHandle(self.handle)


def supervise(state):
    require_main(state)
    c = config(state)
    root = Path(c['checkout'])
    with lock(state, 'supervisor.lock'), (state / 'logs/supervisor.log').open('a', buffering=1) as log:
        def note(message):
            print(datetime.now(timezone.utc).isoformat(), message, file=log, flush=True)
        job = Job()
        children = {}
        attempts, started, retry = {}, {}, {}
        try:
            # Refuse occupied ports; never stop or adopt somebody else's listener.
            for port in PORTS.values():
                with socket.socket() as probe:
                    probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                    probe.bind(('127.0.0.1', port))
            linux(state, 'start')
            commands = {
                'api': ([python(c), '-m', 'uvicorn', 'bursarbridge.public:create_public_app', '--factory',
                         '--host', '127.0.0.1', '--port', '18000', '--proxy-headers',
                         '--forwarded-allow-ips', '127.0.0.1,::1', '--no-access-log'], root / 'services/api', api_env(state)),
                'web': ([state / 'tools/node.exe', root / 'apps/web/node_modules/next/dist/bin/next',
                         'start', '-H', '127.0.0.1', '-p', '13700'], root / 'apps/web', web_env(state)),
                'caddy': ([state / 'tools/caddy.exe', 'run', '--config', state / 'Caddyfile', '--adapter', 'caddyfile'], state, caddy_env(state)),
            }
            (state / 'supervisor.ready').write_text(str(os.getpid()))
            note('Supervisor started; Windows Task Scheduler owns this process')
            last_infra = 0
            while not (state / 'stop.request').exists():
                for name, (args, cwd, env) in commands.items():
                    if name not in children or children[name].poll() is not None:
                        now = time.monotonic()
                        if now < retry.get(name, 0):
                            continue
                        attempts[name] = attempts.get(name, 0) + 1 if now - started.get(name, now) < 30 else 1
                        started[name] = now
                        retry[name] = now + min(60, 3 * 2 ** min(attempts[name] - 1, 5))
                        log_path = state / f'logs/{name}.log'
                        if log_path.exists() and log_path.stat().st_size > 10 * 1024 * 1024:
                            log_path.replace(log_path.with_suffix('.log.1'))
                        with log_path.open('ab') as output:
                            process = subprocess.Popen([str(a) for a in args], cwd=cwd, env=env,
                                                       stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                                       creationflags=subprocess.CREATE_NO_WINDOW)
                        job.add(process)
                        children[name] = process
                        note(f'{name} started pid={process.pid}')
                if time.monotonic() - last_infra > 60:
                    try:
                        linux(state, 'start')
                    except Exception as exc:
                        note('Infrastructure retry: ' + type(exc).__name__)
                    last_infra = time.monotonic()
                time.sleep(3)
        finally:
            job.close()
            for process in children.values():
                with contextlib.suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=10)
            (state / 'supervisor.ready').unlink(missing_ok=True)
            note('Supervisor stopped; owned Windows children closed')


def check(state):
    require_main(state)
    c = config(state)
    root = Path(c['checkout'])
    headers = {'Host': c['hostname'], 'Cf-Connecting-Ip': '203.0.113.250'}
    health = wait('http://127.0.0.1:18780/bbapi/health', headers, seconds=5).json()
    web = wait('http://127.0.0.1:13700/demo', {'Host': c['hostname']}, seconds=30)
    assert 'text/html' in web.headers.get('content-type', '')
    assert health['publicDemo'] and health['chainMode'] == 'fisco' and health['screeningMode'] == 'watchman'
    node = httpx.post('http://127.0.0.1:18545', json={'jsonrpc': '2.0', 'method': 'eth_blockNumber', 'params': [], 'id': 1}, timeout=5, trust_env=False).json()
    screening = httpx.get('http://127.0.0.1:18084/v2/listinfo', timeout=5, trust_env=False).json()
    assert node.get('result') and int(node['result'], 16) > 0
    assert set(screening['lists']) == {'us_ofac'} and screening['lists']['us_ofac'] > 0
    assert (root / 'apps/web/.next/BUILD_ID').exists()
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    print(json.dumps({'ok': True, 'release': sha, 'hostname': c['hostname'], 'ports': PORTS,
                      'publicDemo': True, 'llm': health['llm'], 'chainBlock': node.get('result'),
                      'screening': 'watchman/us_ofac', 'web': 'Next production/live',
                      'webStatus': web.status_code,
                      'logs': str(state / 'logs'), 'externalAcceptance': 'owner route + PO phone/passkey pending'}, indent=2))


def update(state):
    c = config(state)
    root = Path(c['checkout'])
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=root).strip():
        raise RuntimeError('Live checkout is dirty; refusing to replace local changes')
    old = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    stop(state)
    old_build = state / ('build-backup-' + str(time.time_ns()))
    current_build = root / 'apps/web/.next'
    # Both resolved move targets are verified inside the explicitly owned live roots.
    assert current_build.resolve().is_relative_to(root.resolve()) and old_build.resolve().parent == state
    if current_build.exists():
        shutil.move(current_build, old_build)
    try:
        run(['git', 'pull', '--ff-only', 'origin', 'main'], cwd=root)
        require_main(state)
        linux(state, 'start')
        build(state)
    except Exception:
        run(['git', 'reset', '--hard', old], cwd=root)
        if current_build.exists():
            failed_build = state / ('failed-build-' + str(time.time_ns()))
            assert failed_build.resolve().parent == state and current_build.resolve().is_relative_to(root.resolve())
            shutil.move(current_build, failed_build)
        if old_build.exists():
            assert old_build.resolve().parent == state and current_build.resolve().is_relative_to(root.resolve())
            shutil.move(old_build, current_build)
        run(['uv', 'sync', '--frozen'], cwd=root / 'services/api')
        start(state)
        raise RuntimeError('Live update failed; previous release/build restored; private state retained') from None
    start(state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['install', 'start', 'stop', 'update', 'check', 'supervise', 'enable-logon'])
    parser.add_argument('--state', type=Path, default=Path('D:/BursarBridge-live-state'))
    parser.add_argument('--checkout', type=Path, default=Path('D:/BursarBridge-live'))
    parser.add_argument('--hostname', default='bursarbridge.noamofficial.vn')
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--wsl-distro')
    args = parser.parse_args()
    if (args.state / 'logs').exists():
        COMMAND_LOG = args.state / 'logs/commands.log'
    try:
        if os.name != 'nt':
            raise ValueError('Use the Ubuntu VM recipe on Linux')
        if args.action == 'install':
            prepare(args)
        else:
            state = args.state.resolve()
            if not (state / 'bursarbridge-live.marker').exists():
                raise ValueError('Run install first; unrecognized state directory')
            if args.action == 'supervise':
                supervise(state)
            elif args.action == 'enable-logon':
                register(state, logon=True)
            else:
                with lock(state, 'control.lock'):
                    {'start': start, 'stop': stop, 'update': update, 'check': check}[args.action](state)
    except Exception as exc:
        # No raw exception, provider response or dotenv value in terminal output.
        detail = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else (
            f'{Path(exc.cmd[0]).name} exited {exc.returncode}'
            if isinstance(exc, subprocess.CalledProcessError) else 'see private deployment logs'
        )
        if COMMAND_LOG:
            with COMMAND_LOG.open('a', encoding='utf-8') as log:
                print(datetime.now(timezone.utc).isoformat(), type(exc).__name__, detail, file=log)
        print('Live command failed:', type(exc).__name__, detail, file=sys.stderr)
        raise SystemExit(1)
