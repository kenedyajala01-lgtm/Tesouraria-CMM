"""Aba Dashboard — visão geral do caixa e indicadores do mês."""
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
    st.subheader("📊 Dashboard — Visão Geral")

    df = gs.load_caixa()

    if df.empty:
        st.info(
            "Nenhum lançamento ainda. Vá até **💸 Lançamentos** para registrar "
            "entradas e saídas."
        )
        _render_zeros()
        return

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)

    hoje      = date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year

    df_mes = df[
        (df["Data"].dt.month == mes_atual) & (df["Data"].dt.year == ano_atual)
    ]

    total_ent  = df[df["Tipo"] == "Entrada"]["Valor"].sum()
    total_sai  = df[df["Tipo"] == "Saída"]["Valor"].sum()
    saldo_geral = total_ent - total_sai

    ent_mes = df_mes[df_mes["Tipo"] == "Entrada"]["Valor"].sum()
    sai_mes = df_mes[df_mes["Tipo"] == "Saída"]["Valor"].sum()
    sal_mes = ent_mes - sai_mes

    # ── KPIs ──────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Saldo Geral",             f"R$ {saldo_geral:,.2f}")
    k2.metric(f"📥 Entradas — {gs.MESES[mes_atual-1]}", f"R$ {ent_mes:,.2f}")
    k3.metric(f"📤 Saídas — {gs.MESES[mes_atual-1]}",   f"R$ {sai_mes:,.2f}")
    k4.metric(f"📊 Saldo do Mês",           f"R$ {sal_mes:,.2f}",
              delta=f"R$ {sal_mes:,.2f}", delta_color="normal")

    reservado = gs.saldo_total_reservado()
    if reservado > 0:
        st.caption(
            f"🏦 **R$ {reservado:,.2f}** está separado em reservas/metas de poupança "
            f"— saldo livre para uso imediato: **R$ {saldo_geral - reservado:,.2f}**. "
            f"Veja em **💰 Reservas & Poupança**."
        )

    st.divider()

    col_graf, col_cat = st.columns([3, 2])

    # ── Gráfico mensal ─────────────────────────────────────────────────
    with col_graf:
        st.markdown("#### Fluxo Mensal (ano atual)")
        df_ano = df[df["Data"].dt.year == ano_atual].copy()
        df_ano["Mês"] = df_ano["Data"].dt.month

        resumo = (
            df_ano.groupby(["Mês", "Tipo"])["Valor"]
            .sum()
            .unstack(fill_value=0)
            .reindex(range(1, 13), fill_value=0)
        )
        meses_label = [m[:3] for m in gs.MESES]

        fig = go.Figure()
        if "Entrada" in resumo.columns:
            fig.add_bar(
                x=meses_label, y=resumo["Entrada"],
                name="Entradas", marker_color="#27AE60",
            )
        if "Saída" in resumo.columns:
            fig.add_bar(
                x=meses_label, y=resumo["Saída"],
                name="Saídas", marker_color="#E74C3C",
            )
        fig.update_layout(**_LAYOUT, barmode="group",
                          legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)

    # ── Pizza por categoria ────────────────────────────────────────────
    with col_cat:
        st.markdown("#### Saídas por Categoria")
        saidas = df[df["Tipo"] == "Saída"]
        if saidas.empty:
            st.info("Nenhuma saída registrada ainda.")
        else:
            por_cat = saidas.groupby("Categoria")["Valor"].sum().reset_index()
            fig2 = go.Figure(go.Pie(
                labels=por_cat["Categoria"],
                values=por_cat["Valor"],
                hole=0.45,
                marker=dict(colors=[
                    "#C9A84C","#E74C3C","#3498DB","#27AE60",
                    "#9B59B6","#E67E22","#1ABC9C",
                ]),
            ))
            fig2.update_layout(**_LAYOUT, showlegend=True,
                               legend=dict(orientation="v", x=1.02))
            st.plotly_chart(fig2, use_container_width=True)

    # ── Últimos lançamentos ────────────────────────────────────────────
    st.markdown("#### Últimos 10 Lançamentos")
    ultimos = df.sort_values("Data", ascending=False).head(10).copy()
    ultimos["Valor"] = ultimos["Valor"].apply(lambda v: f"R$ {v:,.2f}")
    ultimos["Data"]  = ultimos["Data"].dt.strftime("%d/%m/%Y")
    st.dataframe(ultimos, use_container_width=True, hide_index=True)


def _render_zeros() -> None:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Saldo Geral",    "R$ 0,00")
    k2.metric("📥 Entradas",       "R$ 0,00")
    k3.metric("📤 Saídas",         "R$ 0,00")
    k4.metric("📊 Saldo do Mês",   "R$ 0,00")
