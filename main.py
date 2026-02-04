#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable

DATA_FILE = Path("data.json")
DATE_FORMAT = "%Y-%m-%d"


@dataclass(frozen=True)
class Transaction:
    kind: str
    amount: Decimal
    description: str
    category: str
    entry_date: date

    def to_dict(self) -> dict:
        data = asdict(self)
        data["amount"] = str(self.amount)
        data["entry_date"] = self.entry_date.strftime(DATE_FORMAT)
        return data

    @staticmethod
    def from_dict(data: dict) -> "Transaction":
        return Transaction(
            kind=data["kind"],
            amount=Decimal(data["amount"]),
            description=data["description"],
            category=data.get("category", "outros"),
            entry_date=datetime.strptime(data["entry_date"], DATE_FORMAT).date(),
        )


def load_transactions(path: Path) -> list[Transaction]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Transaction.from_dict(item) for item in data]


def save_transactions(path: Path, items: Iterable[Transaction]) -> None:
    payload = [item.to_dict() for item in items]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_amount(value: str) -> Decimal:
    normalized = value.replace(",", ".")
    return Decimal(normalized)


def parse_date(value: str | None) -> date:
    if value:
        return datetime.strptime(value, DATE_FORMAT).date()
    return date.today()


def add_transaction(args: argparse.Namespace) -> None:
    transactions = load_transactions(DATA_FILE)
    transaction = Transaction(
        kind=args.kind,
        amount=parse_amount(args.amount),
        description=args.description,
        category=args.category,
        entry_date=parse_date(args.date),
    )
    transactions.append(transaction)
    save_transactions(DATA_FILE, transactions)
    print("Transação registrada com sucesso!")


def list_transactions(args: argparse.Namespace) -> None:
    transactions = load_transactions(DATA_FILE)
    if args.kind:
        transactions = [item for item in transactions if item.kind == args.kind]
    if args.category:
        transactions = [item for item in transactions if item.category == args.category]
    if not transactions:
        print("Nenhuma transação encontrada.")
        return
    for item in sorted(transactions, key=lambda x: x.entry_date):
        print(
            f"{item.entry_date.strftime(DATE_FORMAT)} | {item.kind.upper():8} | "
            f"R$ {item.amount:.2f} | {item.category} | {item.description}"
        )


def summary(_: argparse.Namespace) -> None:
    transactions = load_transactions(DATA_FILE)
    income = sum((item.amount for item in transactions if item.kind == "receita"), Decimal("0"))
    expenses = sum((item.amount for item in transactions if item.kind == "despesa"), Decimal("0"))
    balance = income - expenses
    print("Resumo financeiro")
    print(f"Receitas:  R$ {income:.2f}")
    print(f"Despesas:  R$ {expenses:.2f}")
    print(f"Saldo:     R$ {balance:.2f}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gerenciador financeiro simples para receitas e despesas."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("adicionar", help="Adicionar receita ou despesa")
    add_parser.add_argument("kind", choices=["receita", "despesa"], help="Tipo da transação")
    add_parser.add_argument("amount", help="Valor da transação, ex: 120.50")
    add_parser.add_argument("description", help="Descrição breve")
    add_parser.add_argument("--category", default="outros", help="Categoria da transação")
    add_parser.add_argument("--date", help="Data no formato YYYY-MM-DD (padrão: hoje)")
    add_parser.set_defaults(func=add_transaction)

    list_parser = subparsers.add_parser("listar", help="Listar transações")
    list_parser.add_argument("--kind", choices=["receita", "despesa"], help="Filtrar por tipo")
    list_parser.add_argument("--category", help="Filtrar por categoria")
    list_parser.set_defaults(func=list_transactions)

    summary_parser = subparsers.add_parser("resumo", help="Mostrar resumo financeiro")
    summary_parser.set_defaults(func=summary)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
