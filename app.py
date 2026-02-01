import streamlit as st
import pandas as pd
import io
import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ==============================================================================
# 👇👇👇 CONFIGURACIÓN DE ENLACES (PEGA TUS LINKS AQUÍ) 👇👇👇
# ==============================================================================
URL_HISTORICO = "https://github.com/dagoperezh-lgtm/athlos-360-app/raw/refs/heads/main/00%20Estadi%CC%81sticas%20TYM_ACTUALIZADO_V21%20(1).xlsx"
URL_SEMANA    = "https://github.com/dagoperezh-lgtm/athlos-360-app/raw/refs/heads/main/06%20Sem%20(tst).xlsx"
# 🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺🔺

st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold; background-color: #003366; color: white;}
    h1, h2, h3 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES BASE ---
@st.cache_data(ttl=600)
def cargar_datos_github(url_hist, url_sem):
    try:
        df_sem = pd.read_excel(url_sem, engine='openpyxl')
        df_sem.columns = [str(c).strip() for c in df_sem.columns]
        xls = pd.ExcelFile(url_hist, engine='openpyxl')
        dfs_hist = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}
        return df_sem, dfs_hist, None
    except Exception as e:
        return None, None, str(e)

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

def procesar_logica(df_sem, dfs_hist):
    try:
        # LISTA COMPLETA DE MÉTRICAS (RESTAURO V26)
        METRICAS = {
            'tot_tiempo': {'col': 'Tiempo Total (hh:mm:ss)', 'hist': 'Total', 't': 'tiempo', 'lbl': 'Tiempo Total', 'u': ''},
            'tot_dist': {'col': 'Distancia Total (km)', 'hist': 'Distancia Total', 't': 'float', 'lbl': 'Distancia Total', 'u': 'km'},
            'tot_elev': {'col': 'Altimetría Total (m)', 'hist': 'Altimetría', 't': 'float', 'lbl': 'Desnivel Total', 'u': 'm'},
            'cv': {'col': 'CV (Equilibrio)', 'hist': 'CV', 't': 'float', 'lbl': 'Consistencia (CV)', 'u': ''},
            
            'nat_tiempo': {'col': 'Nat: Tiempo (hh:mm:ss)', 'hist': 'Natación', 't': 'tiempo', 'lbl': 'Tiempo', 'u': ''},
            'nat_dist': {'col': 'Nat: Distancia (km)', 'hist': 'Nat Distancia', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
            'nat_ritmo': {'col': 'Nat: Ritmo (min/100m)', 'hist': 'Nat Ritmo', 't': 'tiempo', 'lbl': 'Ritmo', 'u': ' /100m'},
            
            'bike_tiempo': {'col': 'Ciclismo: Tiempo (hh:mm:ss)', 'hist': 'Ciclismo', 't': 'tiempo', 'lbl': 'Tiempo', 'u': ''},
            'bike_dist': {'col': 'Ciclismo: Distancia (km)', 'hist': 'Ciclismo Distancia', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
            'bike_elev': {'col': 'Ciclismo: KOM/Desnivel (m)', 'hist': 'Ciclismo Desnivel', 't': 'float', 'lbl': 'Desnivel', 'u': 'm'},
            'bike_vel': {'col': 'Ciclismo: Vel. Media (km/h)', 'hist': 'Ciclismo Velocidad', 't': 'float', 'lbl': 'Vel. Media', 'u': ' km/h'},
            
            'run_tiempo': {'col': 'Trote: Tiempo (hh:mm:ss)', 'hist': 'Trote', 't': 'tiempo', 'lbl': 'Tiempo', 'u': ''},
            'run_dist': {'col': 'Trote: Distancia (km)', 'hist': 'Trote Distancia', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
            'run_elev': {'col': 'Trote: KOM/Desnivel (m)', 'hist': 'Trote Desnivel', 't': 'float', 'lbl': 'Desnivel', 'u': 'm'},
            'run_ritmo': {'col': 'Trote: Ritmo (min/km)', 'hist': 'Trote Ritmo', 't': 'tiempo', 'lbl': 'Ritmo', 'u': ' /km'}
        }

        # 1. Promedios Club
        avgs_club = {}
        for k, m in METRICAS.items():
            if m['col'] in df_sem.columns:
                vals = df_sem[m['col']].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
                v = vals[vals > (pd.Timedelta(0) if m['t']=='tiempo' else 0)]
                avgs_club[k] = v.mean() if not v.empty else (pd.Timedelta(0) if m['t']=='tiempo' else 0)
            else: avgs_club[k] = None

        # 2. Históricos
        avgs_hist_global = {}
        for k, m in METRICAS.items():
            target = next((s for s in dfs_hist if m['hist'].lower() in s.lower()), None)
            if target:
                cols = [c for c in dfs_hist[target].columns if 'sem' in c.lower()]
                vals = []
                for c in cols:
                    v = dfs_hist[target][c].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
                    if m['t']=='tiempo': vals.extend([x.total_seconds() for x in v if x.total_seconds()>0])
                    else: vals.extend([x for x in v if x>0])
                if vals:
                    avgs_hist_global[k] = pd.Timedelta(seconds=sum(vals)/len(vals)) if m['t']=='tiempo' else sum(vals)/len(vals)
                else: avgs_hist_global[k] = None
            else: avgs_hist_global[k] = None

        # 3. Atletas
        lista_final = []
        c_nom = next((c for c in df_sem.columns if c in ['Deportista', 'Nombre']), None)
        
        if c_nom:
            for _, r in df_sem.iterrows():
                nom = str(r[c_nom]).strip()
                if nom.lower() in ['nan', 'totales', 'promedio']: continue
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
            
        return lista_final, avgs_club, avgs_hist_global, None

    except Exception as e:
        return [], {}, {}, str(e)

def generar_word_v28(data, team_avg, hist_avg):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10.5)
    
    h1 = doc.add_heading("🦅 RESUMEN GLOBAL EQUIPO", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER; h1.runs[0].font.color.rgb = RGBColor(0, 51, 102)
    doc.add_paragraph("Reporte Automático Semanal").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    t = doc.add_table(rows=1, cols=3); t.style = 'Table Grid'
    hdr = t.rows[0].cells; hdr[0].text="MÉTRICA"; hdr[1].text="SEM ACTUAL"; hdr[2].text="HIST ANUAL"
    
    keys = ['tot_tiempo', 'tot_dist', 'tot_elev', 'cv']
    for k in keys:
        if not data: break
        m = data[0]['metrics'][k]['meta']
        r = t.add_row().cells
        r[0].text = m['lbl']
        r[1].text = f"{fmt_val(team_avg.get(k), m['t'])} {m['u']}"
        r[2].text = f"{fmt_val(hist_avg.get(k), m['t'])} {m['u']}"
    doc.add_page_break()

    for d in data:
        doc.add_heading(f"🦅 {d['name']}", level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.
