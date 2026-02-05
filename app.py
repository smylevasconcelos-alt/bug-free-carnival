import streamlit as st
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import pandas as pd

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide"
)

# -----------------------------
# ESTILO PREMIUM
# -----------------------------
st.markdown("""
<style>
body {
    background-color: #f6f7fb;
}

.block-container {
    padding-top: 1.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

h1 {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.08);
    margin-bottom: 15px;
}

button {
    width: 100%;
    border-radius: 12px !important;
    font-size: 18px !important;
    padding: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOGIN
# -----------------------------
USER = "smyle"
PASSWORD = "1234"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.title("🔐 Login")

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if username == USER and password == PASSWORD:
            st.session_state["logged_in"] = True
            st.success("Bem-vindo, Smyle! ✅")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos ❌")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# -----------------------------
# LOGOUT
# -----------------------------
if st.sidebar.button("🚪 Sair"):
    st.session_state["logged_in"] = False
    st.rerun()

# -----------------------------
# DADOS
# -----------------------------
DATA_FILE = Path("data.json")

def load_transactions():
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def save_transactions(items):
    DATA_FILE.write_text(
        json.dumps(items, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

transactions = load_transactions()

# -----------------------------
# HEADER PRINCIPAL
# -----------------------------
st.title("💰 Controle Financeiro")
st.caption("Seu painel pessoal de receitas e despesas")

# -----------------------------
# ABAS
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["➕ Adicionar", "📋 Transações", "📊 Dashboard", "📤 Exportar"]
)

# -----------------------------
# ABA 1 - ADICIONAR
# -----------------------------
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("➕ Nova Transação")

    col1, col2 = st.columns(2)

    with col1:
        kind = st.selectbox("Tipo", ["receita", "despesa"])
        amount = st.text_input("Valor (ex: 120.50)")

    with col2:
        card = st.selectbox(
            "Cartão / Conta",
            ["Nubank", "Inter", "Itaú", "Dinheiro", "Outro"]
        )
        entry_date = st.date_input("Data", value=date.today())

    description = st.text_input("Descrição")
    category = st.text_input("Categoria", value="outros")

    if st.button("💾 Salvar"):
        new_item = {
            "kind": kind,
            "amount": str(amount),
            "description": description,
            "category": category,
            "card": card,
            "entry_date": entry_date.strftime("%Y-%m-%d")
        }
        transactions.append(new_item)
        save_transactions(transactions)
        st.success("Transação registrada! ✅")
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# ABA 2 - LISTAR + APAGAR + FILTRO
# -----------------------------
with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📋 Histórico de Transações")

    if not transactions:
        st.info("Nenhuma transação encontrada.")
    else:
        df = pd.DataFrame(transactions)

        # ✅ CORREÇÃO DEFINITIVA
        if "card" not in df.columns:
            df["card"] = "Sem cartão"

        filtro_cartao = st.selectbox(
            "Filtrar por cartão:",
            ["Todos"] + sorted(df["card"].fillna("Sem cartão").unique())
        )

        if filtro_cartao != "Todos":
            df = df[df["card"] == filtro_cartao]

        st.dataframe(df, use_container_width=True)

        st.divider()
        st.subheader("🗑️ Apagar transação")

        options = [
            f"{i+1} - {t['entry_date']} | {t['kind']} | "
            f"R$ {t['amount']} | {t['description']} "
            f"({t.get('card', 'Sem cartão')})"
            for i, t in enumerate(transactions)
        ]

        selected = st.selectbox("Selecione:", options)
        index_to_delete = options.index(selected)

        if st.button("❌ Apagar"):
            transactions.pop(index_to_delete)
            save_transactions(transactions)
            st.success("Transação apagada! ✅")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# ABA 3 - DASHBOARD + GRÁFICO
# -----------------------------
with tab3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📊 Resumo Mensal + Categoria")

    if transactions:
        df = pd.DataFrame(transactions)

        # ✅ CORREÇÃO DEFINITIVA
        if "card" not in df.columns:
            df["card"] = "Sem cartão"

        months = sorted(df["entry_date"].str[:7].unique())
        selected_month = st.selectbox("Mês:", months)

        df_month = df[df["entry_date"].str.startswith(selected_month)]

        income = df_month[df_month["kind"] == "receita"]["amount"].astype(float).sum()
        expenses = df_month[df_month["kind"] == "despesa"]["amount"].astype(float).sum()
        balance = income - expenses

        col1, col2, col3 = st.columns(3)
        col1.metric("Receitas", f"R$ {income:.2f}")
        col2.metric("Despesas", f"R$ {expenses:.2f}")
        col3.metric("Saldo", f"R$ {balance:.2f}")

        st.divider()
        st.subheader("📌 Gastos por Categoria")

        df_exp = df_month[df_month["kind"] == "despesa"]

        if not df_exp.empty:
            chart_data = df_exp.groupby("category")["amount"].apply(
                lambda x: x.astype(float).sum()
            )
            st.bar_chart(chart_data)
        else:
            st.info("Nenhuma despesa nesse mês.")

    else:
        st.info("Nenhuma transação registrada ainda.")

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# ABA 4 - EXPORTAR EXCEL
# -----------------------------
with tab4:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📤 Exportar Dados")

    if transactions:
        df = pd.DataFrame(transactions)

        # ✅ CORREÇÃO DEFINITIVA
        if "card" not in df.columns:
            df["card"] = "Sem cartão"

        excel_file = "transacoes.xlsx"
        df.to_excel(excel_file, index=False)

        with open(excel_file, "rb") as f:
            st.download_button(
                label="⬇️ Baixar Excel",
                data=f,
                file_name="transacoes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Nenhuma transação para exportar.")

    st.markdown("</div>", unsafe_allow_html=True)