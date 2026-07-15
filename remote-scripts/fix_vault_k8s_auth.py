#!/usr/bin/env python3
"""
Vault: K8s auth method
- Try to find root token from common locations
- If not found: generate a new one via vault operator generate-root (unseal keys needed)
- Enable kubernetes auth method
- Configure kubernetes_host
"""

import os
import re
import subprocess

K8S_HOST = "https://10.10.10.10:6443"


def run(cmd, inp=None, timeout=30):
    r = subprocess.run(cmd, capture_output=True, text=True, input=inp, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()


# ── Check Vault sealed status ─────────────────────────────────────────────────
out, _ = run(["kubectl", "exec", "-n", "vault", "vault-0", "--", "vault", "status"])
print("Vault status:")
print(out[:300])

sealed = True
for line in out.splitlines():
    if line.startswith("Sealed"):
        sealed = line.split()[-1].lower() == "true"

if sealed:
    print("ERROR: Vault is sealed, cannot proceed")
    raise SystemExit(1)

# ── Search for root token ─────────────────────────────────────────────────────
tok = None
search_paths = [
    "/root/vault-init.txt",
    "/root/vault-keys.txt",
    "/root/vault-root-token.txt",
    "/tmp/vault-init.txt",
    "/root/.vault-token",
]
for path in search_paths:
    if not os.path.exists(path):
        continue
    with open(path) as f:
        content = f.read()
    if not content.strip():
        print(f"  {path}: empty")
        continue
    # Try various patterns
    for pattern in [
        r"Initial Root Token:\s+(\S+)",
        r"Root Token[:\s]+(\S+)",
        r"(hvs\.\S{20,})",
        r"(s\.\S{20,})",
    ]:
        m = re.search(pattern, content)
        if m:
            tok = m.group(1)
            print(f"  Found token in {path}: {tok[:12]}...")
            break
    if tok:
        break

# ── Try to get token from vault agent token ───────────────────────────────────
if not tok:
    print("Token not found in files. Trying kubectl exec vault token lookup...")
    # Try using existing vault token if already logged in
    out2, err2 = run(["kubectl", "exec", "-n", "vault", "vault-0", "--", "vault", "token", "lookup"])
    if "root" in out2.lower() or "policies" in out2.lower():
        print("Vault already has a session token configured, checking auth list...")
        out3, _ = run(["kubectl", "exec", "-n", "vault", "vault-0", "--", "vault", "auth", "list"])
        if "kubernetes" in out3.lower():
            print("SKIP: k8s auth already enabled")
            print(out3[:300])
            raise SystemExit(0)

# ── If still no token: try operator generate-root with stored unseal keys ────
if not tok:
    print("\nAttempting operator generate-root...")
    keys = []
    for path in ["/root/vault-init.txt", "/root/vault-keys.txt"]:
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()
            found = re.findall(r"Unseal Key \d+:\s+(\S+)", content)
            if found:
                keys = found
                print(f"  Found {len(keys)} unseal keys in {path}")
                break

    if len(keys) >= 2:
        # Generate OTP
        out_init, err_init = run(
            [
                "kubectl",
                "exec",
                "-n",
                "vault",
                "vault-0",
                "--",
                "vault",
                "operator",
                "generate-root",
                "-init",
                "-format=json",
            ]
        )
        print("generate-root init:", out_init[:200], err_init[:100])

        try:
            import json

            init_data = json.loads(out_init)
            otp = init_data.get("otp", "")
            nonce = init_data.get("nonce", "")
            encoded_token = None

            for i, key in enumerate(keys[:2]):
                out_step, err_step = run(
                    [
                        "kubectl",
                        "exec",
                        "-n",
                        "vault",
                        "vault-0",
                        "--",
                        "vault",
                        "operator",
                        "generate-root",
                        f"-nonce={nonce}",
                        f"-otp={otp}",
                        key,
                    ]
                )
                print(f"  key {i+1}:", out_step[:150])
                m = re.search(r"Encoded Token\s+(\S+)", out_step)
                if m:
                    encoded_token = m.group(1)

            if encoded_token:
                out_dec, _ = run(
                    [
                        "kubectl",
                        "exec",
                        "-n",
                        "vault",
                        "vault-0",
                        "--",
                        "vault",
                        "operator",
                        "generate-root",
                        f"-otp={otp}",
                        "-decode",
                        encoded_token,
                    ]
                )
                tok = out_dec.strip()
                print(f"  Generated root token: {tok[:12]}...")
                with open("/root/vault-root-token.txt", "w") as f:
                    f.write(tok)
                print("  Token saved to /root/vault-root-token.txt")
        except Exception as e:
            print(f"  generate-root failed: {e}")

if not tok:
    print("\nERROR: Cannot obtain Vault root token.")
    print("Manual steps required:")
    print("  1. kubectl exec -n vault vault-0 -- vault login")
    print("     (enter root token when prompted)")
    print("  2. kubectl exec -n vault vault-0 -- vault auth enable kubernetes")
    print(f"  3. kubectl exec -n vault vault-0 -- vault write auth/kubernetes/config kubernetes_host={K8S_HOST}")
    raise SystemExit(1)

# ── Check if k8s auth already enabled ────────────────────────────────────────
out4, err4 = run(
    ["kubectl", "exec", "-n", "vault", "vault-0", "--", "env", f"VAULT_TOKEN={tok}", "vault", "auth", "list"]
)
print("\nAuth list:", out4[:300])

if "kubernetes" in out4.lower():
    print("SKIP: Kubernetes auth already enabled")
else:
    # Enable
    out5, err5 = run(
        [
            "kubectl",
            "exec",
            "-n",
            "vault",
            "vault-0",
            "--",
            "env",
            f"VAULT_TOKEN={tok}",
            "vault",
            "auth",
            "enable",
            "kubernetes",
        ]
    )
    print("enable kubernetes:", out5 or err5)

    # Configure
    out6, err6 = run(
        [
            "kubectl",
            "exec",
            "-n",
            "vault",
            "vault-0",
            "--",
            "env",
            f"VAULT_TOKEN={tok}",
            "vault",
            "write",
            "auth/kubernetes/config",
            f"kubernetes_host={K8S_HOST}",
        ]
    )
    print("configure k8s host:", out6 or err6)

# ── Verify ────────────────────────────────────────────────────────────────────
out7, _ = run(["kubectl", "exec", "-n", "vault", "vault-0", "--", "env", f"VAULT_TOKEN={tok}", "vault", "auth", "list"])
print("\nFinal auth list:")
print(out7[:400])
print("VAULT_K8S_AUTH_DONE")
