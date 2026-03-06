import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="Fluxo de Caixa CFO", layout="wide")

ARQUIVO = "fluxo_caixa.xlsx"

# =====================================================
# CRIAR BASE CASO NÃO EXISTA
# =====================================================

if not os.path.exists(ARQUIVO):

    df_base = pd.DataFrame(columns=[
        "data_lancamento",
        "data_vencimento",
        "tipo",
        "categoria",
        "subcategoria",
        "descricao",
        "valor",
        "status"
    ])

    df_base.to_excel(ARQUIVO, index=False)

# =====================================================
# CARREGAR BASE
# =====================================================

df = pd.read_excel(ARQUIVO)

colunas = [
"data_lancamento",
"data_vencimento",
"type",
"categoria",
"subcategoria",
"descricao",
"valor",
"status"
]

for c in colunas:
    if c not in df.columns:
        df[c] = None

df = df[colunas]

df["data_lancamento"] = pd.to_datetime(df["data_lancamento"], errors="coerce")
df["data_vencimento"] = pd.to_datetime(df["data_vencimento"], errors="coerce")
df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

# =====================================================
# ESTRUTURA FINANCEIRA
# =====================================================

entradas = [
"Comissões",
"Outras Entradas"
]

saidas = {

"Pessoal":[
"Folha CLT",
"Folha PJ",
"Outras Pessoal",
"Bonus/Dividendos"
],

"Administrativas":[
"Aluguel",
"Condomínio e IPTU",
"Conselho",
"Materiais e Limpeza",
"Vagas Garagem sócios",
"Viagem e Hospedagem",
"Manutenções",
"Desp. De representação",
"Outras adm"
],

"Serv. Terceiro":[
"Contabilidade/Juridico",
"Tecnologia",
"Outros"
],

"Marketing":[
"Eventos",
"Marketing",
"Patrocínio"
],

"Outras":[
"Ativo Fixo",
"Financeiras",
"Parcelamentos",
"Impostos"
]

}

st.title("💰 Sistema Inteligente de Fluxo de Caixa")

# =====================================================
# TABS (SUBSTITUI O MENU)
# =====================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
"Dashboard",
"Novo Lançamento",
"Fluxo de Caixa",
"DRE",
"Previsão Caixa"
])

# =====================================================
# DASHBOARD
# =====================================================

with tab1:

    if len(df) == 0:

        st.info("Nenhum dado cadastrado.")

    else:

        df["valor_real"] = df.apply(
            lambda x: x["valor"] if x["tipo"]=="Entrada" else -x["valor"],
            axis=1
        )

        saldo = df["valor_real"].sum()
        receitas = df[df["tipo"]=="Entrada"]["valor"].sum()
        despesas = df[df["tipo"]=="Saída"]["valor"].sum()

        col1,col2,col3 = st.columns(3)

        col1.metric("Saldo Atual", f"R$ {saldo:,.2f}")
        col2.metric("Entradas", f"R$ {receitas:,.2f}")
        col3.metric("Saídas", f"R$ {despesas:,.2f}")

        st.subheader("Despesas por Categoria")

        despesas_cat = df[df["tipo"]=="Saída"].groupby("categoria")["valor"].sum().reset_index()

        if len(despesas_cat) > 0:

            graf = alt.Chart(despesas_cat).mark_bar().encode(
                x="categoria",
                y="valor"
            )

            st.altair_chart(graf, use_container_width=True)

# =====================================================
# NOVO LANÇAMENTO
# =====================================================

with tab2:

    st.subheader("Cadastrar lançamento")

    tipo = st.selectbox("Tipo",["Entrada","Saída"])

    data_lanc = st.date_input("Data lançamento")
    data_venc = st.date_input("Data vencimento")

    if tipo == "Entrada":

        categoria = "Entradas"

        subcategoria = st.selectbox(
        "Subcategoria",
        entradas
        )

    if tipo == "Saída":

        categoria = st.selectbox(
        "Categoria",
        list(saidas.keys())
        )

        subcategoria = st.selectbox(
        "Subcategoria",
        saidas[categoria]
        )

    descricao = st.text_input("Descrição")

    valor = st.number_input("Valor", min_value=0.0)

    status = st.selectbox("Status",["Pendente","Pago"])

    if st.button("Salvar"):

        novo = pd.DataFrame([{

            "data_lancamento":data_lanc,
            "data_vencimento":data_venc,
            "tipo":tipo,
            "categoria":categoria,
            "subcategoria":subcategoria,
            "descricao":descricao,
            "valor":valor,
            "status":status

        }])

        df = pd.concat([df,novo], ignore_index=True)

        df.to_excel(ARQUIVO,index=False)

        st.success("Lançamento salvo!")

# =====================================================
# FLUXO DE CAIXA
# =====================================================

with tab3:

    st.subheader("Fluxo financeiro")

    if len(df) == 0:

        st.warning("Sem dados")

    else:

        df["mes"] = df["data_lancamento"].dt.to_period("M")

        mes = st.selectbox(
        "Filtrar mês",
        sorted(df["mes"].astype(str).unique())
        )

        filtrado = df[df["mes"].astype(str)==mes]

        st.dataframe(filtrado, use_container_width=True)

# =====================================================
# DRE
# =====================================================

with tab4:

    st.subheader("Demonstrativo de Resultado")

    receitas = df[df["tipo"]=="Entrada"]["valor"].sum()
    despesas = df[df["tipo"]=="Saída"]["valor"].sum()

    resultado = receitas - despesas

    st.write("Receitas:", receitas)
    st.write("Despesas:", despesas)
    st.write("Resultado:", resultado)

# =====================================================
# PREVISÃO
# =====================================================

with tab5:

    st.subheader("Previsão de Caixa")

    if len(df) > 0:

        df["mes"] = df["data_vencimento"].dt.to_period("M")

        previsao = df.groupby(["mes","tipo"])["valor"].sum().unstack(fill_value=0)

        previsao["saldo"] = previsao.get("Entrada",0) - previsao.get("Saída",0)

        previsao["saldo_acumulado"] = previsao["saldo"].cumsum()

        previsao = previsao.reset_index()

        graf = alt.Chart(previsao).mark_line().encode(
            x="mes",
            y="saldo_acumulado"
        )

        st.altair_chart(graf, use_container_width=True)

        st.dataframe(previsao)

# =====================================================
# EXPORTAR
# =====================================================

st.sidebar.download_button(
"Baixar Excel",
df.to_csv(index=False).encode(),
"fluxo_caixa.csv"
)
