import streamlit as st
import pandas as pd
import io
import datetime
import openpyxl
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Athlos 360 | Generator",
    page_icon="🦅",
    layout="centered"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {width: 100%; border-radius: 5px; background-color: #003366; color: white; font-weight: bold;}
    .stButton>button:hover {background-color: #004080; color: white;}
    h1 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

# --- TÍTULO ---
st.title("🦅 Athlos 360")
st.markdown("**Generador de Reportes de Rendimiento Deportivo**")
st.write("---")

# --- SIDEBAR: CARGA DE ARCHIVOS ---
with st.sidebar:
    st.header("📂 Carga de Datos")
    f_hist = st.file_uploader("1. Sube el Histórico Anual (.xlsx)", type=["xlsx"])
    f_sem = st.file_uploader("2. Sube la Semana Actual (.xlsx)", type=["xlsx"])
    
    st.info("💡 Asegúrate de subir los archivos correctos del Club TYM.")

# --- FUNCIONES DE LIMPIEZA ---
def clean_time(val):
    if pd.isna(val) or val in ['NC', '0', '', 'NAN', '-']: return pd.Timedelta(0)
    s = str(val).strip()
    try:
        if isinstance(val, (datetime.time, datetime.datetime)):
            return pd.Timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
        parts = list(map(int, s.split(':')))
        if len(parts) == 3: return pd.Timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
    except: pass
    return pd.Timedelta(0)

def fmt_val(val, tipo):
    if val is None: return "-"
    if tipo == 'tiempo':
        if val.total_seconds() == 0: return "-"
        s = int(val.total_seconds())
        if s < 3600: return f"{s//60}m {s%60}s"
        return f"{s//3600}h {(s%3600)//60}m"
    else: return f"{val:.1f}" if val > 0 else "-"

# --- LÓGICA DE PROCESAMIENTO ---
def procesar_datos_web(file_hist, file_sem):
    # 1. Leer archivos
    df_sem = pd.read_excel(file_sem, engine='openpyxl')
    df_sem.columns = [str(c).strip() for c in df_sem.columns]
    
    xls = pd.ExcelFile(file_hist, engine='openpyxl')
    dfs_hist = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}

    # 2. Definir Métricas
    METRICAS = {
        'tot_tiempo': {'col': 'Tiempo Total (hh:mm:ss)', 'hist': 'Total', 'tipo': 'tiempo', 'label': 'Tiempo Total', 'unit': ''},
        'tot_dist':   {'col': 'Distancia Total (km)', 'hist': 'Distancia Total', 'tipo': 'float', 'label': 'Distancia Total', 'unit': 'km'},
        'tot_elev':   {'col': 'Altimetría Total (m)', 'hist': 'Altimetría', 'tipo': 'float', 'label': 'Desnivel Total', 'unit': 'm'},
        'cv':         {'col': 'CV (Equilibrio)', 'hist': 'CV', 'tipo': 'float', 'label': 'Consistencia', 'unit': ''},
        'nat_tiempo': {'col': 'Nat: Tiempo (hh:mm:ss)', 'hist': 'Natación', 'tipo': 'tiempo', 'label': 'Tiempo', 'unit': ''},
        'nat_dist':   {'col': 'Nat: Distancia (km)', 'hist': 'Nat Distancia', 'tipo': 'float', 'label': 'Distancia', 'unit': 'km'},
        'nat_ritmo':  {'col': 'Nat: Ritmo (min/100m)', 'hist': 'Nat Ritmo', 'tipo': 'tiempo', 'label': 'Ritmo', 'unit': '/100m'},
        'bike_tiempo': {'col': 'Ciclismo: Tiempo (hh:mm:ss)', 'hist': 'Ciclismo', 'tipo': 'tiempo', 'label': 'Tiempo', 'unit': ''},
        'bike_dist':   {'col': 'Ciclismo: Distancia (km)', 'hist': 'Ciclismo Distancia', 'tipo': 'float', 'label': 'Distancia', 'unit': 'km'},
        'bike_elev':   {'col': 'Ciclismo: KOM/Desnivel (m)', 'hist': 'Ciclismo Desnivel', 'tipo': 'float', 'label': 'Desnivel', 'unit': 'm'},
        'bike_vel':    {'col': 'Ciclismo: Vel. Media (km/h)', 'hist': 'Ciclismo Velocidad', 'tipo': 'float', 'label': 'Vel. Media', 'unit': 'km/h'},
        'run_tiempo': {'col': 'Trote: Tiempo (hh:mm:ss)', 'hist': 'Trote', 'tipo': 'tiempo', 'label': 'Tiempo', 'unit': ''},
        'run_dist':   {'col': 'Trote: Distancia (km)', 'hist': 'Trote Distancia', 'tipo': 'float', 'label': 'Distancia', 'unit': 'km'},
        'run_elev':   {'col': 'Trote: KOM/Desnivel (m)', 'hist': 'Trote Desnivel', 'tipo': 'float', 'label': 'Desnivel', 'unit': 'm'},
        'run_ritmo':  {'col': 'Trote: Ritmo (min/km)', 'hist': 'Trote Ritmo', 'tipo': 'tiempo', 'label': 'Ritmo', 'unit': '/km'},
    }

    # 3. Calcular Promedios Equipo
    avgs_club = {}
    for k, info in METRICAS.items():
        if info['col'] in df_sem.columns:
            vals = df_sem[info['col']].apply(lambda x: clean_time(x) if info['tipo'] == 'tiempo' else clean_float(x))
            if info['tipo'] == 'tiempo': vals = vals[vals > pd.Timedelta(0)]; avgs_club[k] = vals.mean() if not vals.empty else pd.Timedelta(0)
            else: vals = vals[vals > 0]; avgs_club[k] = vals.mean() if not vals.empty else 0.0
        else: avgs_club[k] = None

    # 4. Calcular Históricos Globales
    avgs_hist_global = {}
    for k, info in METRICAS.items():
        target_sheet = next((s for s in dfs_hist.keys() if info['hist'].lower() in s.lower()), None)
        if target_sheet:
            df_h = dfs_hist[target_sheet]
            cols_vals = [c for c in df_h.columns if 'sem' in c.lower()]
            all_vals = []
            for c in cols_vals:
                vals_col = df_h[c].apply(lambda x: clean_time(x) if info['tipo'] == 'tiempo' else clean_float(x))
                if info['tipo'] == 'tiempo': all_vals