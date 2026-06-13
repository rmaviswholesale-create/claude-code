#!/usr/bin/env python3
import requests, os, sys, time

key = os.environ['HOSTINGER_KEY']
vm_id = os.environ['VM_ID']
key_id = int(os.environ['KEY_ID'])
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

r = requests.post(f'https://api.hostinger.com/api/vps/v1/public-keys/attach/{vm_id}',
                  headers=headers,
                  json={'ids': [key_id]},
                  timeout=15)
print(f'Attach: {r.status_code} {r.text}')
if r.status_code not in (200, 201):
    sys.exit(1)

print('Waiting 60s for key propagation...')
time.sleep(60)
