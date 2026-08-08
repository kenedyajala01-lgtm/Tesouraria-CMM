"""Aba Limpeza de Dados — exclusão seletiva de registros antigos (ADM only)."""
import streamlit as st
from modules import gsheets as gs


def _is_admin() -> bool:
    return st.session_state.get("role") == "admin"


# ─── chaves de confirmação no session_state ───────────────────────────────────
_KEY_CONF_ANO   = "limpeza_conf_ano"
_KEY_CONF_CAIXA = "limpeza_conf_caixa_tudo"
_KEY_CONF_SOC1  = "limpeza_conf_socio_unico"
_KEY_CONF_SOC_T = "limpeza_conf_socios_tudo"
_KEY_CONF_RESET = "limpeza_conf_reset_mens"


def _reset_confs():
    for k in (_KEY_CONF_ANO, _KEY_CONF_CAIXA, _KEY_CONF_SOC1,
              _KEY_CONF_SOC_T, _KEY_CONF_RESET):
        st.session_state[k] = False


def render() -> None:
    if not _is_admin():
        st.error("🔒 **Acesso negado.** Esta área é restrita a Administradores.")
        st.stop()

    # Inicializa flags de confirmação
    for k in (_KEY_CONF_ANO, _KEY_CONF_CAIXA, _KEY_CONF_SOC1,
              _KEY_CONF_SOC_T, _KEY_CONF_RESET):
        if k not in st.session_state:
            st.session_state[k] = False

    st.subheader("🗑️ Limpeza de Dados")
    st.caption(
        "Exclua registros antigos para manter o banco enxuto. "
        "**Todas as operações são irreversíveis.**"
    )

    col_caixa, col_socios = st.columns(2, gap="large")

    # ══════════════════════════════════════════════════════════════════
    # COLUNA ESQUERDA — Fluxo de Caixa
    # ══════════════════════════════════════════════════════════════════
    with col_caixa:
        st.markdown(
            """
            <div style="background:#0C1A31;border:1px solid rgba(201,168,76,0.2);
                        border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem;">
                <h4 style="margin:0 0 0.2rem;color:#E8C878 !important;">
                    💸 Fluxo de Caixa
                </h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        anos = gs.get_caixa_anos()
        total_caixa = sum(gs.count_caixa_por_ano(a) for a in anos)

        if not anos:
            st.info("Nenhum lançamento registrado.")
        else:
            st.metric("Total de lançamentos", total_caixa)

            # ── Deletar por ano ───────────────────────────────────────
            st.markdown("**Excluir lançamentos por ano**")
            ano_sel = st.selectbox(
                "Selecione o ano", anos,
                key="limpeza_ano_sel",
                label_visibility="collapsed",
            )
            qtd_ano = gs.count_caixa_por_ano(ano_sel)
            st.caption(f"{qtd_ano} registro(s) em {ano_sel}")

            conf_ano = st.checkbox(
                f"Confirmo: excluir todos os {qtd_ano} lançamentos de {ano_sel}",
                key=_KEY_CONF_ANO,
            )
            if st.button(
                f"🗑️ Excluir {ano_sel}", key="btn_del_ano",
                disabled=not conf_ano,
                use_container_width=True,
            ):
                n = gs.delete_caixa_por_ano(ano_sel)
                st.success(f"✅ {n} lançamento(s) de {ano_sel} removidos.")
                _reset_confs()
                st.rerun()

            st.divider()

            # ── Deletar tudo ──────────────────────────────────────────
            st.markdown("**⚠️ Limpar TODO o fluxo de caixa**")
            conf_tudo = st.checkbox(
                f"Confirmo: apagar todos os {total_caixa} lançamentos definitivamente",
                key=_KEY_CONF_CAIXA,
            )
            if st.button(
                "💥 Apagar tudo (caixa)", key="btn_del_caixa_tudo",
                disabled=not conf_tudo,
                use_container_width=True,
            ):
                n = gs.delete_caixa_tudo()
                st.success(f"✅ {n} lançamentos removidos.")
                _reset_confs()
                st.rerun()

    # ══════════════════════════════════════════════════════════════════
    # COLUNA DIREITA — Sócios
    # ══════════════════════════════════════════════════════════════════
    with col_socios:
        st.markdown(
            """
            <div style="background:#0C1A31;border:1px solid rgba(201,168,76,0.2);
                        border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem;">
                <h4 style="margin:0 0 0.2rem;color:#E8C878 !important;">
                    👥 Sócios & Mensalidades
                </h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        df_s        = gs.load_socios()
        total_socios = gs.count_socios()

        if df_s.empty:
            st.info("Nenhum sócio cadastrado.")
        else:
            st.metric("Total de sócios", total_socios)

            # ── Remover sócio individual ──────────────────────────────
            st.markdown("**Remover sócio individual**")
            nomes = df_s["Nome"].tolist()
            socio_sel = st.selectbox(
                "Selecione o sócio", nomes,
                key="limpeza_socio_sel",
                label_visibility="collapsed",
            )
            conf_soc1 = st.checkbox(
                f"Confirmo: remover '{socio_sel}' permanentemente",
                key=_KEY_CONF_SOC1,
            )
            if st.button(
                f"🗑️ Remover sócio", key="btn_del_socio",
                disabled=not conf_soc1,
                use_container_width=True,
            ):
                ok = gs.delete_socio(socio_sel)
                if ok:
                    st.success(f"✅ '{socio_sel}' removido.")
                else:
                    st.error("Sócio não encontrado.")
                _reset_confs()
                st.rerun()

            st.divider()

            # ── Reset mensalidades ────────────────────────────────────
            st.markdown("**🔄 Resetar mensalidades (novo ano)**")
            st.caption(
                "Redefine todos os meses de todos os sócios para **Pendente**, "
                "sem remover o cadastro."
            )
            conf_reset = st.checkbox(
                "Confirmo: redefinir todas as mensalidades para Pendente",
                key=_KEY_CONF_RESET,
            )
            if st.button(
                "🔄 Resetar mensalidades", key="btn_reset_mens",
                disabled=not conf_reset,
                use_container_width=True,
            ):
                gs.reset_mensalidades()
                st.success(f"✅ Mensalidades de {total_socios} sócio(s) redefinidas.")
                _reset_confs()
                st.rerun()

            st.divider()

            # ── Remover todos os sócios ───────────────────────────────
            st.markdown("**⚠️ Remover TODOS os sócios**")
            conf_soc_t = st.checkbox(
                f"Confirmo: excluir todos os {total_socios} sócios definitivamente",
                key=_KEY_CONF_SOC_T,
            )
            if st.button(
                "💥 Apagar todos os sócios", key="btn_del_socios_tudo",
                disabled=not conf_soc_t,
                use_container_width=True,
            ):
                n = gs.delete_socios_tudo()
                st.success(f"✅ {n} sócio(s) removidos.")
                _reset_confs()
                st.rerun()
