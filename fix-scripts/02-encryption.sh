#!/bin/bash
# Fix: Encryption at rest for Secrets
ENC_DIR=/etc/kubernetes/encryption
ENC_CFG=$ENC_DIR/encryption-config.yaml
API_MANIFEST=/etc/kubernetes/manifests/kube-apiserver.yaml

mkdir -p $ENC_DIR

if [ -f "$ENC_CFG" ]; then
    echo "SKIP encryption-config.yaml already exists"
else
    KEY=$(python3 -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())")
    cat > $ENC_CFG <<ENCEOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${KEY}
      - identity: {}
ENCEOF
    chmod 600 $ENC_CFG
    echo "CREATED $ENC_CFG"
fi

# Add flag and volume to kube-apiserver manifest
FLAG='--encryption-provider-config=/etc/kubernetes/encryption/encryption-config.yaml'

if grep -q 'encryption-provider-config' $API_MANIFEST; then
    echo "SKIP kube-apiserver already has encryption-provider-config"
else
    python3 - "$API_MANIFEST" "$FLAG" <<'PYEOF'
import sys, re

path = sys.argv[1]
flag = sys.argv[2]

with open(path) as fh:
    txt = fh.read()

lines = txt.split('\n')
new_lines = []
inserted_flag = False

for line in lines:
    new_lines.append(line)
    if not inserted_flag and re.match(r'\s+-\s+kube-apiserver\s*$', line):
        indent = re.match(r'^(\s+)', line).group(1)
        new_lines.append(f'{indent}- {flag}')
        inserted_flag = True

txt = '\n'.join(new_lines)

# Add volumeMount if not present
if 'encryption-config' not in txt:
    vm = '    - mountPath: /etc/kubernetes/encryption\n      name: encryption-config\n      readOnly: true\n'
    txt = re.sub(r'(    volumeMounts:\n)', r'\1' + vm, txt, count=1)
    vol = '  - hostPath:\n      path: /etc/kubernetes/encryption\n      type: DirectoryOrCreate\n    name: encryption-config\n'
    txt = re.sub(r'(  volumes:\n)', r'\1' + vol, txt, count=1)

with open(path, 'w') as fh:
    fh.write(txt)

print(f'DONE {path}')
PYEOF
fi

echo "Waiting 40s for apiserver restart..."
sleep 40
kubectl get nodes --no-headers 2>/dev/null | head -5

# Re-encrypt all existing secrets
echo "Re-encrypting existing secrets..."
kubectl get secrets -A -o json 2>/dev/null | \
  python3 -c "
import json,sys,subprocess
d=json.load(sys.stdin)
count=0
for s in d.get('items',[]):
    ns=s['metadata']['namespace']
    nm=s['metadata']['name']
    r=subprocess.run(['kubectl','replace','-f','-','-n',ns],
      input=json.dumps(s), capture_output=True, text=True)
    if r.returncode==0: count+=1
print(f'Re-encrypted {count} secrets')
" 2>/dev/null

echo "ENCRYPTION_FIX_DONE"
