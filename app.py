import streamlit as st
import sys

# --- 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero) ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅")

# --- 2. VERIFICACIÓN DE LIBRERÍAS (Anti-Error) ---
try:
    import pandas as pd
    import openpyxl
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    import io
    import datetime
except ImportError as e:
    st.error("🛑 ERROR CRÍTICO DE INSTALACIÓN")
    st.warning(f"Falta una librería: {e}")
    st.info("Por favor verifica que tu archivo 'requirements.txt' tenga: streamlit, pandas, openpyxl, python-docx")
    st.stop()

# --- 3. ESTILOS ---
st.markdown("""
    <style>
    .main {background-color: #f4f6f9;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #003366; color: white; padding: 10px;}
    h1 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

st.title("🦅 Athlos 360")
st.write("Generador de Reportes de Alto Rendimiento")

# --- 4. LÓGICA DE DATOS ---
def clean_time(val):
    if pd.isna(val) or str(val).strip() in ['NC', '0', '', 'NAN', '-']: return pd.Timedelta(0)
    try:
        if isinstance(val, (datetime.time, datetime.datetime)):
            return pd.Timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
        p = list(map(int, str(val).split(':')))
        if len(p) == 3: return pd.Timedelta(hours=p[0], minutes=p[1], seconds=p[2])
        if len(p) == 2: return pd.Timedelta(minutes=p[0], seconds=p[1])
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
        'tot_dist': {'col': 'Distancia Total (km)', 'hist': 'Distancia Total', 't': 'float', 'lbl': 'Distancia Total', 'u': 'km'},
        'tot_elev': {'col': 'Altimetría Total (m)', 'hist': 'Altimetría', 't': 'float', 'lbl': 'Desnivel Total', 'u': 'm'},
        'cv': {'col': 'CV (Equilibrio)', 'hist': 'CV', 't': 'float', 'lbl': 'Consistencia', 'u': ''},
        'nat_tiempo': {'col': 'Nat: Tiempo (hh:mm:ss)', 'hist': 'Natación', 't': 'tiempo', 'lbl': 'Tiempo Nat', 'u': ''},
        'bike_tiempo': {'col': 'Ciclismo: Tiempo (hh:mm:ss)', 'hist': 'Ciclismo', 't': 'tiempo', 'lbl': 'Tiempo Bici', 'u': ''},
        'run_tiempo': {'col': 'Trote: Tiempo (hh:mm:ss)', 'hist': 'Trote', 't': 'tiempo', 'lbl': 'Tiempo Trote', 'u': ''}
    }
    
    # 1. Promedios Club
    avgs = {}
    for k, m in METRICAS.items():
        if m['col'] in df_sem.columns:
            vals = df_sem[m['col']].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
            if m['t']=='tiempo': 
                v = vals[vals > pd.Timedelta(0)]
                avgs[k] = v.mean() if not v.empty else pd.Timedelta(0)
            else:
                v = vals[vals > 0]
                avgs[k] = v.mean() if not v.empty else 0.0
        else: avgs[k] = None
        
    # 2. Históricos Globales
    avgs_h_glob = {}
    for k, m in METRICAS.items():
        target = next((s for s in dfs_hist if m['hist'].lower() in s.lower()), None)
        if target:
            df = dfs_hist[target]
            cols = [c for c in df.columns if 'sem' in c.lower()]
            vals = []
            for c in cols:
                v_col = df[c].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
                if m['t']=='tiempo': vals.extend([v.total_seconds() for v in v_col if v.total_seconds()>0])
                else: vals.extend([v for v in v_col if v>0])
            if vals:
                if m['t']=='tiempo': avgs_h_glob[k] = pd.Timedelta(seconds=sum(vals)/len(vals))
                else: avgs_h_glob[k] = sum(vals)/len(vals)
            else: avgs_h_glob[k] = None
        else: avgs_h_glob[k] = None

    # 3. Atletas
    data = []
    c_nom = next((c for c in df_sem.columns if c in ['Deportista', 'Nombre']), None)
    if not c_nom: return [], {}, {}

    for _, r in df_sem.iterrows():
        nom = str(r[c_nom]).strip()
        if nom.lower() in ['nan', 'totales']: continue
        
        metrics = {}
        for k, m in METRICAS.items():
            curr = clean_time(r.get(m['col'])) if m['t']=='tiempo' else clean_float(r.get(m['col']))
            hist = None
            target = next((s for s in dfs_hist if m['hist'].lower() in s.lower()), None)
            if target:
                dfh = dfs_hist[target]
                cnh = next((c for c in dfh.columns if c.lower() in ['nombre','deportista']), None)
                if cnh:
                    row_h = dfh[dfh[cnh].astype(str).str.lower().str.strip() == nom.lower()]
                    if not row_h.empty:
                        cols = [c for c in dfh.columns if 'sem' in c.lower()]
                        if cols:
                            vs = [clean_time(row_h.iloc[0][c]) if m['t']=='tiempo' else clean_float(row_h.iloc[0][c]) for c in cols]
                            if m['t']=='tiempo':
                                vs = [x.total_seconds() for x in vs if x.total_seconds()>0]
                                if vs: hist = pd.Timedelta(seconds=sum(vs)/len(vs))
                            else:
                                vs = [x for x in vs if x>0]
                                if vs: hist = sum(vs)/len(vs)
            metrics[k] = {'val': curr, 'avg': avgs.get(k), 'hist': hist, 'meta': m}
        data.append({'name': nom, 'metrics': metrics})
        
    return data, avgs, avgs_h_glob

def generar_word(data, sem_name, avgs, avgs_h):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10.5)
    
    # PORTADA
    doc.add_heading("🦅 RESUMEN GLOBAL EQUIPO", 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Reporte: {sem_name}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    t = doc.add_table(1, 3); t.style = 'Table Grid'
    h = t.rows[0].cells; h[0].text="Métrica"; h[1].text="Prom. Semana"; h[2].text="Prom. Anual"
    
    keys = ['tot_tiempo', 'tot_dist', 'tot_elev', 'cv']
    for k in keys:
        m = data[0]['metrics'][k]['meta']
        r = t.add_row().cells
        r[0].text = m['lbl']
        r[1].text = f"{fmt_val(avgs.get(k), m['t'])} {m['u']}"
        r[2].text = f"{fmt_val(avgs_h.get(k), m['t'])} {m['u']}"
        
    doc.add_page_break()
    
    # FICHAS
    for d in data:
        doc.add_heading(f"🦅 {d['name']}", 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("─"*40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        ms = d['metrics']
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"⏱️ {fmt_val(ms['tot_tiempo']['val'],'tiempo')}  |  📏 {fmt_val(ms['tot_dist']['val'],'float')} km").bold=True
        
        # Tabla Detalle
        td = doc.add_table(1, 4); td.autofit = True
        hd = td.rows[0].cells; hd[0].text="Métrica"; hd[1].text="Dato"; hd[2].text="Vs Equipo"; hd[3].text="Vs Anual"
        
        for k, item in ms.items():
            m = item['meta']; v = item['val']
            if m['t']=='tiempo' and v.total_seconds()==0: continue
            if m['t']=='float' and v==0: continue
            
            row = td.add_row().cells
            row[0].text = m['lbl']
            row[1].text = f"{fmt_val(v, m['t'])} {m['u']}"
            
            avg = item['avg']
            if avg:
                if m['t']=='tiempo': ok = (v-avg).total_seconds()>=0
                else: ok = (v-avg)>=0
                row[2].text = f"{'+' if ok else '-'}"
            
            hist = item['hist']
            if hist:
                if m['t']=='tiempo': ok = (v-hist).total_seconds()>=0
                else: ok = (v-hist)>=0
                row[3].text = f"{'+' if ok else '-'}"
            else: row[3].text = "New"
            
        doc.add_paragraph("")
        if i < len(data)-1: doc.add_page_break()
        
    bio = io.BytesIO()
    doc.save(bio); bio.seek(0)
    return bio

# --- 5. INTERFAZ ---
with st.sidebar:
    f_hist = st.file_uploader("1. Histórico", type="xlsx")
    f_sem = st.file_uploader("2. Semana", type="xlsx")

if f_hist and f_sem:
    if st.button("▶️ GENERAR", type="primary"):
        with st.spinner("Procesando..."):
            try:
                dat, av_s, av_h = procesar(f_hist, f_sem)
                if not dat:
                    st.warning("No se encontraron atletas.")
                else:
                    st.success(f"¡Listo! {len(dat)} atletas.")
                    bio = generar_word(dat, f_sem.name, av_s, av_h)
                    st.download_button("📥 Descargar Word", bio, f"Reporte_{f_sem.name.replace('.xlsx','')}.docx")
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.info("Sube los archivos en la barra lateral.")