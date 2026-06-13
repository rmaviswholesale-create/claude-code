#!/usr/bin/env python3
import requests, os, sys, time

key = os.environ['HOSTINGER_KEY']
vm_id = os.environ['VM_ID']
key_id = int(os.environ['KEY_ID'])
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}
proxies = ({'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
           if os.environ.get('USE_TOR') == '1' else None)

r = requests.post(f'https://api.hostinger.com/api/vps/v1/public-keys/attach/{vm_id}',
                  headers=headers,
                  json={'ids': [key_id]},
                  proxies=proxies, timeout=20)
print(f'Attach: {r.status_code} {r.text}')
if r.status_code not in (200, 201):
    sys.exit(1)

print('Waiting 60s for key propagation...')
time.sleep(60)
