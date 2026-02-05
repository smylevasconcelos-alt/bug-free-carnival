import streamlit as st
from datetime import date
import pandas as pd
import psycopg2
from supabase import create_client

# =============================
# CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide"
)

# =============================
# ESTILO PREMIUM MOBILE
# =============================
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

# =============================
# SUPABASE CONFIG
# =============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =============================
# POSTGRES CONFIG
# =============================
def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"]
    )

# =============================
# INICIAR BANCO
# =============================
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id UUID PRIMARY KEY,
        name TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        user_id UUID,
        kind TEXT,
        amount NUMERIC,
        description TEXT,
        category TEXT,
        card TEXT,
        entry_date DATE
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# =============================
# PERFIL USUÁRIO
# =============================
def get_user_name(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM profiles WHERE id=%s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None


def save_user_name(user_id, name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO profiles (id, name)
        VALUES (%s,%s)
        ON CONFLICT (id)
        DO UPDATE SET name = EXCLUDED.name
    """, (user_id, name))
    conn.commit()
    cur.close()
    conn.close()

# =============================
# TRANSAÇÕES
# =============================
def load_transactions(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, kind, amount, description, category, card, entry_date
        FROM transactions
        WHERE user_id=%s
        ORDER BY entry_date DESC
    """, (user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{
        "id": r[0],
        "kind": r[1],
        "amount": float(r[2]),
        "description": r[3],
        "category": r[4],
        "card": r[5],
        "entry_date": str(r[6])
    } for r in rows]


def add_transaction(user_id, item):
    conn = get_connection()
    cur = conn.cursor()

    amount_value = float(str(item["amount"]).replace(",", "."))

    cur.execute("""
        INSERT INTO transactions (user_id, kind, amount, description, category, card, entry_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        user_id,
        item["kind"],
        amount_value,
        item["description"],
        item["category"],
        item["card"],
        item["entry_date"]
    ))

    conn.commit()
    cur.close()
    conn.close()


def delete_transaction(transaction_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id=%s", (transaction_id,))
    conn.commit()
    cur.close()
    conn.close()

# =============================
# SESSÃO
# =============================
if "user" not in st.session_state:
    st.session_state["user"] = None

# =============================
# LOGIN + CADASTRO
# =============================
if st.session_state["user"] is None:

    st.title("🔐 Controle Financeiro")

    tab1, tab2 = st.tabs(["➡️ Entrar", "🆕 Criar Conta"])

    # LOGIN
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state["user"] = res.user
                st.success("Login feito ✅")
                st.rerun()
            except:
                st.error("Senha ou email incorretos ❌")

    # CADASTRO
    with tab2:
        name = st.text_input("Seu nome completo")
        new_email = st.text_input("Novo Email")
        new_password = st.text_input("Nova Senha", type="password")

        if st.button("Criar Conta"):
            try:
                res = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password
                })

                user_id = res.user.id
                save_user_name(user_id, name)

                st.success("Conta criada 🎉 Agora faça login!")
            except Exception as e:
                st.error("Erro ao cadastrar ❌")

    st.stop()

# =============================
# USUÁRIO LOGADO
# =============================
user_id = st.session_state["user"].id
user_name = get_user_name(user_id)

# LOGOUT
if st.sidebar.button("🚪 Sair"):
    st.session_state["user"] = None
    st.rerun()

# =============================
# HEADER
# =============================
st.title(f"💰 Bem-vindo, {user_name} 👋")

transactions = load_transactions(user_id)

# =============================
# ABAS DO APP
# =============================
tab_add, tab_list, tab_dash = st.tabs(
    ["➕ Adicionar", "📋 Transações", "📊 Dashboard"]
)

# =============================
# ADICIONAR
# =============================
with tab_add:
    st.subheader("➕ Nova Transação")

    kind = st.selectbox("Tipo", ["receita", "despesa"])
    amount = st.text_input("Valor (ex: 8,00)")
    description = st.text_input("Descrição")
    category = st.text_input("Categoria", value="outros")
    card = st.selectbox("Cartão", ["Nubank", "Inter", "Itaú", "Dinheiro", "Outro"])
    entry_date = st.date_input("Data", value=date.today())

    if st.button("💾 Salvar"):
        try:
            add_transaction(user_id, {
                "kind": kind,
                "amount": amount,
                "description": description,
                "category": category,
                "card": card,
                "entry_date": entry_date
            })
            st.success("Transação salva ✅")
            st.rerun()
        except:
            st.error("Digite um valor válido, ex: 10,50")

# =============================
# LISTAR + APAGAR
# =============================
with tab_list:
    st.subheader("📋 Histórico")

    if not transactions:
        st.info("Nenhuma transação encontrada.")
    else:
        df = pd.DataFrame(transactions)

        st.dataframe(df.drop(columns=["id"]), width="stretch")

        st.divider()
        st.subheader("🗑️ Apagar")

        selected_id = st.selectbox("Selecione:", df["id"].tolist())

        if st.button("❌ Apagar"):
            delete_transaction(selected_id)
            st.success("Apagado ✅")
            st.rerun()

# =============================
# DASHBOARD
# =============================
with tab_dash:
    st.subheader("📊 Resumo Mensal")

    if not transactions:
        st.info("Nada registrado ainda.")
    else:
        df = pd.DataFrame(transactions)
        months = sorted(df["entry_date"].str[:7].unique())

        selected_month = st.selectbox("Mês:", months)

        df_month = df[df["entry_date"].str.startswith(selected_month)]

        income = df_month[df_month["kind"] == "receita"]["amount"].sum()
        expenses = df_month[df_month["kind"] == "despesa"]["amount"].sum()
        balance = income - expenses

        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {income:.2f}")
        c2.metric("Despesas", f"R$ {expenses:.2f}")
        c3.metric("Saldo", f"R$ {balance:.2f}")
✅ AGORA MUITO IMPORTANTE
Depois de colar esse app.py, faça:

git add app.py
git commit -m "Login e cadastro Supabase final"
git push