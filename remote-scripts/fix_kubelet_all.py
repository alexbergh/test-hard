#!/usr/bin/env python3
"""
Fix kubelet config.yaml on ALL nodes (master + workers):
  4.2.1  authentication.anonymous.enabled: false
  4.2.2  authorization.mode: Webhook
  4.2.6  protectKernelDefaults: true  (+sysctl)
  4.2.9  eventRecordQPS: 5
  4.2.11 rotateCertificates: true
  4.2.13 podPidsLimit: 4096
  4.2.14 seccompDefault: true
Then: systemctl restart kubelet
"""

import os
import re
import subprocess

CONFIG = "/var/lib/kubelet/config.yaml"


def run(cmd, inp=None):
    r = subprocess.run(cmd, capture_output=True, text=True, input=inp)
    return r.stdout.strip(), r.stderr.strip()


# Read current config
with open(CONFIG) as f:
    txt = f.read()

print(f"Original config length: {len(txt)} chars")


# ── Helper: set/replace a simple top-level key ───────────────────────────────
def set_key(text, key, value):
    pattern = rf"^({re.escape(key)}:\s*).*$"
    if re.search(pattern, text, re.MULTILINE):
        new_text = re.sub(pattern, rf"\g<1>{value}", text, flags=re.MULTILINE)
        return new_text, False  # replaced
    else:
        return text + f"\n{key}: {value}", True  # appended


# ── 4.2.9 eventRecordQPS ─────────────────────────────────────────────────────
txt, appended = set_key(txt, "eventRecordQPS", "5")
print(f"4.2.9  eventRecordQPS: {'appended' if appended else 'replaced'}")

# ── 4.2.11 rotateCertificates ────────────────────────────────────────────────
txt, appended = set_key(txt, "rotateCertificates", "true")
print(f"4.2.11 rotateCertificates: {'appended' if appended else 'replaced'}")

# ── 4.2.13 podPidsLimit ──────────────────────────────────────────────────────
txt, appended = set_key(txt, "podPidsLimit", "4096")
print(f"4.2.13 podPidsLimit: {'appended' if appended else 'replaced'}")

# ── 4.2.14 seccompDefault ────────────────────────────────────────────────────
txt, appended = set_key(txt, "seccompDefault", "true")
print(f"4.2.14 seccompDefault: {'appended' if appended else 'replaced'}")

# ── 4.2.6 protectKernelDefaults ──────────────────────────────────────────────
txt, appended = set_key(txt, "protectKernelDefaults", "true")
print(f"4.2.6  protectKernelDefaults: {'appended' if appended else 'replaced'}")

# ── 4.2.1 authentication.anonymous.enabled: false ────────────────────────────
# This is nested: authentication:\n  anonymous:\n    enabled: false
# Check if already present
if re.search(r"anonymous:\s*\n\s+enabled:\s*false", txt):
    print("4.2.1  anonymous.enabled already false — SKIP")
elif re.search(r"authentication:", txt):
    # Replace any existing anonymous enabled setting
    if re.search(r"(anonymous:\s*\n\s+enabled:\s*)", txt):
        txt = re.sub(r"(anonymous:\s*\n\s+enabled:\s*)\S+", r"\g<1>false", txt)
        print("4.2.1  anonymous.enabled: replaced")
    else:
        # Inject after authentication: block
        txt = re.sub(r"(authentication:\n)", "authentication:\n  anonymous:\n    enabled: false\n", txt, count=1)
        print("4.2.1  anonymous block injected under authentication:")
else:
    txt += "\nauthentication:\n  anonymous:\n    enabled: false\n"
    print("4.2.1  authentication block appended")

# ── 4.2.2 authorization.mode: Webhook ────────────────────────────────────────
if re.search(r"authorization:\s*\n\s+mode:\s*Webhook", txt):
    print("4.2.2  authorization.mode already Webhook — SKIP")
elif re.search(r"authorization:\s*\n\s+mode:", txt):
    txt = re.sub(r"(authorization:\s*\n\s+mode:\s*)\S+", r"\g<1>Webhook", txt)
    print("4.2.2  authorization.mode: replaced with Webhook")
elif re.search(r"authorization:", txt):
    txt = re.sub(r"(authorization:\n)", "authorization:\n  mode: Webhook\n", txt, count=1)
    print("4.2.2  mode: Webhook injected under authorization:")
else:
    txt += "\nauthorization:\n  mode: Webhook\n"
    print("4.2.2  authorization block appended")

# ── Write back ────────────────────────────────────────────────────────────────
backup = CONFIG + ".bak"
if not os.path.exists(backup):
    with open(backup, "w") as f:
        with open(CONFIG) as orig:
            f.write(orig.read())
    print(f"Backup saved: {backup}")

with open(CONFIG, "w") as f:
    f.write(txt)
print(f"Config written: {CONFIG}")

# ── sysctl for protectKernelDefaults (4.2.6) ─────────────────────────────────
sysctl_settings = [
    ("vm.overcommit_memory", "1"),
    ("vm.panic_on_oom", "0"),
    ("kernel.panic", "10"),
    ("kernel.panic_on_oops", "1"),
    ("kernel.keys.root_maxkeys", "1000000"),
    ("kernel.keys.root_maxbytes", "25000000"),
]
print("\nApplying sysctl settings for protectKernelDefaults:")
for key, val in sysctl_settings:
    out, err = run(["sysctl", "-w", f"{key}={val}"])
    print(f"  {key}={val}: {out or err}")

# Persist in /etc/sysctl.d/
sysctl_file = "/etc/sysctl.d/99-kubelet-protect-kernel.conf"
lines = [f"{k} = {v}\n" for k, v in sysctl_settings]
with open(sysctl_file, "w") as f:
    f.writelines(lines)
print(f"Persisted sysctl to {sysctl_file}")

# ── Restart kubelet ───────────────────────────────────────────────────────────
print("\nRestarting kubelet...")
out, err = run(["systemctl", "restart", "kubelet"])
print(f"restart: {out or err or 'ok'}")

import time

time.sleep(8)
out, err = run(["systemctl", "is-active", "kubelet"])
print(f"kubelet status: {out}")
if out != "active":
    out2, err2 = run(["journalctl", "-u", "kubelet", "--no-pager", "-n", "20"])
    print("kubelet journal:")
    print(out2[-2000:])

print("\nDONE")
