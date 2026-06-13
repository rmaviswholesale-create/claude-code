#!/usr/bin/env python3
"""Discover VPS IP via Hostinger API. Falls back to torsocks+curl, then manual guide."""
import requests, os, sys, time, socket, subprocess, json as json_mod

MANUAL_GUIDE = """
============================================================
  ACTION REQUIRED: Hostinger API unreachable from GitHub Actions
============================================================

  EASIEST -- One command in your Hostinger VPS Console:
    1. Open hpanel.hostinger.com -> VPS -> Console (or Terminal)
    2. Paste this and press Enter:

       curl -fsSL https://raw.githubusercontent.com/rmaviswholesale-create/claude-code/main/setup.sh | bash

  OR -- Supply your VPS credentials as GitHub repo secrets:
    1. Find your VPS IP in hPanel -> VPS -> server overview
    2. Go to: github.com/rmaviswholesale-create/claude-code/settings/secrets/actions
    3. Add: VPS_IP = <your VPS IP>
    4. Add: VPS_PASSWORD = <your root password>
    5. Push any change to main -- deploy runs automatically.
============================================================
"""

key = os.environ.get('HOSTINGER_KEY', '')
api_url = 'https://api.hostinger.com/api/vps/v1/virtual-machines'
curl_headers = [
    '-H', f'Authorization: Bearer {key}',
    '-H', 'Accept: application/json',
    '-H', 'User-Agent: github-actions-deploy/1.0',
]


def p(msg):
    print(msg, flush=True)


def query_direct():
    """Try direct HTTP request via Python requests."""
    hdrs = {
        'Authorization': f'Bearer {key}',
        'Accept': 'application/json',
        'User-Agent': 'github-actions-deploy/1.0',
    }
    for attempt in range(1, 4):
        p(f'  attempt {attempt}/3 [direct]...')
        try:
            r = requests.get(api_url, headers=hdrs, timeout=25)
            p(f'  HTTP {r.status_code}')
            if r.status_code == 200:
                return r.json()
            p(f'  body: {r.text[:250]}')
        except Exception as e:
            p(f'  error: {e}')
        if attempt < 3:
            time.sleep(10)
    return None


def install_tor():
    """Install tor + torsocks, wait for bootstrap. Returns True if ready."""
    p('Installing tor and torsocks...')
    r = subprocess.run(
        ['sudo', 'apt-get', 'install', '-y', '-q', 'tor', 'torsocks'],
        capture_output=True, text=True, check=False
    )
    if r.returncode != 0:
        p(f'apt install failed (rc={r.returncode}): {r.stderr[-200:]}')
        return False
    p('tor+torsocks installed.')

    # Ensure Tor service is running
    subprocess.run(['sudo', 'systemctl', 'restart', 'tor'],
                   capture_output=True, check=False)

    p('Waiting for Tor SOCKS port (up to 60s)...')
    for i in range(60):
        try:
            s = socket.create_connection(('127.0.0.1', 9050), timeout=1)
            s.close()
            p(f'Tor port open after {i+1}s. Waiting 30s for network bootstrap...')
            time.sleep(30)
            p('Tor ready.')
            return True
        except OSError:
            time.sleep(1)
    p('Tor did not start in time.')
    return False


def query_via_torsocks():
    """Use torsocks curl -- bypasses PySocks dependency."""
    for attempt in range(1, 4):
        p(f'  attempt {attempt}/3 [torsocks+curl]...')
        try:
            result = subprocess.run(
                ['torsocks', 'curl', '-sf', '--max-time', '25'] +
                curl_headers + [api_url],
                capture_output=True, text=True, timeout=30, check=False
            )
            p(f'  curl exit={result.returncode}')
            if result.returncode == 0:
                data = json_mod.loads(result.stdout)
                p('  HTTP 200 via Tor!')
                return data
            if result.stderr:
                p(f'  stderr: {result.stderr[:200]}')
            if result.stdout:
                p(f'  stdout: {result.stdout[:200]}')
        except Exception as e:
            p(f'  error: {e}')
        if attempt < 3:
            time.sleep(10)
    return None


# ── Step 1: Direct ────────────────────────────────────────────────────────────
p('Querying Hostinger API (direct)...')
data = query_direct()

# ── Step 2: Tor fallback ──────────────────────────────────────────────────────
if data is None:
    p('Direct failed. Trying via Tor exit node (torsocks+curl)...')
    if install_tor():
        data = query_via_torsocks()
        if data is not None:
            env_file = os.environ.get('GITHUB_ENV', '')
            if env_file:
                with open(env_file, 'a') as f:
                    f.write('USE_TOR=1\n')

# ── Step 3: Give up ───────────────────────────────────────────────────────────
if data is None:
    p(MANUAL_GUIDE)
    sys.exit(1)

vms = data.get('data', [])
if not vms:
    p('No VMs found in account.')
    p(MANUAL_GUIDE)
    sys.exit(1)

vm = vms[0]
vm_id = vm.get('id', 'unknown')
ips = vm.get('ips', [])
vm_ip = (vm.get('main_ip_address') or
         vm.get('ip_address') or
         vm.get('ipv4') or
         (ips[0].get('address') if ips else None) or
         'UNKNOWN')

p(f'VPS found: id={vm_id}  ip={vm_ip}')
out = os.environ.get('GITHUB_OUTPUT', '')
if out:
    with open(out, 'a') as f:
        f.write(f'vm_id={vm_id}\n')
        f.write(f'vm_ip={vm_ip}\n')
