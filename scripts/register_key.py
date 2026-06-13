#!/usr/bin/env python3
import requests, os, sys

key = os.environ['HOSTINGER_KEY']
pub_key = open('/tmp/deploy_key.pub').read().strip()
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

r = requests.post('https://api.hostinger.com/api/vps/v1/public-keys',
                  headers=headers,
                  json={'name': 'gh-deploy-temp', 'key': pub_key},
                  timeout=15)
print(f'Register: {r.status_code} {r.text}')
if r.status_code not in (200, 201):
    sys.exit(1)

key_id = r.json()['data']['id']
github_output = os.environ.get('GITHUB_OUTPUT', '')
if github_output:
    with open(github_output, 'a') as f:
        f.write(f'key_id={key_id}\n')
print(f'Registered key_id={key_id}')
