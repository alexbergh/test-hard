import base64
import os
import re
import sys

ENC_DIR = "/etc/kubernetes/encryption"
ENC_CFG = ENC_DIR + "/encryption-config.yaml"
API = "/etc/kubernetes/manifests/kube-apiserver.yaml"

os.makedirs(ENC_DIR, exist_ok=True)

if not os.path.exists(ENC_CFG):
    key = base64.b64encode(os.urandom(32)).decode()
    lines = [
        "apiVersion: apiserver.config.k8s.io/v1\n",
        "kind: EncryptionConfiguration\n",
        "resources:\n",
        "  - resources:\n",
        "      - secrets\n",
        "    providers:\n",
        "      - aescbc:\n",
        "          keys:\n",
        "            - name: key1\n",
        "              secret: " + key + "\n",
        "      - identity: {}\n",
    ]
    with open(ENC_CFG, "w") as f:
        f.writelines(lines)
    os.chmod(ENC_CFG, 0o600)
    print("CREATED " + ENC_CFG)
else:
    print("SKIP encryption-config exists")

FLAG = "--encryption-provider-config=/etc/kubernetes/encryption/encryption-config.yaml"
with open(API) as f:
    txt = f.read()

if "encryption-provider-config" in txt:
    print("SKIP apiserver already has flag")
    sys.exit(0)

txt_lines = txt.split("\n")
new_lines = []
inserted = False
for line in txt_lines:
    new_lines.append(line)
    if not inserted and re.match(r"\s+-\s+kube-apiserver\s*$", line):
        m = re.match(r"^(\s+)", line)
        indent = m.group(1) if m else "    "
        new_lines.append(indent + "- " + FLAG)
        inserted = True
txt = "\n".join(new_lines)

if "encryption-config" not in txt:
    vm = "    - mountPath: /etc/kubernetes/encryption\n      name: encryption-config\n      readOnly: true\n"
    txt = re.sub(r"(    volumeMounts:\n)", r"\1" + vm, txt, count=1)
    vol = "  - hostPath:\n      path: /etc/kubernetes/encryption\n      type: DirectoryOrCreate\n    name: encryption-config\n"
    txt = re.sub(r"(  volumes:\n)", r"\1" + vol, txt, count=1)

with open(API, "w") as f:
    f.write(txt)
print("DONE apiserver updated with encryption-provider-config")
