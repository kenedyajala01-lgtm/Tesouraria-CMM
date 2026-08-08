"""Aba Exportar Dados — download da tabela de registros financeiros em CSV e Excel."""
from datetime import date, datetime
from io import BytesIO

import pandas as pd
import streamlit as st

from modules import gsheets as gs


def _to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def _to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for nome_aba, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=nome_aba[:31])
    return buffer.getvalue()


def render() -> None:
    st.subheader("📤 Exportação de Dados")
    st.caption(
        "Baixe os registros financeiros da tesouraria em **CSV** ou **Excel** "
        "para arquivar, auditar ou compartilhar com a diretoria."
    )

    df_caixa = gs.load_caixa()

    if df_caixa.empty:
        st.info("Nenhum lançamento registrado ainda para exportar.")
        return

    # ── Filtro de período ────────────────────────────────────────────
    st.markdown("#### Filtrar período (opcional)")
    df_caixa["Data"] = pd.to_datetime(df_caixa["Data"], errors="coerce")

    c1, c2 = st.columns(2)
    with c1:
        anos_disp = sorted(df_caixa["Data"].dt.year.dropna().unique().astype(int), reverse=True)
        ano_sel = st.selectbox("Ano", ["Todos"] + anos_disp, key="exp_ano")
    with c2:
        mes_sel = st.selectbox("Mês", ["Todos"] + gs.MESES, key="exp_mes")

    df_exp = df_caixa.copy()
    if ano_sel != "Todos":
        df_exp = df_exp[df_exp["Data"].dt.year == ano_sel]
    if mes_sel != "Todos":
        df_exp = df_exp[df_exp["Data"].dt.month == gs.MESES.index(mes_sel) + 1]

    df_exp = df_exp.sort_values("Data", ascending=False).copy()
    df_exp_fmt = df_exp.copy()
    df_exp_fmt["Data"] = df_exp_fmt["Data"].dt.strftime("%d/%m/%Y")

    st.dataframe(df_exp_fmt, use_container_width=True, hide_index=True)
    st.caption(f"{len(df_exp_fmt)} registro(s) selecionado(s) para exportação.")

    st.divider()

    ts = datetime.now().strftime("%Y%m%d_%H%M")

    col_csv, col_xlsx, col_xlsx_full = st.columns(3)

    with col_csv:
        st.download_button(
            "⬇️ Baixar CSV — Fluxo de Caixa",
            data=_to_csv_bytes(df_exp_fmt),
            file_name=f"fluxo_caixa_{ts}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_xlsx:
        st.download_button(
            "⬇️ Baixar Excel — Fluxo de Caixa",
            data=_to_excel_bytes({"Fluxo de Caixa": df_exp_fmt}),
            file_name=f"fluxo_caixa_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_xlsx_full:
        df_socios = gs.load_socios()
        sheets = {"Fluxo de Caixa": df_exp_fmt}
        if not df_socios.empty:
            sheets["Sócios"] = df_socios
        st.download_button(
            "⬇️ Excel Completo (Caixa + Sócios)",
            data=_to_excel_bytes(sheets),
            file_name=f"tesouraria_completa_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
