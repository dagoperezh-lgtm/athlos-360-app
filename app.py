import streamlit as st
import sys
import io
import datetime

# --- 1. VERIFICACIÓN DE LIBRERÍAS ---
try:
    import pandas as pd
    import openpyxl
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError as e:
    st.error(f"🛑 Error de Librería: {e}")
    st.info("Revisa requirements.txt")
    st.stop()

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="centered")
st.markdown("""
    <style>
    .stButton>button {width: 100%; background-color: #003366; color: white; padding: 10px; border-radius: 8px;}
    .stButton>button:hover {background-color: #004080; color: white;}
    h1 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

st.title("🦅 Athlos 360")
st.write("Generador de Reportes de Alto Rendimiento (V26)")
st.write("---")

# --- 3. FUNCIONES AUXILIARES ---
def clean_time(val):
    if pd.isna(val) or str(val).strip() in ['NC', '0', '', 'NAN', '-']: return pd.Timedelta(0)
    try:
        if isinstance(val, (datetime.time, datetime.datetime)):
            return pd.Timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
        parts = list(map(int, str(val).split(':')))
        if len(parts) == 3: return pd.Timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
        if len(parts) == 2: return pd.Timedelta(minutes=parts[0], seconds=parts[1])
    except: pass
    return pd.Timedelta(0)

def clean_float(val):
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def fmt_val(val, tipo):
    if val is None: return "-"
    if tipo == 'tiempo':
        if val.total_seconds() == 0: return "-"
        s = int(val.total_seconds())
        if s < 3600: return f"{s//60}m {s%60}s"
        return f"{s//3600}h {(s%3600)//60}m"
    return f"{val:.1f}" if val > 0 else "-"

# --- 4. PROCESAMIENTO DE DATOS ---
def procesar_datos(f_hist, f_sem):
    df_sem = pd.read_excel(f_sem, engine='openpyxl')
    df_sem.columns = [str(c).strip() for c in df_sem.columns]
    
    xls = pd.ExcelFile(f_hist, engine='openpyxl')
    dfs_hist = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}
    
    # METRICAS
    METRICAS = {
        'tot_tiempo': {'col': 'Tiempo Total (hh:mm:ss)', 'hist': 'Total', 't': 'tiempo', 'lbl': 'Tiempo Total', 'u': ''},
        'tot_dist':   {'col': 'Distancia Total (km)', 'hist': 'Distancia Total', 't': 'float', 'lbl': 'Distancia Total', 'u': 'km'},
        'tot_elev':   {'col': 'Altimetría Total (m)', 'hist': 'Altimetría', 't': 'float', 'lbl': 'Desnivel Total', 'u': 'm'},
        'cv':         {'col': 'CV (Equilibrio)', 'hist': 'CV', 't': 'float', 'lbl': 'Consistencia (CV)', 'u': ''},
        
        'nat_tiempo': {'col': 'Nat: Tiempo (hh:mm:ss)', 'hist': 'Natación', 't': 'tiempo', 'lbl': 'Tiempo', 'u': ''},
        'nat_dist':   {'col': 'Nat: Distancia (km)', 'hist': 'Nat Distancia', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'nat_ritmo':  {'col': 'Nat: Ritmo (min/100m)', 'hist': 'Nat Ritmo', 't': 'tiempo', 'lbl': 'Ritmo', 'u': ' /100m'},
        
        'bike_tiempo': {'col': 'Ciclismo: Tiempo (hh:mm:ss)', 'hist': 'Ciclismo', 't': 'tiempo', 'lbl': 'Tiempo', 'u': ''},
        'bike_dist':   {'col': 'Ciclismo: Distancia (km)', 'hist': 'Ciclismo Distancia', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'bike_elev':   {'col': 'Ciclismo: KOM/Desnivel (m)', 'hist': 'Ciclismo Desnivel', 't': 'float', 'lbl