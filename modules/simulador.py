"""Aba Simulador de Eventos — Ponto de Equilíbrio (Break-even)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#EEF2F7",
    margin=dict(t=24, b=56, l=8, r=8),
)

# Limite máximo de participantes no eixo X do gráfico.
# Sem isso, valores de ingresso próximos ao custo variável geram arrays imensos.
_X_MAX_CAP = 5_000


def render() -> None:
    st.subheader("🧮 Simulador de Ponto de Equilíbrio")
    st.caption(
        "Calcule quantos participantes são necessários para cobrir todos os custos "
        "e garantir que o evento não feche no vermelho."
    )

    # ── Inputs ────────────────────────────────────────────────────────
    st.markdown("#### Parâmetros do Evento")
    c1, c2, c3 = st.columns(3)
    with c1:
        nome_evento = st.text_input("Nome do evento", "Jantar de Confraternização")
        custo_fixo  = st.number_input(
            "Custo Fixo Total (R$)", min_value=0.0, value=3000.0, step=500.0,
            format="%.2f",
            help="Local, DJ, decoração, segurança — custo existente independente do público.",
        )
    with c2:
        custo_variavel = st.number_input(
            "Custo Variável por Pessoa (R$)", min_value=0.0, value=45.0, step=5.0,
            format="%.2f",
            help="Alimentação, bebida, brinde — custo que cresce com cada participante.",
        )
        meta_lucro = st.number_input(
            "Meta de Lucro Desejada (R$)", min_value=0.0, value=500.0, step=100.0,
            format="%.2f",
            help="Quanto você quer lucrar além de cobrir os custos.",
        )
    with c3:
        valor_ingresso = st.number_input(
            "Valor do Ingresso (R$)", min_value=0.01, value=120.0, step=10.0,
            format="%.2f",
        )
        capacidade_max = st.number_input(
            "Capacidade Máxima do Local", min_value=1, value=200, step=10,
        )

    margem = valor_ingresso - custo_variavel

    st.divider()

    # ── Validação ─────────────────────────────────────────────────────
    if margem <= 0:
        st.error(
            f"⛔ **Inviável:** O valor do ingresso (R$ {valor_ingresso:,.2f}) "
            f"é menor ou igual ao custo variável por pessoa (R$ {custo_variavel:,.2f}). "
            "Cada participante geraria prejuízo adicional."
        )
        return

    # ── Cálculos ──────────────────────────────────────────────────────
    pe_pessoas  = custo_fixo / margem
    pe_receita  = pe_pessoas * valor_ingresso
    pe_meta     = (custo_fixo + meta_lucro) / margem
    pe_int      = int(np.ceil(pe_pessoas))
    pe_meta_int = int(np.ceil(pe_meta))
    viavel_cap  = pe_int <= capacidade_max

    # ── KPI Cards ─────────────────────────────────────────────────────
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("🎯 Break-even",          f"{pe_int} pessoas")
    r2.metric("💰 Receita no B.E.",     f"R$ {pe_receita:,.2f}")
    r3.metric("📊 Margem por Ingresso", f"R$ {margem:,.2f}")
    r4.metric(f"🏆 Meta (+R${meta_lucro:,.0f})", f"{pe_meta_int} pessoas")

    # ── Alerta Visual ─────────────────────────────────────────────────
    if not viavel_cap:
        alerta_cor   = "rgba(192,57,43,0.15)"
        alerta_borda = "#E74C3C"
        alerta_texto = (
            f"O evento pode ser <strong>inviável</strong>: o break-even exige "
            f"<strong>{pe_int} pessoas</strong>, mas o local comporta apenas "
            f"<strong>{capacidade_max}</strong>."
        )
        alerta_icone = "⛔"
    elif pe_meta_int > capacidade_max:
        alerta_cor   = "rgba(230,126,34,0.15)"
        alerta_borda = "#E67E22"
        alerta_texto = (
            f"O evento cobre os custos com {pe_int} participantes, mas para atingir "
            f"a meta de lucro precisaria de {pe_meta_int} — acima da capacidade máxima "
            f"({capacidade_max}). Considere ajustar o ingresso."
        )
        alerta_icone = "⚠️"
    else:
        alerta_cor   = "rgba(39,174,96,0.12)"
        alerta_borda = "#27AE60"
        lucro_max    = capacidade_max * margem - custo_fixo
        alerta_texto = (
            f"Com o local comportando <strong>{capacidade_max} pessoas</strong> e o "
            f"break-even em <strong>{pe_int}</strong>, o evento tem potencial de "
            f"lucro de até <strong>R$ {lucro_max:,.2f}</strong> com lotação máxima."
        )
        alerta_icone = "✅"

    st.markdown(
        f"""
        <div style="background:{alerta_cor};border:1px solid {alerta_borda};
                    border-radius:12px;padding:1rem 1.5rem;margin:0.5rem 0;">
            <p style="margin:0;font-size:1rem;line-height:1.6;">
                <strong style="font-size:1.4rem;">{alerta_icone} {nome_evento}</strong><br>
                {alerta_texto}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Gráfico Break-even ────────────────────────────────────────────
    st.markdown("#### Gráfico de Ponto de Equilíbrio")

    # CORRIGIDO: x_max tinha risco de gerar arrays muito grandes quando pe_meta
    # é alto (margem baixa). Aplicamos um cap explícito de _X_MAX_CAP.
    x_max   = min(max(int(pe_meta * 2), capacidade_max + 10), _X_MAX_CAP)
    pessoas = np.arange(0, x_max + 1)
    receita = pessoas * valor_ingresso
    custo   = custo_fixo + pessoas * custo_variavel
    lucro   = receita - custo

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=pessoas, y=custo, mode="lines",
        name="Custo Total", line=dict(color="#E74C3C", width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=pessoas, y=receita, mode="lines",
        name="Receita Total", line=dict(color="#2ECC71", width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=pessoas, y=lucro, mode="lines",
        name="Lucro / Prejuízo",
        line=dict(color="#C9A84C", width=1.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(201,168,76,0.07)",
    ))

    fig.add_vline(
        x=pe_pessoas, line_dash="dash", line_color="#E8C878", line_width=1.8,
        annotation_text=f"Break-even: {pe_int} pax",
        annotation_position="top right", annotation_font_color="#E8C878",
    )
    if meta_lucro > 0:
        fig.add_vline(
            x=pe_meta, line_dash="dash", line_color="#9B59B6", line_width=1.5,
            annotation_text=f"Meta lucro: {pe_meta_int} pax",
            annotation_position="top left", annotation_font_color="#C39BD3",
        )
    fig.add_vline(
        x=capacidade_max, line_dash="dot", line_color="#3498DB", line_width=1.2,
        annotation_text=f"Cap. máx: {capacidade_max}",
        annotation_position="top right", annotation_font_color="#85C1E9",
    )
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)")
    fig.add_trace(go.Scatter(
        x=[pe_pessoas], y=[pe_receita], mode="markers",
        marker=dict(color="#E8C878", size=15, symbol="star"),
        name="Break-even ★",
    ))

    fig.update_layout(
        **_LAYOUT,
        xaxis_title="Número de Participantes",
        yaxis_title="Valor (R$)",
        yaxis_tickprefix="R$ ",
        legend=dict(orientation="h", y=-0.18),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabela de Cenários ────────────────────────────────────────────
    st.markdown("#### 📊 Tabela de Cenários")

    # CORRIGIDO: inclui 0 participantes para mostrar o prejuízo de custo fixo
    # e filtra negativos (que podiam aparecer se pe_pessoas fosse muito pequeno)
    pontos_base = [int(pe_pessoas * m) for m in [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]]
    pontos = sorted(
        set(pontos_base + [0, pe_int, pe_meta_int, capacidade_max])
    )

    cenarios = []
    for n in pontos:
        if n < 0:
            continue
        r = n * valor_ingresso
        c = custo_fixo + n * custo_variavel
        l = r - c
        label = ""
        if n == pe_int:
            label = " 🎯 Break-even"
        elif n == pe_meta_int and n != pe_int:
            label = " 🏆 Meta"
        elif n == capacidade_max and n not in (pe_int, pe_meta_int):
            label = " 🏟️ Lotação máx."
        cenarios.append({
            "Participantes": f"{n}{label}",
            "Receita":       f"R$ {r:,.2f}",
            "Custo Total":   f"R$ {c:,.2f}",
            "Resultado":     f"{'✅ Lucro' if l >= 0 else '❌ Prejuízo'}  R$ {abs(l):,.2f}",
        })

    st.dataframe(pd.DataFrame(cenarios), use_container_width=True, hide_index=True)
