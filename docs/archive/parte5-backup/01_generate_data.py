#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import re
import secrets
import string
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path

# GS (Group Separator) usado em GS1 quando um campo de tamanho variável
# não é o último. Em muitos fluxos ele representa o FNC1 de separação.
GS = chr(29)

SERIAL_ALPHABET = string.ascii_uppercase + string.digits
LOT_ALPHABET = string.ascii_uppercase + string.digits + "-._/"


@dataclass
class MedicineData:
    gtin: str
    expiration: str               # YYYY-MM-DD
    expiration_gs1: str           # YYMMDD
    lot: str
    serial: str

    ai_01: str
    ai_17: str
    ai_10: str
    ai_21: str

    gs1_base_raw: str             # contém GS real
    gs1_base_visible: str         # mostra <GS> para debug humano
    gs1_hri: str                  # formato legível
    separator_after_lot: bool


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def validate_gtin(gtin: str) -> str:
    gtin = gtin.strip()
    if not re.fullmatch(r"\d{14}", gtin):
        raise ValueError("GTIN deve conter exatamente 14 dígitos.")
    return gtin


def validate_serial(serial: str) -> str:
    serial = serial.strip().upper()
    if not (1 <= len(serial) <= 20):
        raise ValueError("SERIAL deve ter entre 1 e 20 caracteres.")
    if not re.fullmatch(r"[A-Z0-9\-\._/]+", serial):
        raise ValueError("SERIAL contém caracteres inválidos. Use apenas A-Z, 0-9, -, ., _, /")
    return serial


def validate_lot(lot: str) -> str:
    lot = lot.strip().upper()
    if not (1 <= len(lot) <= 20):
        raise ValueError("LOT deve ter entre 1 e 20 caracteres.")
    if not re.fullmatch(r"[A-Z0-9\-\._/]+", lot):
        raise ValueError("LOT contém caracteres inválidos. Use apenas A-Z, 0-9, -, ., _, /")
    return lot


def validate_expiration(exp: str) -> date:
    try:
        return datetime.strptime(exp.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("EXP deve estar no formato YYYY-MM-DD.") from exc


def to_gs1_date(expiration_date: date) -> str:
    return expiration_date.strftime("%y%m%d")


def generate_serial(length: int = 12) -> str:
    if not (1 <= length <= 20):
        raise ValueError("O comprimento do serial deve ficar entre 1 e 20.")
    return "".join(secrets.choice(SERIAL_ALPHABET) for _ in range(length))


def generate_lot(prefix: str = "L", digits: int = 6) -> str:
    if digits < 1:
        raise ValueError("LOT digits deve ser pelo menos 1.")
    return f"{prefix}{''.join(random.choice(string.digits) for _ in range(digits))}"


def generate_future_expiration(min_days: int = 365, max_days: int = 900) -> date:
    if min_days < 1 or max_days < min_days:
        raise ValueError("Faixa de validade futura inválida.")
    return date.today() + timedelta(days=random.randint(min_days, max_days))


def build_gs1(gtin: str, expiration_date: date, lot: str, serial: str) -> tuple[str, str, str]:
    """
    Ordem adotada:
      (01) GTIN        -> fixo 14
      (17) validade    -> fixo 6
      (10) lote        -> variável
      GS separador
      (21) serial      -> variável

    Isso evita ambiguidade no parser.
    """
    exp_gs1 = to_gs1_date(expiration_date)

    ai_01 = f"01{gtin}"
    ai_17 = f"17{exp_gs1}"
    ai_10 = f"10{lot}"
    ai_21 = f"21{serial}"

    gs1_base_raw = ai_01 + ai_17 + ai_10 + GS + ai_21
    gs1_base_visible = ai_01 + ai_17 + ai_10 + "<GS>" + ai_21
    gs1_hri = f"(01){gtin}(17){exp_gs1}(10){lot}(21){serial}"

    return gs1_base_raw, gs1_base_visible, gs1_hri


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera dados GS1 do medicamento para PKI + HSM + DataMatrix."
    )

    parser.add_argument(
        "--gtin",
        help="GTIN com 14 dígitos. Ex.: 05412345000013",
        default="05412345000013",
    )
    parser.add_argument(
        "--serial",
        help="Serial do medicamento. Máx. 20 caracteres",
    )
    parser.add_argument(
        "--lot",
        help="Lote do medicamento. Máx. 20 caracteres",
    )
    parser.add_argument(
        "--exp",
        help="Validade no formato YYYY-MM-DD",
    )

    parser.add_argument(
        "--serial-len",
        type=int,
        default=12,
        help="Tamanho do serial aleatório quando --serial não for informado. Padrão: 12",
    )
    parser.add_argument(
        "--lot-prefix",
        default="L",
        help="Prefixo do lote aleatório quando --lot não for informado. Padrão: L",
    )
    parser.add_argument(
        "--lot-digits",
        type=int,
        default=6,
        help="Quantidade de dígitos do lote aleatório quando --lot não for informado. Padrão: 6",
    )
    parser.add_argument(
        "--exp-min-days",
        type=int,
        default=365,
        help="Mínimo de dias futuros para validade automática. Padrão: 365",
    )
    parser.add_argument(
        "--exp-max-days",
        type=int,
        default=900,
        help="Máximo de dias futuros para validade automática. Padrão: 900",
    )
    parser.add_argument(
        "--outdir",
        default="data",
        help="Diretório de saída. Padrão: data",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = Path.cwd() / outdir
    ensure_dir(outdir)

    gtin = validate_gtin(args.gtin)
    serial = validate_serial(args.serial) if args.serial else generate_serial(args.serial_len)
    lot = validate_lot(args.lot) if args.lot else validate_lot(generate_lot(args.lot_prefix, args.lot_digits))
    expiration_date = (
        validate_expiration(args.exp)
        if args.exp
        else generate_future_expiration(args.exp_min_days, args.exp_max_days)
    )

    exp_gs1 = to_gs1_date(expiration_date)

    gs1_base_raw, gs1_base_visible, gs1_hri = build_gs1(
        gtin=gtin,
        expiration_date=expiration_date,
        lot=lot,
        serial=serial,
    )

    medicine = MedicineData(
        gtin=gtin,
        expiration=expiration_date.isoformat(),
        expiration_gs1=exp_gs1,
        lot=lot,
        serial=serial,
        ai_01=f"01{gtin}",
        ai_17=f"17{exp_gs1}",
        ai_10=f"10{lot}",
        ai_21=f"21{serial}",
        gs1_base_raw=gs1_base_raw,
        gs1_base_visible=gs1_base_visible,
        gs1_hri=gs1_hri,
        separator_after_lot=True,
    )

    medicine_json = outdir / "medicine.json"
    gs1_base_txt = outdir / "gs1_base.txt"
    gs1_hri_txt = outdir / "gs1_hri.txt"

    medicine_json.write_text(
        json.dumps(asdict(medicine), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    gs1_base_txt.write_text(medicine.gs1_base_raw + "\n", encoding="utf-8")
    gs1_hri_txt.write_text(medicine.gs1_hri + "\n", encoding="utf-8")

    print("[OK] Dados do medicamento gerados com sucesso.")
    print(f"[OK] JSON     -> {medicine_json}")
    print(f"[OK] GS1 RAW  -> {gs1_base_txt}")
    print(f"[OK] GS1 HRI  -> {gs1_hri_txt}")
    print()
    print("Resumo:")
    print(f"  GTIN             : {medicine.gtin}")
    print(f"  VALIDADE         : {medicine.expiration}  (GS1: {medicine.expiration_gs1})")
    print(f"  LOTE             : {medicine.lot}")
    print(f"  SERIAL           : {medicine.serial}")
    print(f"  GS1 RAW visível  : {medicine.gs1_base_visible}")
    print(f"  GS1 HRI          : {medicine.gs1_hri}")
    print()
    print("Obs.: o arquivo data/gs1_base.txt contém o caractere GS real (ASCII 29)")
    print("entre (10) LOT e (21) SERIAL.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
