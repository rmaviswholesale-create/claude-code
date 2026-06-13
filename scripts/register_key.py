#!/usr/bin/env python3
import requests, os, sys

key = os.environ['HOSTINGER_KEY']
pub_key = open('/tmp/deploy_key.pub').read().strip()
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}
proxies = ({'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
           if os.environ.get('USE_TOR') == '1' else None)

r = requests.post('https://api.hostinger.com/api/vps/v1/public-keys',
                  headers=headers,
                  json={'name': 'gh-deploy-temp', 'key': pub_key},
                  proxies=proxies, timeout=20)
print(f'Register: {r.status_code} {r.text}')
if r.status_code not in (200, 201):
    sys.exit(1)

key_id = r.json()['data']['id']
out = os.environ.get('GITHUB_OUTPUT', '')
if out:
    with open(out, 'a') as f:
        f.write(f'key_id={key_id}\n')
print(f'Registered key_id={key_id}')
