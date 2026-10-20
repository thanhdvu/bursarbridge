"""Actual loopback Caddy drill with controlled provider, no public DNS or secrets."""

import argparse
import concurrent.futures
import json
import os
import sqlite3
import subprocess
import threading
import time
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from bursarbridge.agent import scripted_reply
from bursarbridge.chain import Chain
from bursarbridge.providers import Provider
from bursarbridge.public import create_public_app
from bursarbridge.security import digest

HOST = 'bursarbridge.noamofficial.vn'
ROOT = Path(__file__).resolve().parents[3]


class Controlled(Provider):
    """A real HostedGate around a delayed deterministic adapter, no HTTP/model call."""

    def propose(self, history, locale, fallback):
        time.sleep(1)
        return fallback

    def reply(self, history, locale, facts):
        time.sleep(1)
        return scripted_reply(facts, locale)


class Tunnel(httpx.HTTPTransport):
    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def handle_request(self, request):
        # The virtual HTTPS URL retains Secure cookie semantics in the client.
        # Only the transport is rewritten to model cloudflared's loopback HTTP hop.
        headers = httpx.Headers(request.headers)
        headers.update({'Host': HOST, 'Cf-Connecting-Ip': self.ip,
                        'X-Forwarded-For': '203.0.113.99', 'X-Real-IP': '203.0.113.98'})
        routed = httpx.Request(request.method,
                               request.url.copy_with(scheme='http', host='127.0.0.1', port=18781),
                               headers=headers, content=request.read(), extensions=request.extensions)
        return super().handle_request(routed)


def main(binary, output, quiet_seconds):
    os.environ.update(SCREENING_MODE='synthetic', LLM_PROVIDER='openai',
                      OPENAI_BASE_URL='http://127.0.0.1:8318/v1', PUBLIC_LOCAL_PROXY='1',
                      PUBLIC_LLM_DAILY_CALLS='2', PUBLIC_LLM_HOURLY_CALLS='2')
    with TemporaryDirectory(prefix='bb-r8-caddy-') as directory:
        temp = Path(directory)
        app = create_public_app(temp / 'sandboxes', Chain('local'), Controlled('openai'))
        web = Starlette(routes=[Route('/{path:path}', lambda r: HTMLResponse('<html>controlled web</html>'))])
        servers, threads = [], []
        for application, port in [(app, 18001), (web, 13701)]:
            server = uvicorn.Server(uvicorn.Config(application, host='127.0.0.1', port=port,
                                      log_level='error', proxy_headers=True,
                                      forwarded_allow_ips='127.0.0.1,::1'))
            thread = threading.Thread(target=server.run, daemon=True)
            thread.start()
            servers.append(server)
            threads.append(thread)
        process = None
        try:
            for _ in range(100):
                if all(s.started for s in servers):
                    break
                time.sleep(.05)
            assert all(s.started for s in servers)
            text = (ROOT / 'infra/windows/Caddyfile.template').read_text()
            for key, value in {'HOST': HOST, 'EDGE_PORT': '18781', 'API_PORT': '18001', 'WEB_PORT': '13701'}.items():
                text = text.replace('@@' + key + '@@', value)
            path = temp / 'Caddyfile'
            path.write_text(text)
            with (output.parent / 'r8-caddy-drill.log').open('w') as log:
                caddy_env = {**os.environ, 'APPDATA': str(temp / 'caddy-data'),
                             'XDG_DATA_HOME': str(temp / 'caddy-data'), 'XDG_CONFIG_HOME': str(temp / 'caddy-config')}
                subprocess.run([str(binary), 'validate', '--config', str(path), '--adapter', 'caddyfile'],
                               check=True, stdout=log, stderr=log, env=caddy_env)
                process = subprocess.Popen([str(binary), 'run', '--config', str(path), '--adapter', 'caddyfile'],
                                           stdout=log, stderr=log, env=caddy_env,
                                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            for _ in range(100):
                try:
                    if httpx.get('http://127.0.0.1:18781/bbapi/health', headers={'Host': HOST}, trust_env=False).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(.05)
            with httpx.Client(base_url='https://' + HOST, transport=Tunnel('203.0.113.10'), timeout=10, follow_redirects=True) as a, \
                 httpx.Client(base_url='https://' + HOST, transport=Tunnel('203.0.113.10'), timeout=10, follow_redirects=True) as b:
                for client in (a, b):
                    response = client.get('/demo?live=1', headers={'Accept': 'text/html'})
                    assert response.status_code == 200 and 'controlled web' in response.text
                    assert client.cookies.get('bb_sandbox')
                    assert any('Secure' in r.headers.get('set-cookie', '') for r in response.history)
                assert a.cookies.get('bb_sandbox') != b.cookies.get('bb_sandbox')

                def login(persona):
                    response = a.post('/bbapi/session', json={'persona': persona})
                    response.raise_for_status()
                    return persona, {'Authorization': 'Bearer ' + response.json()['token']}

                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    headers = dict(pool.map(login, ['student_linh', 'parent_minh', 'mother_lan', 'judge']))
                other = {'Authorization': 'Bearer ' + b.post('/bbapi/session', json={'persona': 'student_linh'}).json()['token']}
                assert a.get('/bbapi/me', headers=other).status_code == 401
                thread = a.post('/bbapi/agent/threads', headers=headers['student_linh']).json()['threadId']

                def message(client, ref, auth):
                    rows = []
                    start = time.perf_counter()
                    with client.stream('POST', f'/bbapi/agent/threads/{ref}/messages', headers=auth,
                                       json={'text': 'pay tuition', 'locale': 'en'}) as response:
                        if response.status_code != 200:
                            response.read()
                            return response.status_code, rows
                        assert 'content-encoding' not in response.headers
                        assert 'no-transform' in response.headers['cache-control']
                        for line in response.iter_lines():
                            if line.startswith('data: '):
                                event = json.loads(line[6:])
                                rows.append({**event, 'elapsedMs': round(1000 * (time.perf_counter() - start), 1)})
                    return 200, rows

                _, first = message(a, thread, headers['student_linh'])
                assert first[0]['type'] == 'step' and first[0]['elapsedMs'] < 500
                token = next(r for r in first if r['type'] == 'token')
                assert token['elapsedMs'] > 1500 and token['source'] == 'openai'
                _, second = message(a, thread, headers['student_linh'])
                fallback = next(r for r in second if r['type'] == 'token')
                assert fallback['source'] == 'scripted_fallback'
                assert fallback['fallback']['code'] == 'hosted_budget_exhausted'
                assert not a.get('/bbapi/me', headers=headers['student_linh']).json()['frozen']
                assert message(a, thread, headers['student_linh'])[0] == 200
                assert message(a, thread, headers['student_linh'])[0] == 429
                other_thread = b.post('/bbapi/agent/threads', headers=other).json()['threadId']
                assert message(b, other_thread, other)[0] == 200

                with httpx.Client(base_url='https://' + HOST, transport=Tunnel('203.0.113.11')) as c:
                    assert c.get('/bbapi/health').status_code == 200
                with closing(sqlite3.connect(temp / 'sandboxes/admission.db')) as db:
                    keys = {r[0] for r in db.execute('SELECT key FROM budgets')}
                assert 'http:' + digest('203.0.113.10') in keys
                assert 'http:' + digest('203.0.113.11') in keys
                assert 'http:' + digest('203.0.113.99') not in keys
                assert a.post('/bbapi/demo/reset', headers=headers['judge']).status_code == 200
                assert b.get('/bbapi/me', headers=other).status_code == 200

                beats = []
                start = time.monotonic()
                with b.stream('GET', '/bbapi/events', headers=other) as response:
                    assert 'content-encoding' not in response.headers
                    assert 'no-transform' in response.headers['cache-control']
                    for line in response.iter_lines():
                        if line.startswith(': heartbeat'):
                            beats.append(time.monotonic() - start)
                        if time.monotonic() - start >= quiet_seconds:
                            break
                gaps = [end - begin for begin, end in zip(beats, beats[1:])]
                assert len(beats) >= quiet_seconds - 2 and max(gaps, default=0) < 3
                for _ in range(50):
                    if not app.state.manager.active:
                        break
                    time.sleep(.1)
                assert not app.state.manager.active, 'Disconnected SSE retained its sandbox/stream slot'
                report = {'transport': 'Actual loopback HTTP Caddy, simulated named-tunnel HTTPS/client headers',
                          'twoBrowsersSameNetworkIsolated': True, 'parallelPersonaBootstrap': True,
                          'crossSandboxTokenRejected': True, 'resetIsolated': True,
                          'cfClientIpUsed': True, 'forgedXffIgnored': True,
                          'visitorMessageLimitIsolated': True,
                          'firstStepMs': first[0]['elapsedMs'], 'replyMs': token['elapsedMs'],
                          'fallback': {'source': fallback['source'], 'code': fallback['fallback']['code'], 'frozen': False},
                          'quietStreamSeconds': round(beats[-1], 2), 'heartbeatCount': len(beats),
                          'maxHeartbeatGapSeconds': round(max(gaps, default=0), 2),
                          'disconnectedStreamReleased': True,
                          'compression': False, 'cacheControl': 'no-store, no-transform',
                          'limits': 'Controlled delayed adapter, local hash chain/synthetic screening and HTML upstream isolate edge behavior. No model calls, public DNS/Cloudflare path or phone/passkey acceptance claimed.'}
                output.write_text(json.dumps(report, indent=2), encoding='utf-8')
                print(json.dumps(report, indent=2))
        finally:
            if process:
                process.terminate()
                process.wait(timeout=10)
            for server in servers:
                server.should_exit = True
            for thread in threads:
                thread.join(timeout=10)
                assert not thread.is_alive(), 'SSE disconnect retained an upstream stream/server'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--caddy', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('runtime/r8_tunnel_drill.json'))
    parser.add_argument('--quiet-seconds', type=int, default=130)
    args = parser.parse_args()
    main(args.caddy.resolve(), args.output, args.quiet_seconds)
