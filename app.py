# =============================================================================
# 🦅 ATHLOS 360 - V12.0 (DOBLE PORTADA + REPORTE V25)
# =============================================================================
import streamlit as st
import pandas as pd
import os
import math

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

# ESTILOS CSS
st.markdown("""
<style>
    .main-title { font-size: 28px; font-weight: bold; color: #000; margin-bottom: 5px; }
    .sub-title { font-size: 18px; color: #666; margin-bottom: 20px; border-bottom: 2px solid #FF4B4B; }
    .card-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 15px; }
    .stat-label { font-size: 14px; font-weight: bold; color: #555; }
    .stat-value { font-size: 22px; font-weight: bold; color: #000; }
    .comp-text { font-size: 13px; margin-top: 5px; }
    .pos { color: #008000; font-weight: bold; }
    .neg { color: #D00000; font-weight: bold; }
    .disc-header { background-color: #eee; padding: 8px; font-weight: bold; border-radius: 5px; margin-top: 10px; }
    .welcome-header { font-size: 36px; font-weight: bold; color: #1E1E1E; text-align: center; margin-top: 50px; }
    .welcome-sub { font-size: 20px; color: #555; text-align: center; margin-bottom: 50px; }
</style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS (CACHE SAFE) ---
ARCHIVO = "06 Sem (tst).xlsx"

@st.cache_data(ttl=60)
def get_df(nombre_hoja):
    if not os.path.exists(ARCHIVO): return None
    try:
        xls = pd.ExcelFile(ARCHIVO, engine='openpyxl')
        target = next((h for h in xls.sheet_names if nombre_hoja.lower() in h.lower().replace(":","")), None)
        if target:
            # Leer como string para control total
            df = pd.read_excel(xls, sheet_name=target, dtype=str)
            df.columns = [str(c).strip() for c in df.columns]
            col = next((c for c in df.columns if c.lower() in ['nombre','deportista','atleta']), None)
            if col: df.rename(columns={col: 'Nombre'}, inplace=True)
            return df
    except: return None
    return None

# --- 3. SANITIZADORES Y FORMATOS ---
def clean_time_val(val):
    if pd.isna(val) or str(val).strip() in ['','-','nan','0','00:00:00','None']: return 0.0
