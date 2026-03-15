#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


GS = b"\x1d"


def run(cmd: list[str], env: dict[str, str] | None = None, input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input_bytes,
        env=env,
        capture_output=True,
        check=True,
    )


def load_env_required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


def read_payload_base(path: Path) -> bytes:
    data = path.read_bytes()
    if data.endswith(b"\n"):
        data = data[:-1]
    return data


def verify_chain(ca_crt: Path, mfg_crt: Path) -> None:
    proc = run(
        ["openssl", "verify", "-CAfile", str(ca_crt), str(mfg_crt)]
    )
    out = proc.stdout.decode(errors="replace").strip()
    if not out.endswith(": OK"):
        raise RuntimeError(f"Falha na verificação da cadeia: {out}")


def cert_der(cert_path: Path) -> bytes:
    proc = run(
        ["openssl", "x509", "-in", str(cert_path), "-outform", "der"]
    )
    return proc.stdout


def cert_subject(cert_path: Path) -> str:
    proc = run(
        ["openssl", "x509", "-in", str(cert_path), "-noout", "-subject"]
    )
    return proc.stdout.decode(errors="replace").strip()


def cert_issuer(cert_path: Path) -> str:
    proc = run(
        ["openssl", "x509", "-in", str(cert_path), "-noout", "-issuer"]
    )
    return proc.stdout.decode(errors="replace").strip()


def cert_fingerprint_sha256(cert_path: Path) -> str:
    proc = run(
        ["openssl", "x509", "-in", str(cert_path), "-noout", "-fingerprint", "-sha256"]
    )
    line = proc.stdout.decode(errors="replace").strip()
    # Ex.: sha256 Fingerprint=AA:BB:CC...
    return line.split("=", 1)[1].replace(":", "").lower()


def make_kid(cert_path: Path, length: int = 16) -> str:
    digest = hashlib.sha256(cert_der(cert_path)).hexdigest()
    return digest[:length]


def sign_with_pkcs11(data: bytes, hsm_key_uri: str, hsm_module: str, softhsm_conf: str, hsm_pin: str) -> bytes:
    env = os.environ.copy()
    env["SOFTHSM2_CONF"] = softhsm_conf
    env["PKCS11_MODULE_PATH"] = hsm_module
    env["PKCS11_PIN"] = hsm_pin

    with tempfile.NamedTemporaryFile(delete=False) as f_in, tempfile.NamedTemporaryFile(delete=False) as f_out:
        in_path = Path(f_in.name)
        out_path = Path(f_out.name)

    try:
        in_path.write_bytes(data)

        cmd = [
            "openssl", "dgst", "-sha256",
            "-engine", "pkcs11",
            "-keyform", "engine",
            "-sign", hsm_key_uri,
            "-out", str(out_path),
            str(in_path),
        ]
        run(cmd, env=env)
        return out_path.read_bytes()
    finally:
        try:
            in_path.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            out_path.unlink(missing_ok=True)
        except Exception:
            pass


def build_final_payload(gs1_base: bytes, kid: str, sig_b64u: str) -> bytes:
    return gs1_base + GS + f"92{kid}".encode("utf-8") + GS + f"91{sig_b64u}".encode("utf-8")


def main() -> int:
    project_root = Path.cwd()

    data_dir = project_root / "data"
    config_dir = project_root / "config"
    data_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    ca_crt = project_root / load_env_required("CA_CRT")
    mfg_crt = project_root / load_env_required("MFG_CRT")

    softhsm_conf = load_env_required("SOFTHSM2_CONF")
    hsm_module = load_env_required("HSM_MODULE")
    hsm_pin = load_env_required("HSM_PIN")

    hsm_key_uri = os.environ.get("HSM_MFG_KEY")
    if not hsm_key_uri:
        token = load_env_required("HSM_TOKEN_LABEL")
        label = load_env_required("HSM_KEY_LABEL")
        hsm_key_uri = f"pkcs11:token={token};object={label};type=private"

    gs1_base_path = data_dir / "gs1_base.txt"
    if not gs1_base_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {gs1_base_path}")

    gs1_base = read_payload_base(gs1_base_path)
    if GS not in gs1_base:
        raise RuntimeError("O payload base não contém o separador GS esperado (ASCII 29).")

    print("[1/5] Validando cadeia do certificado do fabricante...")
    verify_chain(ca_crt, mfg_crt)
    print("[OK] Cadeia válida.")

    print("[2/5] Gerando KID estável a partir do certificado...")
    kid = make_kid(mfg_crt, length=16)
    print(f"[OK] KID: {kid}")

    print("[3/5] Assinando payload base com chave privada no HSM...")
    signature_raw = sign_with_pkcs11(
        data=gs1_base,
        hsm_key_uri=hsm_key_uri,
        hsm_module=hsm_module,
        softhsm_conf=softhsm_conf,
        hsm_pin=hsm_pin,
    )
    sig_b64u = base64.urlsafe_b64encode(signature_raw).decode("ascii").rstrip("=")
    print("[OK] Assinatura gerada.")

    print("[4/5] Montando payload final...")
    payload = build_final_payload(gs1_base, kid, sig_b64u)

    print("[5/5] Salvando artefatos...")
    (data_dir / "signature.b64u").write_text(sig_b64u + "\n", encoding="utf-8")
    (data_dir / "kid.txt").write_text(kid + "\n", encoding="utf-8")
    (data_dir / "payload.txt").write_bytes(payload + b"\n")

    cert_map = {
        kid: {
            "cert_path": str(mfg_crt),
            "cert_sha256": cert_fingerprint_sha256(mfg_crt),
            "subject": cert_subject(mfg_crt),
            "issuer": cert_issuer(mfg_crt),
        }
    }
    (config_dir / "cert_map.json").write_text(
        json.dumps(cert_map, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("[OK] Arquivos gerados:")
    print(f"  - {data_dir / 'signature.b64u'}")
    print(f"  - {data_dir / 'kid.txt'}")
    print(f"  - {data_dir / 'payload.txt'}")
    print(f"  - {config_dir / 'cert_map.json'}")
    print()
    print("Resumo:")
    print(f"  KID             : {kid}")
    print(f"  Base tem GS?    : {GS in gs1_base}")
    print(f"  Payload tem GS? : {GS in payload}")
    print(f"  Tamanho sig b64u: {len(sig_b64u)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
