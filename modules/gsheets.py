"""
Motor de dados — SQLite local.
Substitui o backend Google Sheets mantendo a mesma API pública,
então nenhum outro módulo precisa mudar.

O banco é criado automaticamente em: <pasta do app>/data/tesouraria.db
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
CAIXA_COLS  = ["Data", "Descrição", "Tipo", "Categoria", "Valor"]
SOCIOS_COLS = ["Nome", "Telefone"] + MESES

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tesouraria.db"


# ─────────────────────────────────────────────────────────────────────────────
# Inicialização
# ─────────────────────────────────────────────────────────────────────────────

def _init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    meses_cols = "\n".join(f'    "{m}" TEXT NOT NULL DEFAULT "Pendente",' for m in MESES)
    with _conn() as con:
        con.executescript(f"""
            CREATE TABLE IF NOT EXISTS fluxo_caixa (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                data        TEXT NOT NULL,
                descricao   TEXT NOT NULL,
                tipo        TEXT NOT NULL,
                categoria   TEXT NOT NULL,
                valor       REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS socios (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nome      TEXT NOT NULL UNIQUE,
                telefone  TEXT NOT NULL DEFAULT "",
                {meses_cols}
                _dummy    INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS solicitacoes_verba (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                diretoria         TEXT NOT NULL,
                descricao         TEXT NOT NULL,
                valor             REAL NOT NULL,
                data_solicitacao  TEXT NOT NULL,
                status            TEXT NOT NULL DEFAULT 'Pendente',
                observacao        TEXT DEFAULT '',
                data_resposta     TEXT
            );

            CREATE TABLE IF NOT EXISTS reservas (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                nome       TEXT NOT NULL UNIQUE,
                meta       REAL NOT NULL DEFAULT 0,
                saldo      REAL NOT NULL DEFAULT 0,
                criado_em  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reservas_mov (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                reserva_id  INTEGER NOT NULL,
                tipo        TEXT NOT NULL,
                valor       REAL NOT NULL,
                data        TEXT NOT NULL,
                descricao   TEXT DEFAULT '',
                FOREIGN KEY (reserva_id) REFERENCES reservas(id)
            );
        """)


@contextmanager
def _conn():
    con = sqlite3.connect(_DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


_init_db()


# ─────────────────────────────────────────────────────────────────────────────
# API pública de leitura
# ─────────────────────────────────────────────────────────────────────────────

def load_caixa() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query(
            "SELECT data AS Data, descricao AS Descrição, tipo AS Tipo, "
            "       categoria AS Categoria, valor AS Valor "
            "FROM fluxo_caixa ORDER BY data DESC",
            con,
        )
    if df.empty:
        return pd.DataFrame(columns=CAIXA_COLS)
    df["Data"]  = pd.to_datetime(df["Data"], errors="coerce").dt.date
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
    return df


def load_socios() -> pd.DataFrame:
    cols_sql = ", ".join(
        ['"nome" AS Nome', '"telefone" AS Telefone']
        + [f'"{m}" AS "{m}"' for m in MESES]
    )
    with _conn() as con:
        df = pd.read_sql_query(f"SELECT {cols_sql} FROM socios", con)
    if df.empty:
        return pd.DataFrame(columns=SOCIOS_COLS)
    return df


def get_caixa_anos() -> list[int]:
    """Retorna lista de anos distintos presentes no fluxo de caixa."""
    with _conn() as con:
        rows = con.execute(
            "SELECT DISTINCT strftime('%Y', data) AS ano FROM fluxo_caixa "
            "WHERE data IS NOT NULL ORDER BY ano DESC"
        ).fetchall()
    return [int(r["ano"]) for r in rows if r["ano"]]


def count_caixa_por_ano(ano: int) -> int:
    with _conn() as con:
        row = con.execute(
            "SELECT COUNT(*) AS n FROM fluxo_caixa WHERE strftime('%Y', data) = ?",
            (str(ano),),
        ).fetchone()
    return row["n"] if row else 0


def count_socios() -> int:
    with _conn() as con:
        row = con.execute("SELECT COUNT(*) AS n FROM socios").fetchone()
    return row["n"] if row else 0


# ─────────────────────────────────────────────────────────────────────────────
# API pública de escrita
# ─────────────────────────────────────────────────────────────────────────────

def append_caixa(row: dict) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO fluxo_caixa (data, descricao, tipo, categoria, valor) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                str(row["Data"]),
                row["Descrição"],
                row["Tipo"],
                row["Categoria"],
                float(row["Valor"]),
            ),
        )


def save_socios(df: pd.DataFrame) -> None:
    meses_cols   = ", ".join(f'"{m}"' for m in MESES)
    placeholders = ", ".join("?" for _ in MESES)
    with _conn() as con:
        con.execute("DELETE FROM socios")
        for _, row in df.iterrows():
            valores_meses = [str(row.get(m, "Pendente")) for m in MESES]
            con.execute(
                f"INSERT INTO socios (nome, telefone, {meses_cols}) "
                f"VALUES (?, ?, {placeholders})",
                [str(row.get("Nome", "")), str(row.get("Telefone", ""))]
                + valores_meses,
            )


def add_socio(nome: str, telefone: str) -> bool:
    try:
        meses_cols = ", ".join(f'"{m}"' for m in MESES)
        defaults   = ", ".join('"Pendente"' for _ in MESES)
        with _conn() as con:
            con.execute(
                f'INSERT INTO socios (nome, telefone, {meses_cols}) '
                f'VALUES (?, ?, {defaults})',
                [nome, telefone],
            )
        return True
    except sqlite3.IntegrityError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# API de limpeza (apenas ADM)
# ─────────────────────────────────────────────────────────────────────────────

def delete_caixa_por_ano(ano: int) -> int:
    """Deleta todos os lançamentos de um ano. Retorna quantos foram removidos."""
    with _conn() as con:
        cur = con.execute(
            "DELETE FROM fluxo_caixa WHERE strftime('%Y', data) = ?",
            (str(ano),),
        )
    return cur.rowcount


def delete_caixa_tudo() -> int:
    """Deleta TODO o fluxo de caixa. Retorna quantos registros foram removidos."""
    with _conn() as con:
        cur = con.execute("DELETE FROM fluxo_caixa")
    return cur.rowcount


def delete_socio(nome: str) -> bool:
    """Remove um sócio pelo nome. Retorna True se encontrado e removido."""
    with _conn() as con:
        cur = con.execute("DELETE FROM socios WHERE nome = ?", (nome,))
    return cur.rowcount > 0


def delete_socios_tudo() -> int:
    """Remove todos os sócios. Retorna quantos foram removidos."""
    with _conn() as con:
        cur = con.execute("DELETE FROM socios")
    return cur.rowcount


def reset_mensalidades() -> None:
    """Redefine todos os meses de todos os sócios para 'Pendente'."""
    sets = ", ".join(f'"{m}" = "Pendente"' for m in MESES)
    with _conn() as con:
        con.execute(f"UPDATE socios SET {sets}")


# ─────────────────────────────────────────────────────────────────────────────
# Solicitações de Verba (pedidos de orçamento de outras diretorias)
# ─────────────────────────────────────────────────────────────────────────────

SOLICITACOES_COLS = [
    "id", "Diretoria", "Descrição", "Valor",
    "Data Solicitação", "Status", "Observação", "Data Resposta",
]


def append_solicitacao(diretoria: str, descricao: str, valor: float) -> None:
    from datetime import date as _date
    with _conn() as con:
        con.execute(
            "INSERT INTO solicitacoes_verba "
            "(diretoria, descricao, valor, data_solicitacao, status) "
            "VALUES (?, ?, ?, ?, 'Pendente')",
            (diretoria.strip(), descricao.strip(), float(valor), str(_date.today())),
        )


def load_solicitacoes() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query(
            "SELECT id, diretoria AS Diretoria, descricao AS Descrição, "
            "valor AS Valor, data_solicitacao AS \"Data Solicitação\", "
            "status AS Status, observacao AS Observação, "
            "data_resposta AS \"Data Resposta\" "
            "FROM solicitacoes_verba ORDER BY id DESC",
            con,
        )
    if df.empty:
        return pd.DataFrame(columns=SOLICITACOES_COLS)
    return df


def count_solicitacoes_pendentes() -> int:
    with _conn() as con:
        row = con.execute(
            "SELECT COUNT(*) AS n FROM solicitacoes_verba WHERE status = 'Pendente'"
        ).fetchone()
    return row["n"] if row else 0


def responder_solicitacao(sol_id: int, status: str, observacao: str = "") -> None:
    """status: 'Aprovado' ou 'Recusado'."""
    from datetime import date as _date
    with _conn() as con:
        con.execute(
            "UPDATE solicitacoes_verba SET status = ?, observacao = ?, "
            "data_resposta = ? WHERE id = ?",
            (status, observacao.strip(), str(_date.today()), sol_id),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Reservas / Metas de Poupança (fundos de reserva do caixa)
# ─────────────────────────────────────────────────────────────────────────────

def load_reservas() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query(
            "SELECT id, nome AS Nome, meta AS Meta, saldo AS Saldo, "
            "criado_em AS \"Criado em\" FROM reservas ORDER BY id",
            con,
        )
    return df


def add_reserva(nome: str, meta: float) -> bool:
    from datetime import date as _date
    try:
        with _conn() as con:
            con.execute(
                "INSERT INTO reservas (nome, meta, saldo, criado_em) "
                "VALUES (?, ?, 0, ?)",
                (nome.strip(), float(meta), str(_date.today())),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def saldo_total_reservado() -> float:
    with _conn() as con:
        row = con.execute("SELECT COALESCE(SUM(saldo), 0) AS s FROM reservas").fetchone()
    return float(row["s"]) if row else 0.0


def saldo_geral_caixa() -> float:
    with _conn() as con:
        row = con.execute(
            "SELECT COALESCE(SUM(CASE WHEN tipo='Entrada' THEN valor ELSE -valor END), 0) "
            "AS s FROM fluxo_caixa"
        ).fetchone()
    return float(row["s"]) if row else 0.0


def aportar_reserva(reserva_id: int, valor: float, descricao: str = "") -> tuple[bool, str]:
    """Move dinheiro do saldo livre para uma reserva. Não altera o saldo geral do caixa."""
    from datetime import date as _date
    valor = float(valor)
    if valor <= 0:
        return False, "O valor deve ser maior que zero."

    disponivel = saldo_geral_caixa() - saldo_total_reservado()
    if valor > disponivel:
        return False, (
            f"Saldo livre insuficiente. Disponível: R$ {disponivel:,.2f}."
        )

    with _conn() as con:
        con.execute("UPDATE reservas SET saldo = saldo + ? WHERE id = ?", (valor, reserva_id))
        con.execute(
            "INSERT INTO reservas_mov (reserva_id, tipo, valor, data, descricao) "
            "VALUES (?, 'Aporte', ?, ?, ?)",
            (reserva_id, valor, str(_date.today()), descricao.strip()),
        )
    return True, "Aporte realizado com sucesso."


def resgatar_reserva(reserva_id: int, valor: float, descricao: str = "") -> tuple[bool, str]:
    """Devolve dinheiro de uma reserva para o saldo livre."""
    from datetime import date as _date
    valor = float(valor)
    if valor <= 0:
        return False, "O valor deve ser maior que zero."

    with _conn() as con:
        row = con.execute("SELECT saldo FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
        if row is None:
            return False, "Reserva não encontrada."
        if valor > float(row["saldo"]):
            return False, f"A reserva possui apenas R$ {row['saldo']:,.2f}."

        con.execute("UPDATE reservas SET saldo = saldo - ? WHERE id = ?", (valor, reserva_id))
        con.execute(
            "INSERT INTO reservas_mov (reserva_id, tipo, valor, data, descricao) "
            "VALUES (?, 'Resgate', ?, ?, ?)",
            (reserva_id, valor, str(_date.today()), descricao.strip()),
        )
    return True, "Resgate realizado com sucesso."


def load_reservas_mov(reserva_id: int) -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql_query(
            "SELECT tipo AS Tipo, valor AS Valor, data AS Data, descricao AS Descrição "
            "FROM reservas_mov WHERE reserva_id = ? ORDER BY id DESC",
            con, params=(reserva_id,),
        )
    return df


def delete_reserva(reserva_id: int) -> bool:
    """Remove uma reserva. O saldo nela é devolvido automaticamente ao caixa livre."""
    with _conn() as con:
        cur = con.execute("DELETE FROM reservas WHERE id = ?", (reserva_id,))
        con.execute("DELETE FROM reservas_mov WHERE reserva_id = ?", (reserva_id,))
    return cur.rowcount > 0
