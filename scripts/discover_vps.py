#!/usr/bin/env python3
"""Discover VPS IP via Hostinger API. Falls back to a clear manual guide."""
import requests, os, sys, time

MANUAL_GUIDE = """
============================================================
  ACTION REQUIRED: Hostinger API unreachable from GitHub Actions
============================================================

  Option A — One-command deploy via Hostinger VPS console (EASIEST):
    1. Log into hPanel (hpanel.hostinger.com)
    2. Click VPS → your server → Console (or Terminal)
    3. Paste this one command and press Enter:

       curl -fsSL https://raw.githubusercontent.com/rmaviswholesale-create/claude-code/main/setup.sh | bash

    Your site will be live in about 30 seconds.

  Option B — Supply your VPS IP so GitHub Actions can deploy:
    1. Find your VPS IP in hPanel → VPS → server overview
    2. Go to: github.com/rmaviswholesale-create/claude-code/settings/secrets/actions
    3. Add secret: VPS_IP  =  <your VPS IP address>
    4. Add secret: VPS_PASSWORD  =  <your VPS root password>
    5. Push any small change to main — the workflow will deploy automatically.

    OR manually trigger this workflow at:
    github.com/rmaviswholesale-create/claude-code/actions
    → "Deploy to Hostinger VPS" → "Run workflow" → fill in IP + password
============================================================
"""

key = os.environ.get('HOSTINGER_KEY', '')
headers = {
    'Authorization': f'Bearer {key}',
    'Accept': 'application/json',
    'User-Agent': 'github-actions-deploy/1.0',
}

for attempt in range(1, 4):
    print(f'Attempt {attempt}/3 — querying Hostinger API...')
    try:
        r = requests.get(
            'https://api.hostinger.com/api/vps/v1/virtual-machines',
            headers=headers, timeout=20
        )
        print(f'HTTP {r.status_code}')
        if r.status_code == 200:
            break
        print(f'Response: {r.text[:400]}')
        if attempt < 3:
            time.sleep(10)
    except Exception as e:
        print(f'Connection error: {e}')
        if attempt < 3:
            time.sleep(10)
else:
    print(MANUAL_GUIDE)
    sys.exit(1)

data = r.json()
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
