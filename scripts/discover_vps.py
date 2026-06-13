#!/usr/bin/env python3
import requests, os, sys

key = os.environ['HOSTINGER_KEY']
headers = {
    'Authorization': f'Bearer {key}',
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (compatible; deploy/1.0)'
}

try:
    r = requests.get('https://api.hostinger.com/api/vps/v1/virtual-machines',
                     headers=headers, timeout=15)
    print(f'HTTP Status: {r.status_code}')
    print(f'Response: {r.text[:500]}')
except Exception as e:
    print(f'Connection error: {e}')
    sys.exit(1)

if r.status_code != 200:
    print(f'API error {r.status_code}: {r.text}')
    sys.exit(1)

data = r.json()
vms = data.get('data', [])
if not vms:
    print('No VMs found')
    sys.exit(1)

vm = vms[0]
vm_id = vm.get('id', 'unknown')
ips = vm.get('ips', [])
vm_ip = (vm.get('main_ip_address') or
         vm.get('ip_address') or
         vm.get('ipv4') or
         (ips[0].get('address') if ips else None) or
         'UNKNOWN')

print(f'Found VPS: id={vm_id} ip={vm_ip}')

github_output = os.environ.get('GITHUB_OUTPUT', '')
if github_output:
    with open(github_output, 'a') as f:
        f.write(f'vm_id={vm_id}\n')
        f.write(f'vm_ip={vm_ip}\n')
