import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from drive_io import *
from historico import construir_historico

st.set_page_config(layout="wide")

st.title("📊 Comedor Viandas Dashboard")

# -----------------------------
# CONFIG
# -----------------------------
FOLDER_INPUT = "1yeVBoN3fS6FrKttSWygTHp0AiXDkUhzI"
FOLDER_REPORTES = "1LP5pK36K-GkJ0Mn1lY-Q21jO0lMzxOLy"
FOLDER_CONFIG = "1RuywZBTKi_aJAEks4kgtveRUPqBvPYAE"
FOLDER_HISTORICO = "1EF1iLR9jIA9tc9Xd_GrnnlnxI4sXVMFN"

# -----------------------------
# HELPERS
# -----------------------------
def color_pct(p):
    if p > 70:
        return "#22c55e"
    elif p >= 60:
        return "#f59e0b"
    return "#ef4444"

def arrow_pct(p):
    if p > 70:
        return "↑"
    elif p >= 60:
        return "–"
    return "↓"

# -----------------------------
# DATA
# -----------------------------
reportes_data = []
files = listar_archivos(FOLDER_REPORTES)

for f in files:
    if not f["name"].endswith(".json"):
        continue
    try:
        data = leer_json(f["id"])
        if "mes" in data:
            reportes_data.append(data)
    except:
        continue

if not reportes_data:
    st.warning("No hay reportes válidos")
    st.stop()

df = construir_historico(reportes_data)

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3 = st.tabs([
    "📁 Reporte mensual",
    "📊 Dashboard",
    "📈 Comparativos"
])

# =========================================================
# TAB 1
# =========================================================
with tab1:

    meses = sorted([r["mes"] for r in reportes_data])
    mes_sel = st.selectbox("Seleccionar mes", meses)

    data = next(r for r in reportes_data if r["mes"] == mes_sel)
    familias = sorted(data["ahorro_real"].keys())

    st.divider()

    # COMPRAS
    st.subheader("🛒 Gasto de compras")
    cols = st.columns(len(familias) + 1)

    total = 0
    for i, f in enumerate(familias):
        val = data["compras"].get(f, 0)
        total += val
        cols[i].metric(f, f"${val:,.0f}")

    cols[-1].metric("Total", f"${total:,.0f}")

    st.divider()

    # COSTO
    st.subheader("🍱 Costo por pibe")

    vianda = data["vianda_por_pibe"]
    calentada = data["calentada_por_pibe"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Vianda", f"${vianda:,.0f}")
    c2.metric("Calentada", f"${calentada:,.0f}")
    c3.metric("Total", f"${(vianda+calentada):,.0f}")

    st.divider()

    # TRANSFERENCIAS
    st.subheader("🔁 Transferencias")

    cols = st.columns(len(data["transferencias"]))

    for i, t in enumerate(data["transferencias"]):
        cols[i].markdown(f"""
        <div style="padding:15px;border:1px solid #374151;border-radius:10px;text-align:center">
            <div style="font-size:18px">
                <b>{t[0]}</b>
                <span style="color:#f97316;font-size:20px"> → </span>
                <b>{t[1]}</b>
            </div>
            <div style="font-size:24px;font-weight:bold;margin-top:5px">
                ${t[2]:,.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # AHORRO (FIX NOMBRE + BADGE)
    st.subheader("💰 Ahorro por familia")

    cols = st.columns(len(familias))

    for i, f in enumerate(familias):
        ahorro = data["ahorro_real"][f]
        pct = data["pct_ahorro"][f] * 100

        cols[i].markdown(f"""
        <div style="font-size:18px;color:#9ca3af;margin-bottom:4px">{f}</div>
        <div style="font-size:28px;font-weight:bold">${ahorro:,.0f}</div>
        <div style="
            display:inline-block;
            padding:6px 12px;
            border-radius:20px;
            background:{color_pct(pct)};
            color:white;
            font-weight:bold;
            margin-top:6px">
            {arrow_pct(pct)} {pct:.2f}%
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # =============================
    # ACUMULADOS (FIX NOMBRE)
    # =============================
    st.subheader("💰 Ahorro acumulado")

    df_fam = df.copy()
    df_fam = df_fam[df_fam["mes"] <= mes_sel]

    cols1 = st.columns(len(familias))
    cols2 = st.columns(len(familias))

    for i, f in enumerate(familias):

        df_tmp = df_fam[df_fam["familia"] == f]

        anual = df_tmp[df_tmp["anio"] == int(mes_sel[:4])]["ahorro"].sum()
        total = df_tmp["ahorro"].sum()

        cols1[i].metric(f"{f} (Año)", f"${anual:,.0f}")
        cols2[i].metric(f"{f} (Total)", f"${total:,.0f}")
