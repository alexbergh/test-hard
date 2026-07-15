import subprocess, os, json

r = subprocess.run(
    ['kubectl', 'get', 'clusterpolicy', 'verify-image-signatures', '--no-headers'],
    capture_output=True, text=True
)
if r.returncode == 0 and 'verify-image-signatures' in r.stdout:
    print('SKIP policy already exists')
    raise SystemExit(0)

pub_key = ''
for p in ['/root/cosign-keys/cosign.pub', '/root/cosign.pub']:
    if os.path.exists(p):
        with open(p) as f:
            pub_key = f.read().strip()
        print('Found cosign key: ' + p)
        break

if not pub_key:
    pub_key = '# UPDATE WITH REAL COSIGN PUBLIC KEY'
    print('WARN: cosign.pub not found, using placeholder')

key_indented = '\n'.join('                    ' + l for l in pub_key.splitlines())

policy_lines = [
    'apiVersion: kyverno.io/v1\n',
    'kind: ClusterPolicy\n',
    'metadata:\n',
    '  name: verify-image-signatures\n',
    '  annotations:\n',
    '    policies.kyverno.io/title: Verify Image Signatures\n',
    'spec:\n',
    '  validationFailureAction: Audit\n',
    '  background: false\n',
    '  rules:\n',
    '    - name: verify-image\n',
    '      match:\n',
    '        any:\n',
    '        - resources:\n',
    '            kinds:\n',
    '              - Pod\n',
    '            namespaces:\n',
    '              - production\n',
    '      verifyImages:\n',
    '        - imageReferences:\n',
    '            - "*"\n',
    '          attestors:\n',
    '            - count: 1\n',
    '              entries:\n',
    '              - keys:\n',
    '                  publicKeys: |-\n',
    key_indented + '\n',
]

with open('/tmp/verify-images.yaml', 'w') as f:
    f.writelines(policy_lines)

r2 = subprocess.run(['kubectl', 'apply', '-f', '/tmp/verify-images.yaml'],
                    capture_output=True, text=True)
print(r2.stdout.strip() or r2.stderr.strip())
