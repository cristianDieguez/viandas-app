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
        return "#22c55e"   # verde suave
    elif p >= 60:
        return "#f59e0b"   # amarillo suave
    return "#ef4444"       # rojo suave

# -----------------------------
# CARGA DATOS
# -----------------------------
reportes_data = []
files = listar_archivos(FOLDER_REPORTES)

for f in files:
    name = f.get("name", "")

    if not name.endswith(".json"):
        continue

    try:
        data = leer_json(f["id"])

        if "mes" not in data or "ahorro_real" not in data:
            continue

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
# TAB 1 — REPORTE
# =========================================================
with tab1:

    st.header("📁 Reporte mensual")

    meses = sorted([r["mes"] for r in reportes_data])
    mes_sel = st.selectbox("Seleccionar mes", meses)

    data = next(r for r in reportes_data if r["mes"] == mes_sel)

    familias = sorted(data["ahorro_real"].keys())

    st.divider()

    # -----------------------------
    # COMPRAS
    # -----------------------------
    st.subheader("🛒 Gasto de compras")

    cols = st.columns(len(familias) + 1)
    total_compras = 0

    for i, f in enumerate(familias):
        val = data["compras"].get(f, 0)
        total_compras += val
        cols[i].metric(f, f"${val:,.0f}")

    cols[-1].metric("Total", f"${total_compras:,.0f}")

    st.divider()

    # -----------------------------
    # COSTO
    # -----------------------------
    st.subheader("🍱 Costo por pibe")

    vianda = data["vianda_por_pibe"]
    calentada = data["calentada_por_pibe"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Vianda", f"${vianda:,.0f}")
    c2.metric("Calentada", f"${calentada:,.0f}")
    c3.metric("Total", f"${(vianda+calentada):,.0f}")

    st.divider()

    # -----------------------------
    # TRANSFERENCIAS (FIX VISUAL)
    # -----------------------------
    st.subheader("🔁 Transferencias")

    for t in data["transferencias"]:
        st.markdown(
            f"<div style='font-size:18px;margin-bottom:8px'>"
            f"<b>{t[0]}</b> → <b>{t[1]}</b>: ${t[2]:,.0f}"
            f"</div>",
            unsafe_allow_html=True
        )

    st.divider()

    # -----------------------------
    # AHORRO (FIX VISUAL)
    # -----------------------------
    st.subheader("💰 Ahorro por familia")

    cols = st.columns(len(familias))

    for i, f in enumerate(familias):
        ahorro = data["ahorro_real"][f]
        pct = data["pct_ahorro"][f] * 100

        cols[i].markdown(f"""
        <div style="font-size:26px;font-weight:bold">${ahorro:,.0f}</div>
        <div style="font-size:18px;color:{color_pct(pct)}">{pct:.2f}%</div>
        """, unsafe_allow_html=True)

    st.divider()

    # -----------------------------
    # GRAFICO % (FIX TEXTO)
    # -----------------------------
    st.subheader("📊 % ahorro por familia")

    df_plot = {
        "familia": familias,
        "pct": [data["pct_ahorro"][f] * 100 for f in familias]
    }

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_plot["familia"],
        y=df_plot["pct"],
        text=[f"{v:.2f}%" for v in df_plot["pct"]],
        textposition="outside",
        textfont=dict(size=16),
        marker_color=[color_pct(v) for v in df_plot["pct"]]
    ))

    fig.update_layout(showlegend=False)
    fig.update_yaxes(ticksuffix="%")

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 2 — DASHBOARD
# =========================================================
with tab2:

    st.header("Evolución")

    familia = st.selectbox("Familia", df["familia"].unique())
    df_f = df[df["familia"] == familia]

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(df_f, x="mes", y="ahorro")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(df_f, x="mes", y="acum_total")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("% ahorro mensual")

    avg = df_f["pct"].mean()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_f["mes"],
        y=df_f["pct"],
        text=[f"{v:.2f}%" for v in df_f["pct"]],
        textposition="outside",
        textfont=dict(size=14),
        marker_color=[color_pct(v) for v in df_f["pct"]],
        name=""  # elimina trace 0
    ))

    fig.add_trace(go.Scatter(
        x=df_f["mes"],
        y=[avg]*len(df_f),
        mode="lines",
        name=f"Promedio {avg:.2f}%",
        line=dict(dash="dash")
    ))

    fig.update_yaxes(ticksuffix="%")

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 3 — COMPARATIVOS
# =========================================================
with tab3:

    st.header("Comparativo anual")

    df["mes_num"] = df["mes"].dt.month

    familia = st.selectbox("Familia", df["familia"].unique(), key="comp")
    df_f = df[df["familia"] == familia]

    fig = px.line(
        df_f,
        x="mes_num",
        y="pct",
        color="anio"
    )

    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)

    # BARRAS FIX VISUAL
    fig2 = go.Figure()

    fig2.add_trace(go.Bar(
        x=df_f["mes_num"],
        y=df_f["pct"],
        text=[f"{v:.2f}%" for v in df_f["pct"]],
        textposition="outside",
        textfont=dict(size=14)
    ))

    fig2.update_yaxes(ticksuffix="%")

    st.plotly_chart(fig2, use_container_width=True)
