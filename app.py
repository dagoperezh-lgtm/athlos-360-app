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
    st.error(f"Error de Librería: {e}")
    st.stop()

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅")
st.markdown("""
    <style>
    .stButton>button {
        width: 100%; 
        background-color: #003366; 
        color: white; 
        padding: 10px; 
        border-radius: 8px;
    }
    h1 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

st.title("🦅 Athlos 360")
st.write("Generador de Reportes de Alto Rendimiento (V26.2)")
st.write("---")

# --- 3. FUNCIONES AUXILIARES ---
def clean_time(val):
    if pd.isna(val): return pd.Timedelta(0)
    s_val = str(val).strip()
    if s_val in ['NC', '0', '', 'NAN', '-']: return pd.Timedelta(0)
    try:
        if isinstance(val, (datetime.time, datetime.datetime)):
            return pd.Timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
        parts = list(map(int, s_val.split(':')))
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

# --- 4. PROCESAMIENTO ---
def procesar_datos(f_hist, f_sem):
    df_sem = pd.read_excel(f_sem, engine='openpyxl')
    df_sem.columns = [str(c).strip() for c in df_sem.columns]
    
    xls = pd.ExcelFile(f_hist, engine='openpyxl')
    dfs_hist = {}
    for s in xls.sheet_names:
        dfs_hist[s] = pd.read_excel(xls, sheet_name=s)
    
    # DICCIONARIO VERTICAL (Anti-Error de Sintaxis)
    METRICAS = {
        'tot_tiempo': {
            'col': 'Tiempo Total (hh:mm:ss)', 
            'hist': 'Total', 
            't': 'tiempo', 
            'lbl': 'Tiempo Total', 
            'u': ''
        },
        'tot_dist': {
            'col': 'Distancia Total (km)', 
            'hist': 'Distancia Total', 
            't': 'float', 
            'lbl': 'Distancia Total', 
            'u': 'km'
        },
        'tot_elev': {
            'col': 'Altimetría Total (m)', 
            'hist': 'Altimetría', 
            't': 'float', 
            'lbl': 'Desnivel Total', 
            'u': 'm'
        },
        'cv': {
            'col': 'CV (Equilibrio)', 
            'hist': 'CV', 
            't': 'float', 
            'lbl': 'Consistencia (CV)', 
            'u': ''
        },
        'nat_tiempo': {
            'col': 'Nat: Tiempo (hh:mm:ss)', 
            'hist': 'Natación', 
            't': 'tiempo', 
            'lbl': 'Tiempo', 
            'u': ''
        },
        'nat_dist': {
            'col': 'Nat: Distancia (km)', 
            'hist': 'Nat Distancia', 
            't': 'float', 
            'lbl': 'Distancia', 
            'u': 'km'
        },
        'nat_ritmo': {
            'col': 'Nat: Ritmo (min/100m)', 
            'hist': 'Nat Ritmo', 
            't': 'tiempo', 
            'lbl': 'Ritmo', 
            'u': '/100m'
        },
        'bike_tiempo': {
            'col': 'Ciclismo: Tiempo (hh:mm:ss)', 
            'hist': 'Ciclismo', 
            't': 'tiempo', 
            'lbl': 'Tiempo', 
            'u': ''
        },
        'bike_dist': {
            'col': 'Ciclismo: Distancia (km)', 
            'hist': 'Ciclismo Distancia', 
            't': 'float', 
            'lbl': 'Distancia', 
            'u': 'km'
        },
        'bike_elev': {
            'col': 'Ciclismo: KOM/Desnivel (m)', 
            'hist': 'Ciclismo Desnivel', 
            't': 'float', 
            'lbl': 'Desnivel', 
            'u': 'm'
        },
        'bike_vel': {
            'col': 'Ciclismo: Vel. Media (km/h)', 
            'hist': 'Ciclismo Velocidad', 
            't': 'float', 
            'lbl': 'Vel. Media', 
            'u': 'km/h'
        },
        'run_tiempo': {
            'col': 'Trote: Tiempo (hh:mm:ss)', 
            'hist': 'Trote', 
            't': 'tiempo', 
            'lbl': 'Tiempo', 
            'u': ''
        },
        'run_dist': {
            'col': 'Trote: Distancia (km)', 
            'hist': 'Trote Distancia', 
            't': 'float', 
            'lbl': 'Distancia', 
            'u': 'km'
        },
        'run_elev': {
            'col': 'Trote: KOM/Desnivel (m)', 
            'hist': 'Trote Desnivel', 
            't': 'float', 
            'lbl': 'Desnivel', 
            'u': 'm'
        },
        'run_ritmo': {
            'col': 'Trote: Ritmo (min/km)', 
            'hist': 'Trote Ritmo', 
            't': 'tiempo', 
            'lbl': 'Ritmo', 
            'u': '/km'
        }
    }
    
    # 1. Promedios
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
        
    # 2. Históricos
    avgs_hist_global = {}
    for k, m in METRICAS.items():
        target = next((s for s in dfs_hist if m['hist'].lower() in s.lower()), None)
        if target:
            cols = [c for c in dfs_hist[target].columns if 'sem' in c.lower()]
            vals = []
            for c in cols:
                v = dfs_hist[target][c].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
                if m['t']=='tiempo': 
                    vals.extend([x.total_seconds() for x in v if x.total_seconds()>0])
                else: 
                    vals.extend([x for x in v if x>0])
            if vals:
                if m['t']=='tiempo':
                    avgs_hist_global[k] = pd.Timedelta(seconds=sum(vals)/len(vals))
                else:
                    avgs_hist_global[k] = sum(vals)/len(vals)
            else: avgs_hist_global[k] = None
        else: avgs_hist_global[k] = None

    # 3. Atletas
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
            metrics[k] = {'val': curr, 'avg': avgs_club.get(k), 'hist': h_val, 'meta': m}
        lista_final.append({'name': nom, 'metrics': metrics})
        
    return lista_final, avgs_club, avgs_hist_global

# --- 5. GENERAR WORD ---
def generar_word_v26(data, fname, team_avg, hist_avg):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10.5)
    style.paragraph_format.space_after = Pt(2)

    # PORTADA
    h1 = doc.add_heading("🦅 RESUMEN GLOBAL EQUIPO", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1.runs[0].font.color.rgb = RGBColor(0, 51, 102)
    
    p = doc.add_paragraph(f"Reporte: {fname.replace('.xlsx', '')}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    t = doc.add_table(rows=1, cols=3)
    t.style = 'Table Grid'
    hdr = t.rows[0].cells
    hdr[0].text = "METRICA"
    hdr[1].text = "PROM SEMANA"
    hdr[2].text = "PROM ANUAL"
    
    keys = ['tot_tiempo', 'tot_dist', 'tot_elev', 'cv', 'nat_tiempo', 'bike_tiempo', 'run_tiempo']
    for k in keys:
        if not data: break
        m = data[0]['metrics'][k]['meta']
        r = t.add_row().cells
        r[0].text = m['lbl']
        r[1].text = f"{fmt_val(team_avg.get(k), m['t'])} {m['u']}"
        r[2].text = f"{fmt_val(hist_avg.get(k), m['t'])} {m['u']}"

    doc.add_page_break()

    # FICHAS
    for s in doc.sections: 
        s.top_margin = Cm(1.27)
        s.bottom_margin = Cm(1.27)
    
    for i, d in enumerate(data):
        if i > 0: doc.add_page_break()
        
        h = doc.add_heading(level=1)
        run = h.add_run(f"🦅 {d['name']}")
        run.font.color.rgb = RGBColor(0, 51, 102)
        run.font.bold = True
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("─" * 40).alignment = WD_ALIGN_PARAGRAPH.CENTER

        m = d['metrics']
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        t_val = fmt_val(m['tot_tiempo']['val'],'tiempo')
        d_val = fmt_val(m['tot_dist']['val'],'float')
        
        p.add_run(f"⏱️ {t_val} | 📏 {d_val} km").bold = True

        # TABLAS
        def crear_tabla(titulo, keys_dep):
            act = False
            for k in keys_dep:
                it = m[k]
                if it['meta']['t']=='tiempo' and it['val'].total_seconds()>0: act=True
                elif it['meta']['t']!='tiempo' and it['val']>0: act=True
            
            p_tit = doc.add_paragraph()
            tr = p_tit.add_run(titulo)
            tr.bold = True
            tr.font.color.rgb = RGBColor(0, 51, 102)
            
            if not act: 
                p_tit.add_run(" (Sin actividad)").font.color.rgb = RGBColor(150,150,150)
                return

            tb = doc.add_table(rows=1, cols=4)
            hd = tb.rows[0].cells
            hd[0].text="Métrica"; hd[1].text="Dato"; hd[2].text="Vs Eq"; hd[3].text="Vs Anual"
            
            for k in keys_dep:
                item = m[k]; meta = item['meta']
                val = item['val']; avg = item['avg']; hval = item['hist']
                
                if (meta['t']=='tiempo' and val.total_seconds()==0): continue
                if (meta['t']!='tiempo' and val==0): continue
                
                row = tb.add_row().cells
                row[0].text = meta['lbl']
                row[1].text = f"{fmt_val(val, meta['t'])}{meta['u']}"
                
                if avg:
                    if meta['t']=='tiempo': ok = (val-avg).total_seconds()>=0
                    else: ok = (val-avg)>=0
                    if 'Ritmo' in meta['lbl']: ok = not ok
                    row[2].text = "+" if ok else "-"
                else: row[2].text = "-"
                
                if hval:
                    if meta['t']=='tiempo': ok = (val-hval).total_seconds()>=0
                    else: ok = (val-hval)>=0
                    if 'Ritmo' in meta['lbl']: ok = not ok
                    row[3].text = "+" if ok else "-"
                else: row[3].text = "New"
            doc.add_paragraph("")

        crear_tabla("🏊 NATACIÓN", ['nat_tiempo','nat_dist','nat_ritmo'])
        crear_tabla("🚴 CICLISMO", ['bike_tiempo','bike_dist','bike_elev','bike_vel'])
        crear_tabla("🏃 TROTE", ['run_tiempo','run_dist','run_elev','run_ritmo'])

        doc.add_paragraph("─" * 40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ins = doc.add_paragraph()
        p_ins.add_run("💡 Insight: ").bold = True
        p_ins.add_run("Constancia es progreso.").italic = True

    bio = io.BytesIO()
    doc.save(bio); bio.seek(0)
    return bio

# --- 6. INTERFAZ ---
with st.sidebar:
    st.header("📂 Cargar Datos")
    f_hist = st.file_uploader("1. Histórico", type="xlsx")
    f_sem = st.file_uploader("2. Semana", type="xlsx")

if f_hist and f_sem:
    if st.button("▶️ GENERAR REPORTE", type="primary"):
        with st.spinner("Procesando..."):
            try:
                datos, avs, avh = procesar_datos(f_hist, f_sem)
                st.success(f"✅ ¡Éxito! {len(datos)} atletas.")
                
                doc_final = generar_word_v26(datos, f_sem.name, avs, avh)
                
                st.download_button(
                    label="📥 Descargar Reporte (.docx)",
                    data=doc_final,
                    file_name=f"Reporte_Athlos_{f_sem.name.replace('.xlsx','')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Error: {e}")