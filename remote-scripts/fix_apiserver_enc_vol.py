import re
import sys

path = "/etc/kubernetes/manifests/kube-apiserver.yaml"

with open(path) as f:
    txt = f.read()

if "encryption-config" in txt:
    print("SKIP: encryption-config volume already present")
    sys.exit(0)

# Add volumeMount before the first existing volumeMount entry
vm_block = "    - mountPath: /etc/kubernetes/encryption\n" "      name: encryption-config\n" "      readOnly: true\n"
txt = re.sub(r"(    volumeMounts:\n)", r"\1" + vm_block, txt, count=1)

# Add volume before the first existing volume entry
vol_block = (
    "  - hostPath:\n"
    "      path: /etc/kubernetes/encryption\n"
    "      type: DirectoryOrCreate\n"
    "    name: encryption-config\n"
)
txt = re.sub(r"(  volumes:\n)", r"\1" + vol_block, txt, count=1)

with open(path, "w") as f:
    f.write(txt)

print("DONE: encryption-config volume and volumeMount added")

# Verify
with open(path) as f:
    for i, line in enumerate(f, 1):
        if "encryption" in line.lower():
            print(f"  {i}: {line.rstrip()}")
