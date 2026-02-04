# Gerenciador Financeiro (CLI)

Um programa simples em Python para registrar receitas e despesas, com armazenamento em arquivo `data.json`.

## Requisitos

- Python 3.10+

## Uso

```bash
python main.py adicionar receita 2500.00 "Salário" --category trabalho
python main.py adicionar despesa 120.50 "Mercado" --category alimentacao --date 2024-05-01
python main.py listar
python main.py listar --kind despesa
python main.py resumo
```

## Estrutura de dados

As transações são salvas no arquivo `data.json` no mesmo diretório do programa, no seguinte formato:

```json
[
  {
    "kind": "receita",
    "amount": "2500.00",
    "description": "Salário",
    "category": "trabalho",
    "entry_date": "2024-05-05"
  }
]
```
