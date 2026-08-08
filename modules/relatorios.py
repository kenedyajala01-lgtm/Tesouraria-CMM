"""Aba Relatórios — resumo anual de mensalidades e fluxo de caixa."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules import gsheets as gs

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#EEF2F7",
    margin=dict(t=24, b=40, l=8, r=8),
)


def render() -> None:
    st.subheader("📋 Relatórios")

    tab_caixa, tab_socios = st.tabs(["💰 Fluxo de Caixa", "👥 Adimplência de Sócios"])

    with tab_caixa:
        _relatorio_caixa()

    with tab_socios:
        _relatorio_socios()


# ─────────────────────────────────────────────────────────────────────────────

def _relatorio_caixa() -> None:
    st.markdown("#### Resumo Anual do Caixa")

    df = gs.load_caixa()
    if df.empty:
        st.info("Nenhum lançamento registrado.")
        return

    df["Data"]  = pd.to_datetime(df["Data"], errors="coerce")
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)

    ano_sel = st.selectbox(
        "Ano", sorted(df["Data"].dt.year.dropna().unique().astype(int), reverse=True),
        key="rel_ano_caixa",
    )

    df_ano = df[df["Data"].dt.year == ano_sel].copy()
    df_ano["Mês"] = df_ano["Data"].dt.month

    resumo = (
        df_ano.groupby(["Mês", "Tipo"])["Valor"]
        .sum()
        .unstack(fill_value=0)
        .reindex(range(1, 13), fill_value=0)
    )

    total_ent = resumo.get("Entrada", pd.Series([0]*12)).sum()
    total_sai = resumo.get("Saída",   pd.Series([0]*12)).sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Entradas", f"R$ {total_ent:,.2f}")
    c2.metric("Total Saídas",   f"R$ {total_sai:,.2f}")
    c3.metric("Resultado",      f"R$ {total_ent - total_sai:,.2f}")

    meses_label = [m[:3] for m in gs.MESES]
    fig = go.Figure()
    if "Entrada" in resumo.columns:
        fig.add_bar(x=meses_label, y=resumo["Entrada"],
                    name="Entradas", marker_color="#27AE60")
    if "Saída" in resumo.columns:
        fig.add_bar(x=meses_label, y=resumo["Saída"],
                    name="Saídas", marker_color="#E74C3C")

    saldo_acum = (
        resumo.get("Entrada", 0) - resumo.get("Saída", 0)
    ).cumsum()
    fig.add_trace(go.Scatter(
        x=meses_label, y=saldo_acum, mode="lines+markers",
        name="Saldo Acumulado",
        line=dict(color="#C9A84C", width=2, dash="dot"),
    ))
    fig.update_layout(**_LAYOUT, barmode="group",
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)

    # Tabela mensal
    tabela = pd.DataFrame({
        "Mês":      gs.MESES,
        "Entradas": resumo.get("Entrada", [0]*12).values,
        "Saídas":   resumo.get("Saída",   [0]*12).values,
    })
    tabela["Resultado"] = tabela["Entradas"] - tabela["Saídas"]
    for col in ["Entradas", "Saídas", "Resultado"]:
        tabela[col] = tabela[col].apply(lambda v: f"R$ {v:,.2f}")
    st.dataframe(tabela, use_container_width=True, hide_index=True)


def _relatorio_socios() -> None:
    st.markdown("#### Adimplência Anual por Sócio")

    df = gs.load_socios()
    if df.empty:
        st.info("Nenhum sócio cadastrado.")
        return

    meses_disp = [m for m in gs.MESES if m in df.columns]
    if not meses_disp:
        st.warning("Nenhuma coluna de mês encontrada na planilha de sócios.")
        return

    def _contar(row: pd.Series, status: str) -> int:
        return sum(
            1 for m in meses_disp
            if str(row.get(m, "")).strip().lower() == status.lower()
        )

    df["Meses Pagos"]    = df.apply(lambda r: _contar(r, "Pago"),    axis=1)
    df["Meses Devendo"]  = df.apply(lambda r: _contar(r, "Pendente"),axis=1)
    df["% Adimplência"]  = (df["Meses Pagos"] / len(meses_disp) * 100).round(1)

    total_socios   = len(df)
    adimplentes    = int((df["Meses Devendo"] == 0).sum())
    inadimplentes  = total_socios - adimplentes

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Sócios",  total_socios)
    c2.metric("✅ Adimplentes",    adimplentes)
    c3.metric("⚠️ Inadimplentes", inadimplentes)

    cols_exib = ["Nome", "Meses Pagos", "Meses Devendo", "% Adimplência"]
    st.dataframe(
        df[cols_exib].sort_values("Meses Devendo", ascending=False),
        use_container_width=True, hide_index=True,
    )
