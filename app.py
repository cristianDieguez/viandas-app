import streamlit as st
import plotly.express as px
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
# 📁 TAB 1 — REPORTE MENSUAL (NUEVO PRO)
# =========================================================
with tab1:

    st.header("📁 Reporte mensual")

    meses = sorted([r["mes"] for r in reportes_data])

    mes_sel = st.selectbox("Seleccionar mes", meses)

    data = next(r for r in reportes_data if r["mes"] == mes_sel)

    st.subheader(f"Resumen {mes_sel}")

    # -----------------------------
    # MÉTRICAS GENERALES
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    total_ahorro = sum(data["ahorro_real"].values())

    col1.metric("💰 Ahorro total", f"${total_ahorro:,.0f}")

    vianda = data.get("vianda_por_pibe", 0)
    calentada = data.get("calentada_por_pibe", 0)

    col2.metric("🍱 Vianda por pibe", f"${vianda:,.0f}")
    col3.metric("🔥 Calentada por pibe", f"${calentada:,.0f}")

    st.divider()

    # -----------------------------
    # POR FAMILIA
    # -----------------------------
    st.subheader("👨‍👩‍👧‍👦 Ahorro por familia")

    familias = list(data["ahorro_real"].keys())

    cols = st.columns(len(familias))

    for i, f in enumerate(familias):
        ahorro = data["ahorro_real"][f]
        pct = data["pct_ahorro"][f] * 100

        cols[i].metric(
            label=f,
            value=f"${ahorro:,.0f}",
            delta=f"{pct:.2f}%"
        )

    st.divider()

    # -----------------------------
    # GRÁFICO DISTRIBUCIÓN
    # -----------------------------
    st.subheader("📊 Distribución del ahorro")

    df_bar = px.data.tips()  # placeholder limpio

    df_bar = {
        "familia": list(data["ahorro_real"].keys()),
        "ahorro": list(data["ahorro_real"].values())
    }

    fig = px.bar(df_bar, x="familia", y="ahorro", text_auto=True)

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

    # NUEVO → barras %
    st.subheader("% ahorro mensual")

    fig3 = px.bar(df_f, x="mes", y="pct", text_auto=True)
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

    # ✔ CORRECTO: comparar por %
    fig = px.line(
        df_f,
        x="mes_num",
        y="pct",
        color="anio",
        title="Comparación por % de ahorro"
    )

    fig.update_yaxes(ticksuffix="%")

    st.plotly_chart(fig, use_container_width=True)
