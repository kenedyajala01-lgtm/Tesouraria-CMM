"""
⚓ Tesouraria Grêmio Naval — app.py
Ponto de entrada da aplicação com controle de acesso (ADM / Visitante).
"""
import hashlib
import streamlit as st

st.set_page_config(
    page_title="Tesouraria — Grêmio Naval",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Constantes de autenticação
# ─────────────────────────────────────────────────────────────────────────────
_SENHA_HASH = hashlib.sha256(b"rogerreidelas2026").hexdigest()


def _check_password(pw: str) -> bool:
    return hashlib.sha256(pw.encode()).hexdigest() == _SENHA_HASH


# ─────────────────────────────────────────────────────────────────────────────
# CSS — Tema Marítimo (Navy × Gold)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Nunito:ital,wght@0,300;0,400;0,600;1,400&display=swap');

    :root {
        --bg:      #060D1B; --surface: #0C1A31; --card:    #102244;
        --border:  rgba(201,168,76,0.18);
        --gold:    #C9A84C; --gold-hi: #E8C878;
        --text:    #EEF2F7; --muted:   #7A8EA8;
        --success: #27AE60; --danger:  #C0392B; --warn: #E67E22;
    }

    .stApp { background-color: var(--bg); color: var(--text); font-family: 'Nunito', sans-serif; }
    .block-container { padding-top: 1.5rem; }

    h1, h2, h3, h4 { font-family: 'Cinzel', serif !important; color: var(--gold) !important; letter-spacing: 0.04em; }
    h1 { font-size: 1.9rem !important; }
    h4 { font-size: 1rem !important; color: var(--gold-hi) !important; }

    .stTabs [data-baseweb="tab-list"] { background: var(--surface); border-radius: 10px; padding: 4px 6px; gap: 4px; border: 1px solid var(--border); }
    .stTabs [data-baseweb="tab"] { color: var(--muted); font-family: 'Cinzel', serif; font-size: 0.82rem; border-radius: 8px; padding: 6px 14px; transition: all 0.2s; }
    .stTabs [aria-selected="true"] { background: var(--gold) !important; color: var(--bg) !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"]:hover { color: var(--gold-hi); }

    [data-testid="stMetric"] { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.25rem; }
    [data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.09em; }
    [data-testid="stMetricValue"]  { color: var(--gold-hi) !important; font-family: 'Cinzel', serif; font-size: 1.5rem !important; }
    [data-testid="stMetricDelta"]  { font-size: 0.8rem !important; }

    .stButton > button { background: linear-gradient(135deg, var(--gold), var(--gold-hi)); color: var(--bg); border: none; border-radius: 8px; font-family: 'Cinzel', serif; font-weight: 700; letter-spacing: 0.05em; padding: 0.45rem 1.25rem; transition: all 0.18s ease; box-shadow: 0 2px 8px rgba(201,168,76,0.25); }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(201,168,76,0.45); }

    .stTextInput input, .stNumberInput input, .stSelectbox > div > div { background-color: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; color: var(--text) !important; }
    .stDateInput input { background: var(--card) !important; color: var(--text) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
    label { color: var(--muted) !important; font-size: 0.82rem; letter-spacing: 0.04em; }

    .stDataFrame { border: 1px solid var(--border) !important; border-radius: 10px !important; }
    .stAlert { border-radius: 10px !important; }
    [data-testid="stNotificationContentSuccess"] { background: rgba(39,174,96,0.12) !important; }
    [data-testid="stNotificationContentError"]   { background: rgba(192,57,43,0.12) !important; }

    details { border: 1px solid var(--border) !important; border-radius: 10px !important; background: var(--surface) !important; }
    summary { color: var(--gold) !important; font-family: 'Cinzel', serif; font-size: 0.88rem; }
    hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

    .wpp-btn { display: inline-block; background: #25D366; color: #fff !important; padding: 3px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 700; text-decoration: none; letter-spacing: 0.03em; transition: opacity 0.15s; }
    .wpp-btn:hover { opacity: 0.85; }

    /* Badge de role */
    .role-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        font-family: 'Cinzel', serif;
    }
    .role-adm  { background: rgba(201,168,76,0.18); color: #E8C878; border: 1px solid rgba(201,168,76,0.4); }
    .role-vis  { background: rgba(52,152,219,0.15); color: #85C1E9; border: 1px solid rgba(52,152,219,0.35); }

    /* Tela de login */
    .login-card {
        max-width: 440px;
        margin: 3rem auto;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 2.5rem 2rem;
    }

    ::-webkit-scrollbar       { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 3px; }

    /* ── Navegação na barra lateral ────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] .stRadio > label { display: none; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 2px; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.55rem 0.9rem;
        margin-bottom: 4px;
        width: 100%;
        transition: all 0.15s ease;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
        border-color: var(--gold);
        background: rgba(201,168,76,0.08);
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] label div p {
        color: var(--text) !important;
        font-size: 0.88rem;
        font-family: 'Nunito', sans-serif;
    }
    [data-testid="stSidebar"] hr { margin: 0.75rem 0 !important; }

    .sidebar-brand {
        text-align: center;
        padding: 0.5rem 0 1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
    }
    .sidebar-brand .anchor { font-size: 2rem; }
    .sidebar-brand h3 {
        font-family: 'Cinzel', serif !important;
        color: var(--gold) !important;
        font-size: 1.05rem !important;
        margin: 0.2rem 0 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Cabeçalho
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center;padding:0.5rem 0 1rem;">
        <div style="font-size:2.4rem;">⚓</div>
        <h1 style="margin:0.1rem 0 0;">GRÊMIO NAVAL</h1>
        <p style="color:#7A8EA8;font-size:0.8rem;letter-spacing:0.18em;
                  text-transform:uppercase;margin-top:0.3rem;">
            Sistema Integrado de Tesouraria
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Estado de sessão
# ─────────────────────────────────────────────────────────────────────────────
if "role" not in st.session_state:
    st.session_state["role"] = None          # None | "admin" | "visitor"
if "login_error" not in st.session_state:
    st.session_state["login_error"] = False

# ─────────────────────────────────────────────────────────────────────────────
# Tela de Acesso (se ainda não autenticado)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state["role"] is None:
    st.markdown(
        """
        <div style="text-align:center;margin-bottom:0.5rem;">
            <p style="color:#7A8EA8;font-size:0.92rem;">
                Selecione como deseja acessar o sistema.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_vis, col_adm = st.columns(2, gap="large")

    with col_vis:
        st.markdown(
            """
            <div style="background:#0C1A31;border:1px solid rgba(52,152,219,0.25);
                        border-radius:14px;padding:1.5rem;text-align:center;margin-bottom:1rem;">
                <div style="font-size:2rem;">👁️</div>
                <h4 style="color:#85C1E9 !important;margin:0.5rem 0 0.3rem;">Visitante</h4>
                <p style="color:#7A8EA8;font-size:0.82rem;margin:0;">
                    Acesso somente leitura.<br>Dashboard · Relatórios · Simulador
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Entrar como Visitante", use_container_width=True, key="btn_visitor"):
            st.session_state["role"] = "visitor"
            st.rerun()

    with col_adm:
        st.markdown(
            """
            <div style="background:#0C1A31;border:1px solid rgba(201,168,76,0.25);
                        border-radius:14px;padding:1.5rem;text-align:center;margin-bottom:1rem;">
                <div style="font-size:2rem;">🔐</div>
                <h4 style="color:#E8C878 !important;margin:0.5rem 0 0.3rem;">Administrador</h4>
                <p style="color:#7A8EA8;font-size:0.82rem;margin:0;">
                    Acesso total ao sistema.<br>Requer senha de administrador.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        senha = st.text_input(
            "Senha", type="password", placeholder="Digite a senha de ADM",
            key="inp_senha_adm", label_visibility="collapsed",
        )
        if st.button("Entrar como Administrador", use_container_width=True, key="btn_adm"):
            if _check_password(senha):
                st.session_state["role"] = "admin"
                st.session_state["login_error"] = False
                st.rerun()
            else:
                st.session_state["login_error"] = True
                st.rerun()

        if st.session_state["login_error"]:
            st.error("🔒 Senha incorreta. Tente novamente.")

    st.stop()  # Não renderiza nada mais enquanto não autenticado

# ─────────────────────────────────────────────────────────────────────────────
# Usuário autenticado
# ─────────────────────────────────────────────────────────────────────────────
role = st.session_state["role"]   # "admin" | "visitor"

# ─────────────────────────────────────────────────────────────────────────────
# Importa módulos
# ─────────────────────────────────────────────────────────────────────────────
from modules import (  # noqa: E402
    dashboard, lancamentos, socios, reservas, solicitacoes,
    relatorios, exportacao, simulador, limpeza, gsheets as gs,
)

# ─────────────────────────────────────────────────────────────────────────────
# Barra lateral — identidade, navegação e logout
# ─────────────────────────────────────────────────────────────────────────────
_badge_html = (
    '<span class="role-badge role-adm">⚙️ ADMINISTRADOR</span>'
    if role == "admin"
    else '<span class="role-badge role-vis">👁️ VISITANTE</span>'
)

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="anchor">⚓</div>
            <h3>GRÊMIO NAVAL</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(_badge_html, unsafe_allow_html=True)
    st.write("")

    if role == "admin":
        _n_pend = gs.count_solicitacoes_pendentes()
        _sol_label = (
            f"📨 Solicitações de Verba ({_n_pend})" if _n_pend else "📨 Solicitações de Verba"
        )
        paginas = [
            "📊 Dashboard",
            "💸 Lançamentos",
            "👥 Sócios & Cobranças",
            "💰 Reservas & Poupança",
            _sol_label,
            "📋 Relatórios",
            "📤 Exportar Dados",
            "🧮 Simulador de Eventos",
            "🗑️ Limpeza de Dados",
        ]
    else:
        paginas = [
            "📊 Dashboard",
            "💰 Reservas & Poupança",
            "📨 Solicitações de Verba",
            "📋 Relatórios",
            "📤 Exportar Dados",
            "🧮 Simulador de Eventos",
            "🔒 Área Restrita",
        ]

    pagina_sel = st.radio(
        "Navegação", paginas, label_visibility="collapsed", key="nav_page",
    )

    st.divider()
    if st.button("🚪 Sair", key="btn_logout", use_container_width=True):
        st.session_state["role"] = None
        st.session_state["login_error"] = False
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Demo warning
# ─────────────────────────────────────────────────────────────────────────────
try:
    _demo = "gcp_service_account" not in st.secrets
except Exception:
    _demo = True

if _demo:
    st.warning(
        "🔒 **Modo Demo** — os dados ficam apenas na memória desta sessão. "
        "Configure `.streamlit/secrets.toml` com suas credenciais do Google Sheets "
        "para persistência real.",
        icon="ℹ️",
    )

# ─────────────────────────────────────────────────────────────────────────────
# Roteamento de página — exibição condicional por role
# ─────────────────────────────────────────────────────────────────────────────
_pagina = pagina_sel.split(" ", 1)[-1].split(" (")[0]  # remove ícone e contador

if _pagina == "Dashboard":
    dashboard.render()
elif _pagina == "Lançamentos" and role == "admin":
    lancamentos.render()
elif _pagina == "Sócios & Cobranças" and role == "admin":
    socios.render()
elif _pagina == "Reservas & Poupança":
    reservas.render()
elif _pagina == "Solicitações de Verba":
    solicitacoes.render()
elif _pagina == "Relatórios":
    relatorios.render()
elif _pagina == "Exportar Dados":
    exportacao.render()
elif _pagina == "Simulador de Eventos":
    simulador.render()
elif _pagina == "Limpeza de Dados" and role == "admin":
    limpeza.render()
elif _pagina == "Área Restrita":
    st.markdown(
        """
        <div style="text-align:center;padding:3rem 1rem;">
            <div style="font-size:3.5rem;margin-bottom:1rem;">🔒</div>
            <h3 style="color:#E74C3C !important;">Acesso Restrito</h3>
            <p style="color:#7A8EA8;font-size:0.95rem;max-width:400px;margin:0 auto 1.5rem;">
                As páginas <strong>Lançamentos</strong>, <strong>Sócios & Cobranças</strong>
                e demais funções administrativas exigem acesso de Administrador.
            </p>
            <p style="color:#7A8EA8;font-size:0.82rem;">
                Clique em <strong>🚪 Sair</strong> e entre com a senha de ADM para liberar o acesso completo.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
