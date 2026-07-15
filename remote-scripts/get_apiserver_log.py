import subprocess, os

r = subprocess.run(
    ['crictl', 'ps', '-a', '--name', 'kube-apiserver', '-o', 'json'],
    capture_output=True, text=True
)

if r.returncode != 0 or not r.stdout.strip():
    print("crictl ps failed:", r.stderr[:200])
else:
    import json
    try:
        data = json.loads(r.stdout)
        containers = data.get('containers', [])
        if containers:
            cid = containers[0]['id']
            r2 = subprocess.run(['crictl', 'logs', '--tail=40', cid],
                                capture_output=True, text=True)
            print("STDOUT:", r2.stdout[-2000:])
            print("STDERR:", r2.stderr[-2000:])
        else:
            print("No kube-apiserver containers found")
    except Exception as e:
        print("Parse error:", e, r.stdout[:500])

print("---manifest snippet---")
r3 = subprocess.run(['grep', '-n', 'encryption\|volume\|Volume\|profil',
                     '/etc/kubernetes/manifests/kube-apiserver.yaml'],
                    capture_output=True, text=True)
print(r3.stdout)
