"""Aba Sócios — tabela interativa de mensalidades e links de cobrança via WhatsApp."""
import urllib.parse
from datetime import date

import pandas as pd
import streamlit as st

from modules import gsheets as gs


# ─────────────────────────────────────────────────────────────────────────────
# Geração de links WhatsApp
# ─────────────────────────────────────────────────────────────────────────────

def _normalizar_telefone(raw: str) -> str:
    """
    Remove formatação e garante prefixo 55 (Brasil).

    CORRIGIDO: versão anterior não validava comprimento mínimo.
    Um número com menos de 10 dígitos (DDD + número) é inválido.
    """
    phone = "".join(c for c in str(raw) if c.isdigit())
    if len(phone) < 10:
        return ""
    if not phone.startswith("55"):
        phone = "55" + phone
    return phone


def _gerar_link_wpp(telefone: str, nome: str, meses_pendentes: list[str]) -> str:
    phone = _normalizar_telefone(telefone)
    if not phone:
        return ""
    meses_str = ", ".join(meses_pendentes)
    msg = (
        f"Olá, {nome}! 😊\n"
        f"Aqui é a Tesouraria do *Grêmio Naval*.\n\n"
        f"Gostaríamos de lembrá-lo(a) que identificamos pendências de mensalidade "
        f"referentes a: *{meses_str}*.\n\n"
        f"Por favor, entre em contato para regularizar sua situação. "
        f"Estamos à disposição! ⚓"
    )
    return f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"


# ─────────────────────────────────────────────────────────────────────────────
# Render principal
# ─────────────────────────────────────────────────────────────────────────────

def render() -> None:
    st.subheader("👥 Painel de Sócios e Mensalidades")

    df_s      = gs.load_socios()
    mes_atual = gs.MESES[date.today().month - 1]

    # ── Cadastro de novo sócio ────────────────────────────────────────
    with st.expander("➕ Cadastrar Novo Sócio"):
        n1, n2, n3 = st.columns([2, 2, 1])
        with n1:
            novo_nome = st.text_input("Nome completo", key="inp_nome_socio")
        with n2:
            novo_tel = st.text_input(
                "Telefone (com DDD)", placeholder="51999887766", key="inp_tel_socio"
            )
        with n3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Adicionar ✚", use_container_width=True):
                if novo_nome.strip():
                    ok = gs.add_socio(novo_nome.strip(), novo_tel.strip())
                    if ok:
                        st.success(f"✅ '{novo_nome}' adicionado!")
                        st.rerun()
                    else:
                        st.warning("Sócio já cadastrado.")
                else:
                    st.error("Informe o nome do sócio.")

    st.divider()

    if df_s.empty:
        st.info("Nenhum sócio cadastrado. Use o formulário acima para adicionar.")
        return

    inad_count = 0
    if mes_atual in df_s.columns:
        inad_count = int(
            (df_s[mes_atual].astype(str).str.strip().str.lower() != "pago").sum()
        )

    tab_todos, tab_inad, tab_relatorio = st.tabs([
        "📋 Todos os Sócios",
        f"⚠️ Inadimplentes — {mes_atual} ({inad_count})",
        "📱 Central de Cobranças",
    ])

    with tab_todos:
        _render_tabela_editavel(df_s)

    with tab_inad:
        _render_inadimplentes(df_s, mes_atual)

    with tab_relatorio:
        _render_central_cobrancas(df_s)


# ─────────────────────────────────────────────────────────────────────────────
# Sub-componentes
# CORRIGIDO: type hints agora usam pd.DataFrame (import no topo do módulo)
# CORRIGIDO: import pandas removido de dentro das funções
# ─────────────────────────────────────────────────────────────────────────────

def _render_tabela_editavel(df: pd.DataFrame) -> None:
    st.markdown("#### Tabela Anual de Mensalidades")
    st.caption("Selecione **Pago** ou **Pendente** em cada célula e salve ao final.")

    col_config = {}
    for mes in gs.MESES:
        if mes in df.columns:
            col_config[mes] = st.column_config.SelectboxColumn(
                mes, options=["Pago", "Pendente"], required=True, width="small"
            )

    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
    )

    if st.button("💾 Salvar Alterações", key="btn_salvar_socios"):
        gs.save_socios(edited)
        st.success("✅ Mensalidades atualizadas com sucesso!")
        st.rerun()


def _render_inadimplentes(df: pd.DataFrame, mes_atual: str) -> None:
    if mes_atual not in df.columns:
        st.error(f"Coluna '{mes_atual}' não encontrada na planilha.")
        return

    df_inad = df[df[mes_atual].astype(str).str.strip().str.lower() != "pago"].copy()

    if df_inad.empty:
        st.success(f"🎉 Todos os sócios estão em dia em **{mes_atual}**!")
        return

    st.warning(
        f"**{len(df_inad)}** sócio(s) com mensalidade pendente em **{mes_atual}**."
    )

    for _, row in df_inad.iterrows():
        nome     = row.get("Nome", "—")
        telefone = row.get("Telefone", "")
        meses_p  = [
            m for m in gs.MESES
            if m in row.index and str(row[m]).strip().lower() != "pago"
        ]
        link = _gerar_link_wpp(telefone, nome, meses_p)

        ca, cb, cc = st.columns([2, 3, 1])
        with ca:
            st.markdown(f"**{nome}**")
        with cb:
            st.caption(f"Pendente: {', '.join(meses_p)}")
        with cc:
            if link:
                st.markdown(
                    f'<a href="{link}" target="_blank" class="wpp-btn">📱 WhatsApp</a>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Sem telefone")
        st.divider()


def _render_central_cobrancas(df: pd.DataFrame) -> None:
    """Mostra links de cobrança para todos os meses com pendências."""
    st.markdown("#### 📱 Central de Cobranças — Visão Geral")
    st.caption("Filtre por mês para ver os sócios inadimplentes e gerar links WhatsApp.")

    mes_sel = st.selectbox(
        "Selecione o mês de referência",
        options=gs.MESES,
        index=date.today().month - 1,
        key="mes_central_cobrancas",
    )

    if mes_sel not in df.columns:
        st.info("Coluna não encontrada.")
        return

    df_inad = df[df[mes_sel].astype(str).str.strip().str.lower() != "pago"].copy()

    st.metric(f"Inadimplentes em {mes_sel}", f"{len(df_inad)} sócios")

    if df_inad.empty:
        st.success(f"✅ Ninguém deve {mes_sel}!")
        return

    rows_html = ""
    for _, row in df_inad.iterrows():
        nome     = row.get("Nome", "—")
        telefone = row.get("Telefone", "")
        meses_p  = [
            m for m in gs.MESES
            if m in row.index and str(row[m]).strip().lower() != "pago"
        ]
        link = _gerar_link_wpp(telefone, nome, meses_p)
        btn  = (
            f'<a href="{link}" target="_blank" class="wpp-btn">📱 Cobrar</a>'
            if link else '<span style="color:#8899AA;font-size:0.8rem">Sem tel.</span>'
        )
        rows_html += (
            f"<tr><td>{nome}</td><td>{len(meses_p)} meses</td><td>{btn}</td></tr>"
        )

    st.markdown(
        f"""
        <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
          <thead>
            <tr style="color:#C9A84C;text-align:left;border-bottom:1px solid rgba(201,168,76,0.3);">
              <th style="padding:8px">Nome</th>
              <th style="padding:8px">Meses Devendo</th>
              <th style="padding:8px">Ação</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )
