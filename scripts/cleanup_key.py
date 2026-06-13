#!/usr/bin/env python3
import requests, os, sys

key = os.environ['HOSTINGER_KEY']
key_id = os.environ.get('KEY_ID', '')
if not key_id or key_id == 'null':
    print('No key to clean up')
    sys.exit(0)

headers = {'Authorization': f'Bearer {key}'}
r = requests.delete(f'https://api.hostinger.com/api/vps/v1/public-keys/{key_id}',
                    headers=headers, timeout=15)
print(f'Cleanup: {r.status_code}')
