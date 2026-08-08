"""
Aba Reservas & Poupança.

Sistema de "cofrinhos" internos do caixa: o Tesoureiro pode separar parte
do saldo livre em metas nomeadas (ex: "Reserva de Emergência",
"Formatura 2026", "Manutenção de Equipamentos"). O dinheiro continua
dentro do saldo total do Grêmio — a reserva apenas marca quanto está
"comprometido" com cada objetivo, evitando que seja gasto por engano.
"""
import streamlit as st

from modules import gsheets as gs


def _is_admin() -> bool:
    return st.session_state.get("role") == "admin"


def render() -> None:
    st.subheader("💰 Reservas & Metas de Poupança")
    st.caption(
        "Separe parte do saldo em cofrinhos com objetivo definido, sem perder o "
        "controle do quanto ainda está livre para uso imediato."
    )

    saldo_geral = gs.saldo_geral_caixa()
    saldo_reservado = gs.saldo_total_reservado()
    saldo_livre = saldo_geral - saldo_reservado

    k1, k2, k3 = st.columns(3)
    k1.metric("💰 Saldo Total do Caixa", f"R$ {saldo_geral:,.2f}")
    k2.metric("🔒 Reservado em Metas", f"R$ {saldo_reservado:,.2f}")
    k3.metric("💵 Saldo Livre (disponível)", f"R$ {saldo_livre:,.2f}")

    st.divider()

    if _is_admin():
        _criar_reserva()
        st.divider()

    _listar_reservas(saldo_livre)


def _criar_reserva() -> None:
    with st.expander("➕ Criar Nova Reserva / Meta"):
        with st.form("form_nova_reserva", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input(
                    "Nome da reserva", placeholder="Ex: Reserva de Emergência"
                )
            with c2:
                meta = st.number_input(
                    "Meta (R$) — opcional, use 0 se não houver alvo fixo",
                    min_value=0.0, step=100.0, format="%.2f", value=0.0,
                )
            criar = st.form_submit_button("Criar Reserva", use_container_width=True)

        if criar:
            if not nome.strip():
                st.error("Informe um nome para a reserva.")
            else:
                ok = gs.add_reserva(nome, meta)
                if ok:
                    st.success(f"✅ Reserva '{nome}' criada!")
                    st.rerun()
                else:
                    st.warning("Já existe uma reserva com esse nome.")


def _listar_reservas(saldo_livre: float) -> None:
    df = gs.load_reservas()

    if df.empty:
        st.info(
            "Nenhuma reserva criada ainda. "
            + ("Use o formulário acima para começar." if _is_admin()
               else "Fale com a Tesouraria para criar metas de poupança.")
        )
        return

    st.markdown("#### Reservas Ativas")

    for _, row in df.iterrows():
        nome  = row["Nome"]
        meta  = float(row["Meta"])
        saldo = float(row["Saldo"])
        pct   = min(saldo / meta, 1.0) if meta > 0 else None

        with st.container():
            st.markdown(
                f"""
                <div style="background:#0C1A31;border:1px solid rgba(201,168,76,0.25);
                            border-radius:12px;padding:1rem 1.25rem;margin-bottom:0.5rem;">
                    <p style="margin:0;color:#E8C878;font-family:'Cinzel',serif;font-size:1.05rem;">
                        🏦 {nome}
                    </p>
                    <p style="margin:0.2rem 0 0;color:#EEF2F7;font-size:1.3rem;font-weight:700;">
                        R$ {saldo:,.2f}
                        <span style="color:#7A8EA8;font-size:0.85rem;font-weight:400;">
                            {f" / meta R$ {meta:,.2f}" if meta > 0 else " (sem meta fixa)"}
                        </span>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if pct is not None:
                st.progress(pct, text=f"{pct*100:.0f}% da meta atingida")

            if _is_admin():
                ca, cb, cc, cd = st.columns([2, 2, 2, 1])
                with ca:
                    v_aporte = st.number_input(
                        "Aportar (R$)", min_value=0.0, step=50.0, format="%.2f",
                        key=f"aporte_{row['id']}", label_visibility="collapsed",
                    )
                with cb:
                    if st.button("➕ Aportar", key=f"btn_aporte_{row['id']}", use_container_width=True):
                        ok, msg = gs.aportar_reserva(int(row["id"]), v_aporte)
                        (st.success if ok else st.error)(msg)
                        if ok:
                            st.rerun()
                with cc:
                    v_resgate = st.number_input(
                        "Resgatar (R$)", min_value=0.0, step=50.0, format="%.2f",
                        key=f"resgate_{row['id']}", label_visibility="collapsed",
                    )
                    if st.button("➖ Resgatar", key=f"btn_resgate_{row['id']}", use_container_width=True):
                        ok, msg = gs.resgatar_reserva(int(row["id"]), v_resgate)
                        (st.success if ok else st.error)(msg)
                        if ok:
                            st.rerun()
                with cd:
                    if st.button("🗑️", key=f"btn_del_res_{row['id']}", help="Excluir reserva e devolver saldo ao caixa livre"):
                        gs.delete_reserva(int(row["id"]))
                        st.success(f"Reserva '{nome}' removida — saldo devolvido ao caixa livre.")
                        st.rerun()

            with st.expander("📜 Histórico de movimentações"):
                mov = gs.load_reservas_mov(int(row["id"]))
                if mov.empty:
                    st.caption("Nenhuma movimentação ainda.")
                else:
                    mov_disp = mov.copy()
                    mov_disp["Valor"] = mov_disp["Valor"].apply(lambda v: f"R$ {v:,.2f}")
                    st.dataframe(mov_disp, use_container_width=True, hide_index=True)

            st.divider()
