import json, subprocess, sys

r = subprocess.run(['kubectl', 'get', 'secrets', '-A', '-o', 'json'],
                   capture_output=True, text=True)
try:
    data = json.loads(r.stdout)
except Exception as e:
    print('Error parsing secrets:', e)
    sys.exit(1)

count = 0
errors = 0
for secret in data.get('items', []):
    ns = secret['metadata']['namespace']
    name = secret['metadata']['name']
    secret_json = json.dumps(secret)
    result = subprocess.run(
        ['kubectl', 'replace', '--force', '-f', '-'],
        input=secret_json, capture_output=True, text=True
    )
    if result.returncode == 0:
        count += 1
    else:
        errors += 1

print(f'Re-encrypted: {count} secrets, errors: {errors}')
