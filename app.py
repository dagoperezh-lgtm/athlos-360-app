import streamlit as st
import sys

# --- 1. INTENTO DE IMPORTAR LIBRERÍAS ---
try:
    import pandas as pd
    import openpyxl
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    import io
    import datetime
    import numpy as np
except ImportError as e:
    st.error(f"🛑 Error de librería: {e}")
    st.stop()

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="centered")

st.markdown("""
    <style>
    .stButton>button {width: 100%; background-color: #003366; color: white;}
    </style>
""", unsafe_allow_html=True)

st.title("🦅 Athlos 360")
st.success("✅ Sistema listo.")
st.write("---")

# --- 3. FUNCIONES ---
def clean_time(val):
    if pd.isna(val) or str(val).strip() in ['NC', '0', '', 'NAN', '-']: return pd.Timedelta(0)
    try:
        if isinstance(val, (datetime.time, datetime.datetime)):
            return pd.Timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
        p = list(map(int, str(val).split(':')))
        if len(p) == 3: return pd.Timedelta(hours=p[0], minutes=p[1], seconds=p[2])
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

def procesar(f_hist, f_sem):
    df_sem = pd.read_excel(f_sem, engine='openpyxl')
    df_sem.columns = [str(c).strip() for c in df_sem.columns]
    
    xls = pd.ExcelFile(f_hist, engine='openpyxl')
    dfs_hist = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}
    
    METRICAS = {
        'tot_tiempo': {'col': 'Tiempo Total (hh:mm:ss)', 'hist': 'Total', 't': 'tiempo', 'lbl': 'Tiempo Total', 'u': ''},
        'tot_dist': {'col': 'Distancia Total (km)', 'hist': 'Distancia Total', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'tot_elev': {'col': 'Altimetría Total (m)', 'hist': 'Altimetría', 't': 'float', 'lbl': 'Desnivel', 'u': 'm'},
        'cv': {'col': 'CV (Equilibrio)', 'hist': 'CV', 't': 'float', 'lbl': 'Consistencia', 'u': ''},
        'nat_tiempo': {'col': 'Nat: Tiempo (hh:mm:ss)', 'hist': 'Natación', 't': 'tiempo', 'lbl': 'Tiempo Nat', 'u': ''},
        'bike_tiempo': {'col': 'Ciclismo: Tiempo (hh:mm:ss)', 'hist': 'Ciclismo', 't': 'tiempo', 'lbl': 'Tiempo Bici', 'u': ''},
        'run_tiempo': {'col': 'Trote: Tiempo (hh:mm:ss)', 'hist': 'Trote', 't': 'tiempo', 'lbl': 'Tiempo Trote', 'u': ''}
    }
    
    avgs = {}
    for k, m in METRICAS.items():
        if m['col'] in df_sem.columns:
            vals = df_sem[m['col']].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
            v = vals[vals > (pd.Timedelta(0) if m['t']=='tiempo' else 0)]
            avgs[k] = v.mean() if not v.empty else (pd.Timedelta(0) if m['t']=='tiempo' else 0)
        else: avgs[k] = None
        
    avgs_h = {}
    for k, m in METRICAS.items():
        t = next((s for s in dfs_hist if m['hist'].lower() in s.lower()), None)
        if t:
            cols = [c for c in dfs_hist[t].columns if 'sem' in c.lower()]
            vals = []
            for c in cols:
                v = dfs_hist[t][c].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
                if m['t']=='tiempo': vals.extend([x.total_seconds() for x in v if x.total_seconds()>0])
                else: vals.extend([x for x in v if x>0])
            if vals:
                avgs_h[k] = pd.Timedelta(seconds=sum(vals)/len(vals)) if m['t']=='tiempo' else sum(vals)/len(vals)
            else: avgs_h[k] = None
        else: avgs_h[k] = None

    data = []
    c_nom = next((c for c in df_sem.columns if c in ['Deportista', 'Nombre']), None)
    if not c_nom: return [], {}, {}

    for _, r in df_sem.iterrows():
        nom = str(r[c_nom]).strip()
        if nom.lower() in ['nan', 'totales']: continue
        ms = {}
        for k, m in METRICAS.items():
            curr = clean_time(r.get(m['col'])) if m['t']=='tiempo' else clean_float(r.get(m['col']))
            h_val = None
            t = next((s for s in dfs_hist if m['hist'].lower() in s.lower()), None)
            if t:
                dh = dfs_hist[t]
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
            ms[k] = {'val': curr, 'avg': avgs.get(k), 'hist': h_val, 'meta': m}
        data.append({'name': nom, 'metrics': ms})
    return data, avgs, avgs_h

def gen_word(data, sem, av_s, av_h):
    doc = Document()
    style = doc.styles['Normal']; style.font.name='Calibri'; style.font.size=Pt(10.5)
    
    doc.add_heading("🦅 RESUMEN GLOBAL", 0).alignment=WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Reporte: {sem}").alignment=WD_ALIGN_PARAGRAPH.CENTER
    
    t = doc.add_table(1,3); t.style='Table Grid'
    h = t.rows[0].cells; h[0].text="Métrica"; h[1].text="Prom. Sem"; h[2].text="Prom. Anual"
    keys=['tot_tiempo','tot_dist','tot_elev','cv']
    for k in keys:
        if k in data[0]['metrics']:
            m = data[0]['metrics'][k]['meta']
            r = t.add_row().cells
            r[0].text=m['lbl']
            r[1].text=f"{fmt_val(av_s.get(k),m['t'])} {m['u']}"
            r[2].text=f"{fmt_val(av_h.get(k),m['t'])} {m['u']}"
    doc.add_page_break()
    
    # --- AQUÍ ESTABA EL ERROR CORREGIDO (enumerate) ---
    for i, d in enumerate(data):
        doc.add_heading(f"🦅 {d['name']}",1).alignment=WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("─"*40).alignment=WD_ALIGN_PARAGRAPH.CENTER
        ms = d['metrics']
        p = doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"⏱️ {fmt_val(ms['tot_tiempo']['val'],'tiempo')} | 📏 {fmt_val(ms['tot_dist']['val'],'float')} km").bold=True
        
        td = doc.add_table(1,4); td.autofit=True
        hd = td.rows[0].cells; hd[0].text="Métrica"; hd[1].text="Dato"; hd[2].text="Vs Eq"; hd[3].text="Vs Anual"
        for k, item in ms.items():
            m=item['meta']; v=item['val']
            if m['t']=='tiempo' and v.total_seconds()==0: continue
            if m['t']=='float' and v==0: continue
            r = td.add_row().cells
            r[0].text=m['lbl']; r[1].text=f"{fmt_val(v,m['t'])} {m['u']}"
            
            avg=item['avg']
            if avg:
                ok = (v-avg).total_seconds()>=0 if m['t']=='tiempo' else (v-avg)>=0
                r[2].text = "+" if ok else "-"
            else: r[2].text="-"
            
            hist=item['hist']
            if hist:
                ok = (v-hist).total_seconds()>=0 if m['t']=='tiempo' else (v-hist)>=0
                r[3].text = "+" if ok else "-"
            else: r[3].text="New"
            
        doc.add_paragraph("")
        if i < len(data)-1: doc.add_page_break()
        
    b = io.BytesIO()
    doc.save(b); b.seek(0)
    return b

# --- 4. INTERFAZ ---
with st.sidebar:
    st.header("Cargar Datos")
    fh = st.file_uploader("Histórico", type="xlsx")
    fs = st.file_uploader("Semana", type="xlsx")

if fh and fs:
    if st.button("▶️ GENERAR", type="primary"):
        try:
            d, avs, avh = procesar(fh, fs)
            st.success(f"Procesados {len(d)} atletas.")
            st.download_button("📥 Descargar Word", gen_word(d, fs.name, avs, avh), f"Reporte_{fs.name.replace('.xlsx','')}.docx")
        except Exception as e:
            st.error(f"Error: {e}")