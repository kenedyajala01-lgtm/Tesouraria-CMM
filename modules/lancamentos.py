"""Aba Lançamentos — formulário de entrada/saída e histórico filtrado."""
import datetime

import pandas as pd
import streamlit as st

from modules import gsheets as gs

CATEGORIAS = [
    "Mensalidade", "Eventos", "Esportes",
    "Fardamento/Materiais", "Manutenção", "Administrativo", "Outros",
]

# Mapa mês → número (1‑12), pré-computado uma vez no import
_MES_NUM = {mes: i + 1 for i, mes in enumerate(gs.MESES)}


def render() -> None:
    st.subheader("📝 Registrar Nova Transação")

    with st.form("form_lancamento", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            data = st.date_input("Data", datetime.date.today())
            tipo = st.selectbox("Tipo de Operação", ["Entrada", "Saída"])
        with c2:
            descricao = st.text_input(
                "Descrição", placeholder="Ex: Compra de troféus do torneio"
            )
            categoria = st.selectbox("Categoria", CATEGORIAS)
        with c3:
            valor = st.number_input(
                "Valor (R$)", min_value=0.01, step=10.0, format="%.2f", value=100.0
            )
            st.markdown("<br>", unsafe_allow_html=True)
            salvar = st.form_submit_button(
                "💾 Confirmar Lançamento", use_container_width=True
            )

    if salvar:
        if not descricao.strip():
            st.error("O campo **Descrição** é obrigatório.")
        else:
            gs.append_caixa(
                {
                    "Data":       data,
                    "Descrição":  descricao.strip(),
                    "Tipo":       tipo,
                    "Categoria":  categoria,
                    "Valor":      valor,
                }
            )
            icone = "📥" if tipo == "Entrada" else "📤"
            st.success(
                f"{icone} **{tipo}** de R$ {valor:,.2f} "
                f"({categoria}) registrada com sucesso!"
            )
            st.rerun()

    # ── Histórico com filtros ──────────────────────────────────────────
    st.divider()
    st.markdown("#### Histórico de Lançamentos")

    df = gs.load_caixa()

    if df.empty:
        st.info("Nenhum lançamento encontrado. Use o formulário acima para começar.")
        return

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        f_tipo = st.selectbox("Filtrar tipo", ["Todos", "Entrada", "Saída"])
    with fc2:
        f_cat = st.selectbox("Filtrar categoria", ["Todas"] + CATEGORIAS)
    with fc3:
        f_mes = st.selectbox("Filtrar mês", ["Todos"] + gs.MESES)

    df_f = df.copy()
    if f_tipo != "Todos":
        df_f = df_f[df_f["Tipo"] == f_tipo]
    if f_cat != "Todas":
        df_f = df_f[df_f["Categoria"] == f_cat]
    if f_mes != "Todos":
        # CORRIGIDO: pandas importado no topo; lookup via dict em vez de .index()
        df_f = df_f[
            pd.to_datetime(df_f["Data"], errors="coerce").dt.month == _MES_NUM[f_mes]
        ]

    df_f = df_f.sort_values("Data", ascending=False).copy()

    t_ent = df_f[df_f["Tipo"] == "Entrada"]["Valor"].sum()
    t_sai = df_f[df_f["Tipo"] == "Saída"]["Valor"].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Entradas (filtro)", f"R$ {t_ent:,.2f}")
    m2.metric("Saídas (filtro)",   f"R$ {t_sai:,.2f}")
    m3.metric("Saldo (filtro)",    f"R$ {t_ent - t_sai:,.2f}")

    df_disp = df_f.copy()
    df_disp["Valor"] = df_disp["Valor"].apply(lambda v: f"R$ {v:,.2f}")
    st.dataframe(df_disp, use_container_width=True, hide_index=True)
