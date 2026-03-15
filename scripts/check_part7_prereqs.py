#!/usr/bin/env python3
from pathlib import Path
import json

GS = b"\x1d"

payload = Path("data/payload.txt").read_bytes().rstrip(b"\n")
base = Path("data/gs1_base.txt").read_bytes().rstrip(b"\n")
kid = Path("data/kid.txt").read_text(encoding="utf-8").strip()
cert_map = json.loads(Path("config/cert_map.json").read_text(encoding="utf-8"))
registry = json.loads(Path("registry/seen_serials.json").read_text(encoding="utf-8"))

parts = payload.split(GS)
rebuilt = parts[0] + GS + parts[1] if len(parts) >= 2 else b""

print("payload_len:", len(payload))
print("gs_count:", payload.count(GS))
print("parts:", len(parts))
print("starts_with_01:", payload.startswith(b"01"))
print("has_92:", b"\x1d92" in payload)
print("has_91:", b"\x1d91" in payload)
print("kid_len:", len(kid))
print("kid_in_map:", kid in cert_map)
print("rebuilt_equals_base:", rebuilt == base)
print("registry_is_dict:", isinstance(registry, dict))

assert payload.startswith(b"01"), "Payload não começa com AI 01"
assert payload.count(GS) == 3, "Quantidade inesperada de GS"
assert len(parts) == 4, "Payload deve ter 4 partes separadas por GS"
assert b"\x1d92" in payload, "AI 92 não encontrado"
assert b"\x1d91" in payload, "AI 91 não encontrado"
assert len(kid) == 16, "KID deve ter 16 caracteres"
assert kid in cert_map, "KID não encontrado no cert_map"
assert rebuilt == base, "Base reconstruída não bate com gs1_base"
assert isinstance(registry, dict), "Registro de clonagem inválido"

print("OK: pré-requisitos da Parte 7 validados.")
