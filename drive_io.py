import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
import io
import json

SCOPES = ["https://www.googleapis.com/auth/drive"]


@st.cache_resource
def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds)


def listar_archivos(folder_id):
    service = get_drive_service()
    results = service.files().list(
        pageSize=5,
        fields="files(id, name)"
    ).execute()
    return results.get("files", [])


def buscar_archivo(nombre, folder_id):
    service = get_drive_service()
    query = f"name='{nombre}' and '{folder_id}' in parents"
    results = service.files().list(q=query).execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def leer_csv(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    data = request.execute()
    return pd.read_csv(io.BytesIO(data))


def leer_json(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    data = request.execute()
    return json.loads(data.decode("utf-8"))
