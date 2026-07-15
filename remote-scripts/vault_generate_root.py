#!/usr/bin/env python3
"""
Generate a new Vault root token using operator generate-root.
Requires 2 unseal keys (threshold=2 out of 3).
Since vault-init.txt is empty, we attempt to find keys from:
1. Previous unseal commands (we know vault is unsealed, so keys were used)
2. Re-initialize if not initialized (SKIP - already initialized)
3. Use known static keys from deployment scripts if available

If keys are truly unavailable, re-init vault (DESTRUCTIVE - loses all data).
"""
import subprocess, re, os, json

def run(cmd, inp=None, timeout=30):
    r = subprocess.run(cmd, capture_output=True, text=True, input=inp, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def vexec(vault_cmd, timeout=15):
    return run(['kubectl', 'exec', '-n', 'vault', 'vault-0', '--'] + vault_cmd, timeout=timeout)

print("=== Vault status ===")
out, _ = vexec(['vault', 'status'])
print(out[:300])

# Check if already have auth list working
out2, err2 = vexec(['vault', 'auth', 'list'])
print("\n=== Current auth list (no token) ===")
print(out2[:200] or err2[:200])

# If kubernetes is already there (from a previous login state)
if 'kubernetes' in out2.lower():
    print("SKIP: Kubernetes auth already enabled")
    raise SystemExit(0)

# Try generate-root with no keys (will show OTP + nonce, need to provide keys)
print("\n=== Attempting generate-root init ===")
out3, err3 = vexec(['vault', 'operator', 'generate-root', '-init', '-format=json'])
print(out3[:300] or err3[:200])

if not out3.strip():
    print("ERROR: generate-root failed")
    # Check if there's already a generate-root in progress
    out_cancel, _ = vexec(['vault', 'operator', 'generate-root', '-cancel'])
    print("Cancel result:", out_cancel[:100])
    out3, err3 = vexec(['vault', 'operator', 'generate-root', '-init', '-format=json'])
    print("Retry:", out3[:300] or err3[:200])

try:
    data = json.loads(out3)
    otp   = data.get('otp', '')
    nonce = data.get('nonce', '')
    print(f"\nOTP: {otp[:20]}...")
    print(f"Nonce: {nonce}")
except Exception as e:
    print(f"Could not parse generate-root output: {e}")
    print("Raw:", out3[:500])
    print("\nVault root token recovery requires unseal keys.")
    print("Since vault-init.txt is empty, the keys were lost.")
    print("\nOption 1: If you know the unseal keys, run:")
    print("  kubectl exec -n vault vault-0 -- vault operator generate-root -otp=<OTP> <KEY1>")
    print("  kubectl exec -n vault vault-0 -- vault operator generate-root -otp=<OTP> <KEY2>")
    print("  kubectl exec -n vault vault-0 -- vault operator generate-root -decode=<ENCODED> -otp=<OTP>")
    print("\nOption 2: Re-initialize Vault (DESTRUCTIVE - all secrets lost):")
    print("  kubectl delete pvc -n vault data-vault-0")
    print("  kubectl delete pod -n vault vault-0")
    print("  # Wait for new pod, then: vault operator init -key-shares=3 -key-threshold=2")
    print("  # Save the output to /root/vault-init.txt")
    raise SystemExit(1)

# We have OTP and nonce - but need the unseal keys
# Check if there are any keys stored anywhere
keys = []
for path in ['/root/vault-init.txt', '/root/vault-keys.txt']:
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path) as f:
            content = f.read()
        found = re.findall(r'Unseal Key \d+:\s+(\S+)', content)
        keys.extend(found)

print(f"\nFound {len(keys)} unseal keys")
if len(keys) < 2:
    print("Need at least 2 unseal keys to generate root token.")
    print(f"OTP={otp}")
    print(f"Nonce={nonce}")
    print("\nProvide 2 unseal keys:")
    print(f"  kubectl exec -n vault vault-0 -- vault operator generate-root -nonce={nonce} KEY1")
    print(f"  kubectl exec -n vault vault-0 -- vault operator generate-root -nonce={nonce} KEY2")
    print(f"  kubectl exec -n vault vault-0 -- vault operator generate-root -decode=ENCODED_TOKEN -otp={otp}")
    raise SystemExit(1)

# Provide keys
encoded_token = None
for i, key in enumerate(keys[:2]):
    out_k, err_k = vexec(['vault', 'operator', 'generate-root',
                           f'-nonce={nonce}', key], timeout=15)
    print(f"Key {i+1} result: {out_k[:200] or err_k[:100]}")
    m = re.search(r'Encoded Token\s+(\S+)', out_k)
    if m:
        encoded_token = m.group(1)
        print(f"Encoded token: {encoded_token[:20]}...")

if not encoded_token:
    print("ERROR: No encoded token after providing keys")
    raise SystemExit(1)

# Decode
out_dec, err_dec = vexec(['vault', 'operator', 'generate-root',
                           f'-otp={otp}', '-decode', encoded_token], timeout=15)
root_token = out_dec.strip()
print(f"\nRoot token: {root_token[:12]}...")

# Save token
with open('/root/vault-root-token.txt', 'w') as f:
    f.write(root_token)
print("Saved to /root/vault-root-token.txt")

# Enable k8s auth
out_al, _ = vexec(['env', f'VAULT_TOKEN={root_token}', 'vault', 'auth', 'list'])
if 'kubernetes' in out_al.lower():
    print("k8s auth already enabled")
else:
    _, e1 = vexec(['env', f'VAULT_TOKEN={root_token}', 'vault', 'auth', 'enable', 'kubernetes'])
    print(f"enable kubernetes: {e1 or 'ok'}")
    _, e2 = vexec(['env', f'VAULT_TOKEN={root_token}', 'vault', 'write',
                   'auth/kubernetes/config', 'kubernetes_host=https://10.10.10.10:6443'])
    print(f"configure: {e2 or 'ok'}")

out_final, _ = vexec(['env', f'VAULT_TOKEN={root_token}', 'vault', 'auth', 'list'])
print("\nFinal auth list:")
print(out_final[:300])
print("VAULT_K8S_AUTH_DONE")
