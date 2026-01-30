import streamlit as st
import sys
import io
import datetime

# --- 1. VERIFICACIÓN DE LIBRERÍAS (ANTI-CRASH) ---
try:
    import pandas as pd
    import openpyxl
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError as e:
    st.error(f"🛑 Error Crítico: Falta la librería {e}")
    st.info("Verifica tu archivo requirements.txt en GitHub.")
    st.stop()

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="centered")

# Estilos CSS
st.markdown("""
    <style>
    .stButton>button {width: 100%; background-color: #003366; color: white; font-weight: bold; border-radius: 8px; padding: 0.5rem;}
    .stButton>button:hover {background-color: #004080; color: white;}
    h1 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

st.title("🦅 Athlos 360")
st.markdown("**Generador de Reportes de Alto Rendimiento (Versión Web V26)**")
st.write("---")

# --- 3. FUNCIONES DE LIMPIEZA Y FORMATO ---
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

# --- 4. LÓGICA DE PROCESAMIENTO (CEREBRO) ---
def procesar_datos(f_hist, f_sem):
    # Cargar Archivos
    df_sem = pd.read_excel(f_sem, engine='openpyxl')
    df_sem.columns = [str(c).strip() for c in df_sem.columns]
    
    xls = pd.ExcelFile(f_hist, engine='openpyxl')
    dfs_hist = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}
    
    # Definición de Métricas Completa (V25)
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
        'bike_elev':   {'col': 'Ciclismo: KOM/Desnivel (m)', 'hist': 'Ciclismo Desnivel', 't': 'float', 'lbl': 'Desnivel', 'u': 'm'},
        'bike_vel':    {'col': 'Ciclismo: Vel. Media (km/h)', 'hist': 'Ciclismo Velocidad', 't': 'float', 'lbl': 'Vel. Media', 'u': ' km/h'},
        
        'run_tiempo': {'col': 'Trote: Tiempo (hh:mm:ss)', 'hist': 'Trote', 't': 'tiempo', 'lbl': 'Tiempo', 'u': ''},
        'run_dist':   {'col': 'Trote: Distancia (km)', 'hist': 'Trote Distancia', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'run_elev':   {'col': 'Trote: KOM/Desnivel (m)', 'hist': 'Trote Desnivel', 't': 'float', 'lbl': 'Desnivel', 'u': 'm'},
        'run_ritmo':  {'col': 'Trote: Ritmo (min/km)', 'hist': 'Trote Ritmo', 't': 'tiempo', 'lbl': 'Ritmo', 'u': ' /km'},
    }
    
    # 1. Promedios Club
    avgs_club = {}
    for k, m in METRICAS.items():
        if m['col'] in df_sem.columns:
            vals = df_sem[m['col']].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
            if m['t']=='tiempo': 
                v = vals[vals > pd.Timedelta(0)]
                avgs_club[k] = v.mean() if not v.empty else pd.Timedelta(0)
            else:
                v = vals[vals > 0]
                avgs_club[k] = v.mean() if not v.empty else 0.0
        else: avgs_club[k] = None
        
    # 2. Promedios Históricos Globales
    avgs_hist_global = {}
    for k, m in METRICAS.items():
        target = next((s for s in dfs_hist if m['hist'].lower() in s.lower()), None)
        if target:
            cols = [c for c in dfs_hist[target].columns if 'sem' in c.lower()]
            vals = []
            for c in cols:
                v_col = dfs_hist[target][c].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
                if m['t']=='tiempo': vals.extend([v.total_seconds() for v in v_col if v.total_seconds()>0])
                else: vals.extend([v for v in v_col if v>0])
            if vals:
                avgs_hist_global[k] = pd.Timedelta(seconds=sum(vals)/len(vals)) if m['t']=='tiempo' else sum(vals)/len(vals)
            else: avgs_hist_global[k] = None
        else: avgs_hist_global[k] = None

    # 3. Procesar Atletas
    lista_final = []
    c_nom = next((c for c in df_sem.columns if c in ['Deportista', 'Nombre']), None)
    if not c_nom: return [], {}, {}

    for _, r in df_sem.iterrows():
        nom = str(r[c_nom]).strip()
        if nom.lower() in ['nan', 'totales']: continue
        
        metrics = {}
        for k, m in METRICAS.items():
            curr = clean_time(r.get(m['col'])) if m['t']=='tiempo' else clean_float(r.get(m['col']))
            h_val = None
            target = next((s for s in dfs_hist if m['hist'].lower() in s.lower()), None)
            if target:
                dh = dfs_hist[target]
                cnh = next((c for c in dh.columns if c.lower() in ['nombre','deportista']), None)
                if cnh:
                    rh = dh[dh[cnh].astype(str).str.lower().str.strip() == nom.lower()]
                    if not rh.empty:
                        cols = [c for c in dh.columns if 'sem' in c.lower()]
                        if cols:
                            vs = [clean_time(rh.iloc[0][c]) if m['t']=='tiempo' else clean_float(rh.iloc[0][c]) for c in cols]
                            if m['t']=='tiempo': 
                                vs = [x.total_seconds() for x in vs if x.total_seconds()>0]
                                if vs: h_val = pd.Timedelta(seconds=sum(vs)/len(vs))
                            else:
                                vs = [x for x in vs if x>0]
                                if vs: h_val = sum(vs)/len(vs)
            metrics[k] = {'val': curr, 'avg': avgs_club.get(k), 'hist': h_val, 'meta': m}
        lista_final.append({'name': nom, 'metrics': metrics})
        
    return lista_final, avgs_club, avgs_hist_global

# --- 5. GENERADOR DE WORD (DISEÑO V25 COMPLETO) ---
def generar_word_v25(data, fname, team_avg, hist_avg):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10.5)
    style.paragraph_format.space_after = Pt(2)

    # --- PORTADA ---
    h1 = doc.add_heading("🦅 RESUM