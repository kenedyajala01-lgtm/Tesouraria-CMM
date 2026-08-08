"""
Aba Solicitações de Verba.

Qualquer diretoria (RP, Cultural, Esportes, etc.) pode enviar um pedido de
orçamento através de um formulário simples. O Tesoureiro (Administrador)
avalia cada pedido e aprova ou recusa, com um comentário opcional.
"""
from datetime import date

import pandas as pd
import streamlit as st

from modules import gsheets as gs

DIRETORIAS = [
    "RP (Relações Públicas)", "Cultural", "Esportes", "Comunicação",
    "Eventos", "Infraestrutura", "Outra",
]

_STATUS_BADGE = {
    "Pendente": ('⏳ Pendente', 'rgba(230,126,34,0.15)', '#E67E22'),
    "Aprovado": ('✅ Aprovado', 'rgba(39,174,96,0.15)',  '#27AE60'),
    "Recusado": ('❌ Recusado', 'rgba(192,57,43,0.15)',  '#C0392B'),
}


def _is_admin() -> bool:
    return st.session_state.get("role") == "admin"


def render() -> None:
    st.subheader("📨 Solicitação de Verba")
    st.caption(
        "Outras diretorias podem solicitar orçamento para eventos e despesas. "
        "A Tesouraria avalia e responde cada pedido."
    )

    if _is_admin():
        tab_novo, tab_avaliar, tab_historico = st.tabs([
            "📝 Nova Solicitação", "⚖️ Avaliar Pedidos", "📜 Histórico Completo",
        ])
    else:
        tab_novo, tab_historico = st.tabs(["📝 Nova Solicitação", "📜 Minhas Solicitações"])
        tab_avaliar = None

    with tab_novo:
        _form_nova_solicitacao()

    if tab_avaliar is not None:
        with tab_avaliar:
            _painel_avaliacao()

    with tab_historico:
        _historico(mostrar_status_geral=_is_admin())


# ─────────────────────────────────────────────────────────────────────────────

def _form_nova_solicitacao() -> None:
    with st.form("form_solicitacao_verba", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            diretoria_opt = st.selectbox("Diretoria Solicitante", DIRETORIAS)
            diretoria_outra = ""
            if diretoria_opt == "Outra":
                diretoria_outra = st.text_input("Nome da diretoria")
        with c2:
            valor = st.number_input(
                "Valor Solicitado (R$)", min_value=0.01, step=50.0,
                format="%.2f", value=200.0,
            )

        descricao = st.text_area(
            "Descrição do Gasto",
            placeholder="Ex: Compra de material para o evento de integração de outubro",
            height=100,
        )

        enviar = st.form_submit_button("📨 Enviar Solicitação", use_container_width=True)

    if enviar:
        diretoria_final = diretoria_outra.strip() if diretoria_opt == "Outra" else diretoria_opt
        if not diretoria_final:
            st.error("Informe o nome da diretoria solicitante.")
        elif not descricao.strip():
            st.error("O campo **Descrição do Gasto** é obrigatório.")
        else:
            gs.append_solicitacao(diretoria_final, descricao, valor)
            st.success(
                f"✅ Solicitação de **R$ {valor:,.2f}** enviada para a diretoria "
                f"**{diretoria_final}**! A Tesouraria irá avaliar em breve."
            )
            st.rerun()


def _painel_avaliacao() -> None:
    df = gs.load_solicitacoes()
    pendentes = df[df["Status"] == "Pendente"] if not df.empty else df

    if pendentes.empty:
        st.success("🎉 Nenhuma solicitação pendente no momento.")
        return

    st.warning(f"**{len(pendentes)}** solicitação(ões) aguardando avaliação.")

    for _, row in pendentes.iterrows():
        with st.container():
            st.markdown(
                f"""
                <div style="background:#0C1A31;border:1px solid rgba(201,168,76,0.25);
                            border-radius:12px;padding:1rem 1.25rem;margin-bottom:0.75rem;">
                    <p style="margin:0;color:#E8C878;font-family:'Cinzel',serif;font-size:1rem;">
                        {row['Diretoria']} — R$ {row['Valor']:,.2f}
                    </p>
                    <p style="margin:0.3rem 0 0;color:#7A8EA8;font-size:0.85rem;">
                        📅 {row['Data Solicitação']}
                    </p>
                    <p style="margin:0.5rem 0 0;color:#EEF2F7;font-size:0.9rem;">
                        {row['Descrição']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            ca, cb, cc = st.columns([3, 1, 1])
            with ca:
                obs = st.text_input(
                    "Observação (opcional)", key=f"obs_{row['id']}",
                    label_visibility="collapsed",
                    placeholder="Comentário para a diretoria solicitante...",
                )
            with cb:
                if st.button("✅ Aprovar", key=f"aprovar_{row['id']}", use_container_width=True):
                    gs.responder_solicitacao(int(row["id"]), "Aprovado", obs)
                    st.success(f"Solicitação de {row['Diretoria']} aprovada.")
                    st.rerun()
            with cc:
                if st.button("❌ Recusar", key=f"recusar_{row['id']}", use_container_width=True):
                    gs.responder_solicitacao(int(row["id"]), "Recusado", obs)
                    st.warning(f"Solicitação de {row['Diretoria']} recusada.")
                    st.rerun()
            st.divider()


def _historico(mostrar_status_geral: bool) -> None:
    df = gs.load_solicitacoes()
    if df.empty:
        st.info("Nenhuma solicitação registrada ainda.")
        return

    c1, c2, c3 = st.columns(3)
    total = len(df)
    aprovados = int((df["Status"] == "Aprovado").sum())
    pendentes = int((df["Status"] == "Pendente").sum())
    c1.metric("Total de Solicitações", total)
    c2.metric("✅ Aprovadas", aprovados)
    c3.metric("⏳ Pendentes", pendentes)

    f_status = st.selectbox(
        "Filtrar por status", ["Todos", "Pendente", "Aprovado", "Recusado"],
        key="filtro_status_sol",
    )
    df_f = df if f_status == "Todos" else df[df["Status"] == f_status]

    df_disp = df_f.drop(columns=["id"]).copy()
    df_disp["Valor"] = df_disp["Valor"].apply(lambda v: f"R$ {v:,.2f}")
    st.dataframe(df_disp, use_container_width=True, hide_index=True)
