#!/usr/bin/env python3
"""Discover VPS IP via Hostinger API. Falls back to Tor proxy, then manual guide."""
import requests, os, sys, time, socket, subprocess

MANUAL_GUIDE = """
============================================================
  ACTION REQUIRED: Hostinger API unreachable from GitHub Actions
============================================================

  EASIEST — One command in your Hostinger VPS Console:
    1. Open hpanel.hostinger.com -> VPS -> Console (or Terminal)
    2. Paste this and press Enter:

       curl -fsSL https://raw.githubusercontent.com/rmaviswholesale-create/claude-code/main/setup.sh | bash

  OR — Supply your VPS credentials as GitHub repo secrets:
    1. Find your VPS IP in hPanel -> VPS -> server overview
    2. Go to: github.com/rmaviswholesale-create/claude-code/settings/secrets/actions
    3. Add: VPS_IP = <your VPS IP>
    4. Add: VPS_PASSWORD = <your root password>
    5. Push any change to main -- deploy runs automatically.
============================================================
"""

key = os.environ.get('HOSTINGER_KEY', '')
url = 'https://api.hostinger.com/api/vps/v1/virtual-machines'
headers = {
    'Authorization': f'Bearer {key}',
    'Accept': 'application/json',
    'User-Agent': 'github-actions-deploy/1.0',
}


def query_api(proxies=None, label='direct'):
    for attempt in range(1, 4):
        print(f'  attempt {attempt}/3 [{label}]...')
        try:
            r = requests.get(url, headers=headers, timeout=25, proxies=proxies)
            print(f'  HTTP {r.status_code}')
            if r.status_code == 200:
                return r
            print(f'  response: {r.text[:300]}')
        except Exception as e:
            print(f'  error: {e}')
        if attempt < 3:
            time.sleep(10)
    return None


def start_tor():
    print('Installing Tor...')
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tor'],
                   capture_output=True, check=False)
    subprocess.run(['sudo', 'systemctl', 'start', 'tor'],
                   capture_output=True, check=False)
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'PySocks', '-q'],
                   capture_output=True, check=False)
    print('Waiting for Tor to bootstrap (up to 60s)...')
    for i in range(60):
        try:
            s = socket.create_connection(('127.0.0.1', 9050), timeout=1)
            s.close()
            print(f'Tor ready after {i+1}s')
            return True
        except OSError:
            time.sleep(1)
    print('Tor did not start in time.')
    return False


# Step 1: Try direct connection
print('Querying Hostinger API (direct)...')
result = query_api(label='direct')

# Step 2: Fallback to Tor exit node
if result is None:
    print('Direct failed. Trying via Tor exit node...')
    if start_tor():
        proxies = {'http': 'socks5h://127.0.0.1:9050',
                   'https': 'socks5h://127.0.0.1:9050'}
        result = query_api(proxies=proxies, label='tor')
        if result is not None:
            env_file = os.environ.get('GITHUB_ENV', '')
            if env_file:
                with open(env_file, 'a') as f:
                    f.write('USE_TOR=1\n')

# Step 3: Give up with instructions
if result is None:
    print(MANUAL_GUIDE)
    sys.exit(1)

data = result.json()
vms = data.get('data', [])
if not vms:
    print('No VMs found in account.')
    print(MANUAL_GUIDE)
    sys.exit(1)

vm = vms[0]
vm_id = vm.get('id', 'unknown')
ips = vm.get('ips', [])
vm_ip = (vm.get('main_ip_address') or
         vm.get('ip_address') or
         vm.get('ipv4') or
         (ips[0].get('address') if ips else None) or
         'UNKNOWN')

print(f'VPS found: id={vm_id}  ip={vm_ip}')
out = os.environ.get('GITHUB_OUTPUT', '')
if out:
    with open(out, 'a') as f:
        f.write(f'vm_id={vm_id}\n')
        f.write(f'vm_ip={vm_ip}\n')
