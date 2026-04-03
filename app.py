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
        return "green"
    elif p >= 60:
        return "orange"
    return "red"

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
# 📁 TAB 1 — REPORTE MENSUAL
# =========================================================
with tab1:

    st.header("📁 Reporte mensual")

    meses = sorted([r["mes"] for r in reportes_data])
    mes_sel = st.selectbox("Seleccionar mes", meses)

    data = next(r for r in reportes_data if r["mes"] == mes_sel)

    st.subheader(f"Resumen {mes_sel}")

    familias = sorted(data["ahorro_real"].keys())

    # -----------------------------
    # GASTO COMPRAS
    # -----------------------------
    st.markdown("### 🛒 Gasto de compras")

    cols = st.columns(len(familias) + 1)
    total_compras = 0

    for i, f in enumerate(familias):
        val = data["compras"].get(f, 0)
        total_compras += val
        cols[i].metric(f, f"${val:,.0f}")

    cols[-1].metric("Total", f"${total_compras:,.0f}")

    # -----------------------------
    # COSTO PIBE (REEMPLAZA AHORRO TOTAL)
    # -----------------------------
    st.markdown("### 🍱 Costo por pibe")

    vianda = data["vianda_por_pibe"]
    calentada = data["calentada_por_pibe"]
    total_pibe = vianda + calentada

    c1, c2, c3 = st.columns(3)
    c1.metric("Vianda", f"${vianda:,.0f}")
    c2.metric("Calentada", f"${calentada:,.0f}")
    c3.metric("Total", f"${total_pibe:,.0f}")

    # -----------------------------
    # TRANSFERENCIAS
    # -----------------------------
    st.markdown("### 🔁 Transferencias")

    for t in data["transferencias"]:
        st.write(f"{t[0]} → {t[1]}: ${t[2]:,.0f}")

    # -----------------------------
    # AHORRO POR FAMILIA
    # -----------------------------
    st.markdown("### 💰 Ahorro por familia")

    cols = st.columns(len(familias))

    for i, f in enumerate(familias):
        ahorro = data["ahorro_real"][f]
        pct = data["pct_ahorro"][f] * 100

        cols[i].markdown(f"""
        **{f}**  
        ${ahorro:,.0f}  
        <span style="color:{color_pct(pct)};font-weight:bold;">
        {pct:.2f}%
        </span>
        """, unsafe_allow_html=True)

    # -----------------------------
    # GRAFICO UTIL → % AHORRO
    # -----------------------------
    st.markdown("### 📊 % ahorro por familia")

    df_plot = {
        "familia": familias,
        "pct": [data["pct_ahorro"][f] * 100 for f in familias]
    }

    fig = px.bar(df_plot, x="familia", y="pct", text_auto=True)
    fig.update_traces(marker_color=[color_pct(v) for v in df_plot["pct"]])
    fig.update_yaxes(ticksuffix="%")

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# 📊 TAB 2 — DASHBOARD
# =========================================================
with tab2:

    st.header("Evolución")

    familia = st.selectbox("Familia", df["familia"].unique())

    df_f = df[df["familia"] == familia]

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(df_f, x="mes", y="ahorro", title="Ahorro mensual")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.line(df_f, x="mes", y="acum_total", title="Acumulado")
        st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------
    # % AHORRO CON PROMEDIO
    # -----------------------------
    st.subheader("% ahorro mensual")

    avg = df_f["pct"].mean()

    fig3 = go.Figure()

    fig3.add_trace(go.Bar(
        x=df_f["mes"],
        y=df_f["pct"],
        text=[f"{v:.2f}%" for v in df_f["pct"]],
        marker_color=[color_pct(v) for v in df_f["pct"]]
    ))

    fig3.add_trace(go.Scatter(
        x=df_f["mes"],
        y=[avg] * len(df_f),
        mode="lines",
        name=f"Promedio {avg:.2f}%",
        line=dict(dash="dash")
    ))

    fig3.update_yaxes(ticksuffix="%")

    st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# 📈 TAB 3 — COMPARATIVOS
# =========================================================
with tab3:

    st.header("Comparativo anual")

    df["mes_num"] = df["mes"].dt.month

    familia = st.selectbox("Familia", df["familia"].unique(), key="comp")

    df_f = df[df["familia"] == familia]

    # LINEAS POR AÑO
    fig = px.line(
        df_f,
        x="mes_num",
        y="pct",
        color="anio",
        title="Comparación por % de ahorro"
    )

    fig.update_yaxes(ticksuffix="%")

    st.plotly_chart(fig, use_container_width=True)

    # BARRAS POR AÑO
    fig2 = px.bar(
        df_f,
        x="mes_num",
        y="pct",
        color="anio",
        barmode="group",
        text_auto=True
    )

    fig2.update_yaxes(ticksuffix="%")

    st.plotly_chart(fig2, use_container_width=True)
