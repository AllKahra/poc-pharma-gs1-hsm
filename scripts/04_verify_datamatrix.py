#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image
from pylibdmtx.pylibdmtx import decode


GS = b"\x1d"


def run(cmd: list[str], input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input_bytes,
        capture_output=True,
        check=True,
    )


def decode_datamatrix(image_path: Path) -> bytes:
    img = Image.open(image_path)
    decoded_items = decode(img)
    if not decoded_items:
        raise RuntimeError("Falha ao decodificar o DataMatrix.")
    return decoded_items[0].data


def parse_fixed_base_and_sections(payload: bytes) -> dict:
    parts = payload.split(GS)
    if len(parts) != 4:
        raise RuntimeError(f"Formato inesperado do payload: esperado 4 partes, obtido {len(parts)}")

    part1, part2, part3, part4 = parts

    if not part1.startswith(b"01"):
        raise RuntimeError("Payload inválido: não começa com AI 01.")
    if b"17" not in part1:
        raise RuntimeError("Payload inválido: AI 17 não encontrado na primeira parte.")
    if not part2.startswith(b"21"):
        raise RuntimeError("Payload inválido: segunda parte não começa com AI 21.")
    if not part3.startswith(b"92"):
        raise RuntimeError("Payload inválido: terceira parte não começa com AI 92.")
    if not part4.startswith(b"91"):
        raise RuntimeError("Payload inválido: quarta parte não começa com AI 91.")

    # part1 = 01 + GTIN(14) + 17 + EXP(6) + 10 + LOT(variable)
    if len(part1) < 2 + 14 + 2 + 6 + 2 + 1:
        raise RuntimeError("Primeira parte do payload é curta demais.")

    if part1[0:2] != b"01":
        raise RuntimeError("AI 01 inválido.")
    gtin = part1[2:16].decode("utf-8")

    if part1[16:18] != b"17":
        raise RuntimeError("AI 17 inválido ou fora de posição.")
    exp = part1[18:24].decode("utf-8")

    if part1[24:26] != b"10":
        raise RuntimeError("AI 10 inválido ou fora de posição.")
    lot = part1[26:].decode("utf-8")

    serial = part2[2:].decode("utf-8")
    kid = part3[2:].decode("utf-8")
    sig_b64u = part4[2:].decode("utf-8")

    signed_base = part1 + GS + part2

    return {
        "gtin": gtin,
        "expiration_gs1": exp,
        "lot": lot,
        "serial": serial,
        "kid": kid,
        "signature_b64u": sig_b64u,
        "signed_base": signed_base,
        "payload_parts": parts,
    }


def load_cert_path_from_kid(cert_map_path: Path, kid: str) -> Path:
    cert_map = json.loads(cert_map_path.read_text(encoding="utf-8"))
    if kid not in cert_map:
        raise RuntimeError(f"KID não encontrado em cert_map.json: {kid}")
    cert_path = Path(cert_map[kid]["cert_path"])
    if not cert_path.exists():
        raise RuntimeError(f"Certificado do KID não encontrado: {cert_path}")
    return cert_path


def verify_signature(cert_path: Path, signed_base: bytes, signature_b64u: str) -> tuple[bool, str]:
    padding = "=" * (-len(signature_b64u) % 4)
    signature_raw = base64.urlsafe_b64decode(signature_b64u + padding)

    with NamedTemporaryFile(delete=False) as f_sig, NamedTemporaryFile(delete=False) as f_data:
        sig_path = Path(f_sig.name)
        data_path = Path(f_data.name)

    try:
        sig_path.write_bytes(signature_raw)
        data_path.write_bytes(signed_base)

        pubkey_proc = run(["openssl", "x509", "-in", str(cert_path), "-pubkey", "-noout"])
        pubkey_pem = pubkey_proc.stdout

        with NamedTemporaryFile(delete=False) as f_pub:
            pub_path = Path(f_pub.name)

        try:
            pub_path.write_bytes(pubkey_pem)

            proc = subprocess.run(
                [
                    "openssl", "dgst", "-sha256",
                    "-verify", str(pub_path),
                    "-signature", str(sig_path),
                    str(data_path),
                ],
                capture_output=True,
            )

            stdout = proc.stdout.decode(errors="replace").strip()
            stderr = proc.stderr.decode(errors="replace").strip()
            combined = (stdout + "\n" + stderr).strip()

            return proc.returncode == 0 and "Verified OK" in combined, combined
        finally:
            pub_path.unlink(missing_ok=True)
    finally:
        sig_path.unlink(missing_ok=True)
        data_path.unlink(missing_ok=True)


def verify_chain(ca_crt: Path, cert_path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["openssl", "verify", "-CAfile", str(ca_crt), str(cert_path)],
        capture_output=True,
    )
    output = (proc.stdout.decode(errors="replace") + proc.stderr.decode(errors="replace")).strip()
    return proc.returncode == 0 and output.endswith(": OK"), output


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    return json.loads(text)


def save_registry(path: Path, registry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_clone_registry(registry_path: Path, gtin: str, serial: str, lot: str) -> tuple[bool, dict]:
    registry = load_registry(registry_path)
    key = f"{gtin}|{serial}"
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if key not in registry:
        registry[key] = {
            "gtin": gtin,
            "serial": serial,
            "lot": lot,
            "first_seen": now,
            "last_seen": now,
            "seen_count": 1,
        }
        save_registry(registry_path, registry)
        return False, registry[key]

    registry[key]["last_seen"] = now
    registry[key]["seen_count"] = int(registry[key].get("seen_count", 1)) + 1
    save_registry(registry_path, registry)
    return True, registry[key]


def build_hri(info: dict) -> str:
    return (
        f"(01){info['gtin']}"
        f"(17){info['expiration_gs1']}"
        f"(10){info['lot']}"
        f"(21){info['serial']}"
        f"(92){info['kid']}"
        f"(91){info['signature_b64u']}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verifica autenticidade, integridade e clonagem do DataMatrix da PoC."
    )
    parser.add_argument("image", help="Caminho da imagem DataMatrix. Ex.: dm/medicine.png")
    parser.add_argument(
        "--check-chain",
        action="store_true",
        help="Valida a cadeia do certificado do fabricante contra a CA.",
    )
    parser.add_argument(
        "--registry",
        default="registry/seen_serials.json",
        help="Arquivo JSON do registro de clonagem. Padrão: registry/seen_serials.json",
    )
    parser.add_argument(
        "--cert-map",
        default="config/cert_map.json",
        help="Arquivo de mapeamento KID -> certificado. Padrão: config/cert_map.json",
    )
    parser.add_argument(
        "--ca",
        default="pki/ca.crt",
        help="Certificado da CA. Padrão: pki/ca.crt",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    image_path = Path(args.image)
    cert_map_path = Path(args.cert_map)
    ca_crt = Path(args.ca)
    registry_path = Path(args.registry)

    if not image_path.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")
    if not cert_map_path.exists():
        raise FileNotFoundError(f"cert_map.json não encontrado: {cert_map_path}")
    if args.check_chain and not ca_crt.exists():
        raise FileNotFoundError(f"Certificado CA não encontrado: {ca_crt}")

    print("[1/6] Decodificando DataMatrix...")
    payload = decode_datamatrix(image_path).rstrip(b"\n")
    print(f"[OK] Payload decodificado. Tamanho: {len(payload)} bytes")

    print("[2/6] Fazendo parsing do payload...")
    info = parse_fixed_base_and_sections(payload)
    print("[OK] Payload parseado com sucesso.")
    print(f"  GTIN  : {info['gtin']}")
    print(f"  EXP   : {info['expiration_gs1']}")
    print(f"  LOT   : {info['lot']}")
    print(f"  SERIAL: {info['serial']}")
    print(f"  KID   : {info['kid']}")

    print("[3/6] Localizando certificado pelo KID...")
    cert_path = load_cert_path_from_kid(cert_map_path, info["kid"])
    print(f"[OK] Certificado localizado: {cert_path}")

    print("[4/6] Verificando assinatura...")
    sig_ok, sig_output = verify_signature(cert_path, info["signed_base"], info["signature_b64u"])
    print(sig_output if sig_output else "[sem saída do openssl]")
    if not sig_ok:
        print()
        print("[RESULTADO] INVÁLIDO")
        print("Motivo: assinatura inválida. Houve adulteração ou payload inconsistente.")
        return 2

    print("[OK] Assinatura válida.")

    if args.check_chain:
        print("[5/6] Validando cadeia do certificado...")
        chain_ok, chain_output = verify_chain(ca_crt, cert_path)
        print(chain_output if chain_output else "[sem saída do openssl]")
        if not chain_ok:
            print()
            print("[RESULTADO] INVÁLIDO")
            print("Motivo: cadeia do certificado inválida.")
            return 3
        print("[OK] Cadeia válida.")
    else:
        print("[5/6] Validação de cadeia não solicitada.")

    print("[6/6] Consultando registro de clonagem...")
    clone_suspected, record = update_clone_registry(
        registry_path=registry_path,
        gtin=info["gtin"],
        serial=info["serial"],
        lot=info["lot"],
    )

    print()
    if clone_suspected:
        print("[RESULTADO] ASSINATURA VÁLIDA, MAS HÁ SUSPEITA DE CLONAGEM")
        print("Motivo: GTIN|SERIAL já havia sido visto anteriormente.")
    else:
        print("[RESULTADO] VÁLIDO")
        print("Motivo: assinatura válida e primeira ocorrência desse GTIN|SERIAL.")

    print()
    print("Resumo final:")
    print(f"  HRI reconstruído : {build_hri(info)[:220]}{'...' if len(build_hri(info)) > 220 else ''}")
    print(f"  Registro         : {record}")

    return 0 if not clone_suspected else 10


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        raise SystemExit(1)
