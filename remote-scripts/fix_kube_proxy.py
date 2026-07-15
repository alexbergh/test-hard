import json
import re
import subprocess
import sys

r = subprocess.run(
    ["kubectl", "-n", "kube-system", "get", "configmap", "kube-proxy", "-o", "json"], capture_output=True, text=True
)
d = json.loads(r.stdout)
conf = d["data"].get("config.conf", "")

if "127.0.0.1:10249" in conf:
    print("SKIP already set to 127.0.0.1:10249")
    sys.exit(0)

if "metricsBindAddress" in conf:
    conf = re.sub(r"metricsBindAddress:\s*\S*", 'metricsBindAddress: "127.0.0.1:10249"', conf)
else:
    conf = conf.rstrip() + '\nmetricsBindAddress: "127.0.0.1:10249"\n'

d["data"]["config.conf"] = conf
r2 = subprocess.run(["kubectl", "apply", "-f", "-"], input=json.dumps(d), capture_output=True, text=True)
print(r2.stdout.strip() or r2.stderr.strip())
