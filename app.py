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
# CARGA SEGURA DE DATOS
# -----------------------------
reportes_data = []
files = []

try:
    files = listar_archivos(FOLDER_REPORTES)

    st.write("DEBUG archivos encontrados:", files)

    for f in files:
        name = f.get("name", "")

        if not name.endswith(".json"):
            continue

        try:
            data = leer_json(f["id"])

            # VALIDACIÓN REAL (NO por nombre)
            if "mes" not in data or "ahorro_real" not in data:
                continue

            reportes_data.append(data)

        except Exception as e:
            st.warning(f"Error leyendo {name}")

except Exception as e:
    st.error("Error conectando con Google Drive")
    st.stop()

if not reportes_data:
    st.warning("No hay reportes válidos en la carpeta")
    st.stop()

# construir histórico
df = construir_historico(reportes_data)

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3 = st.tabs([
    "📊 Dashboard",
    "📈 Comparativos",
    "📁 Reportes"
])

# =============================
# TAB 1
# =============================
with tab1:

    st.header("Evolución de ahorro")

    familia = st.selectbox("Familia", df["familia"].unique())

    df_f = df[df["familia"] == familia]

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(df_f, x="mes", y="ahorro", title="Ahorro mensual")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.line(df_f, x="mes", y="acum_total", title="Ahorro acumulado")
        st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.line(df_f, x="mes", y="pct", title="% ahorro mensual")
    fig3.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig3, use_container_width=True)


# =============================
# TAB 2
# =============================
with tab2:

    st.header("Comparativo entre años")

    df["mes_num"] = df["mes"].dt.month

    familia = st.selectbox("Familia (comparativo)", df["familia"].unique(), key="comp")

    df_f = df[df["familia"] == familia]

    fig = px.line(
        df_f,
        x="mes_num",
        y="ahorro",
        color="anio",
        title="Mismo mes en distintos años"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Acumulado anual")

    fig2 = px.line(
        df_f,
        x="mes",
        y="acum_anual",
        color="anio",
        title="Acumulado por año"
    )

    st.plotly_chart(fig2, use_container_width=True)


# =============================
# TAB 3
# =============================
with tab3:

    st.header("Consulta de reportes")

    meses = []

    for f in files:
        name = f.get("name", "")

        if not name.endswith(".json"):
            continue

        try:
            data = leer_json(f["id"])

            if "mes" not in data:
                continue

            meses.append(data["mes"])

        except:
            continue

    if not meses:
        st.warning("No hay reportes disponibles")
        st.stop()

    mes_sel = st.selectbox("Seleccionar mes", sorted(meses))

    file_id = buscar_archivo(f"{mes_sel}.json", FOLDER_REPORTES)

    if file_id:
        try:
            data = leer_json(file_id)

            st.subheader("Ahorro del mes")

            for f, v in data["ahorro_real"].items():
                pct = data["pct_ahorro"][f] * 100
                st.write(f"**{f}**: ${v:,.2f} ({pct:.2f}%)")

            st.subheader("Detalle JSON")
            st.json(data)

        except:
            st.error("Error leyendo el reporte")
