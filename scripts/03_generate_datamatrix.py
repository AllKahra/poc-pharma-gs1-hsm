#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image
from pylibdmtx.pylibdmtx import encode, decode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera DataMatrix a partir do payload assinado."
    )
    parser.add_argument(
        "--payload",
        default="data/payload.txt",
        help="Arquivo de entrada com o payload bruto. Padrão: data/payload.txt",
    )
    parser.add_argument(
        "--out",
        default="dm/medicine.png",
        help="Arquivo PNG de saída. Padrão: dm/medicine.png",
    )
    parser.add_argument(
        "--decoded-out",
        default="dm/decoded_from_image.txt",
        help="Arquivo de saída do payload decodificado da imagem. Padrão: dm/decoded_from_image.txt",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    payload_path = Path(args.payload)
    out_path = Path(args.out)
    decoded_out_path = Path(args.decoded_out)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    decoded_out_path.parent.mkdir(parents=True, exist_ok=True)

    if not payload_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {payload_path}")

    payload = payload_path.read_bytes()
    if payload.endswith(b"\n"):
        payload = payload[:-1]

    print("[1/4] Gerando símbolo DataMatrix...")
    encoded = encode(payload)

    img = Image.frombytes("RGB", (encoded.width, encoded.height), encoded.pixels)
    img.save(out_path)

    print("[2/4] Reabrindo a imagem para validar decodificação...")
    img2 = Image.open(out_path)
    decoded_items = decode(img2)

    if not decoded_items:
        raise RuntimeError("Falha ao decodificar o DataMatrix gerado.")

    decoded = decoded_items[0].data
    decoded_out_path.write_bytes(decoded + b"\n")

    print("[3/4] Comparando payload original com payload decodificado...")
    if decoded != payload:
        raise RuntimeError("Payload decodificado difere do payload original.")

    print("[4/4] Concluído com sucesso.")
    print(f"[OK] Imagem gerada         -> {out_path}")
    print(f"[OK] Payload decodificado -> {decoded_out_path}")
    print(f"[OK] Tamanho payload      -> {len(payload)} bytes")
    print(f"[OK] Tem GS?              -> {b'\x1d' in payload}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
