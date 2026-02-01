import streamlit as st
import pandas as pd
import io
import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- TUS ENLACES DE GITHUB (Ya configurados) ---
URL_HISTORICO = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/00%20Estadi%CC%81sticas%20TYM_ACTUALIZADO_V21%20(1).xlsx"
URL_SEMANA    = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/06%20Sem%20(tst).xlsx"

st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main {background-color: #f4f6f9;}
    h1 {color: #003366;}
    div.stMetric {background-color: #ffffff; padding: 10px; border-radius: 5px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);}
    </style>
""", unsafe_allow_html=True)

# --- 1. FUNCIONES AUXILIARES (MATEMÁTICA V25) ---
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
        s = int(abs(val.total_seconds()))
        h, rem = divmod(s, 3600)
        m, s = divmod(rem, 60)
        if h > 0: return f"{h}h {m}m"
        return f"{m}m {s}s"
    else:
        return f"{val:.1f}"

# --- 2. CARGA DE DATOS ---
@st.cache_data(ttl=600)
def cargar_datos(url_h, url_s):
    try:
        df_s = pd.read_excel(url_s, engine='openpyxl')
        df_s.columns = [str(c).strip() for c in df_s.columns]
        xls = pd.ExcelFile(url_h, engine='openpyxl')
        dfs_h = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}
        return df_s, dfs_h, None
    except Exception as e:
        return None, None, str(e)

# --- 3. PROCESAMIENTO LÓGICO (MOTOR V25 COMPLETO) ---
def procesar(df_sem, dfs_hist):
    # Diccionario Maestro de Métricas (No borrar nada)
    METRICAS = {
        'tot_tiempo': {'col': 'Tiempo Total (hh:mm:ss)', 'hist': 'Total', 't': 'tiempo', 'lbl': 'Tiempo Total', 'u': ''},
        'tot_dist': {'col': 'Distancia Total (km)', 'hist': 'Distancia Total', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'tot_elev': {'col': 'Altimetría Total (m)', 'hist': 'Altimetría', 't': 'float', 'lbl': 'Desnivel', 'u': 'm'},
        'cv': {'col': 'CV (Equilibrio)', 'hist': 'CV', 't': 'float', 'lbl': 'Consistencia', 'u': ''},
        
        'nat_tiempo': {'col': 'Nat: Tiempo (hh:mm:ss)', 'hist': 'Natación', 't': 'tiempo', 'lbl': 'Tiempo', 'u': ''},
        'nat_dist': {'col': 'Nat: Distancia (km)', 'hist': 'Nat Distancia', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'nat_ritmo': {'col': 'Nat: Ritmo (min/100m)', 'hist': 'Nat Ritmo', 't': 'tiempo', 'lbl': 'Ritmo', 'u': '/100m'},
        
        'bike_tiempo': {'col': 'Ciclismo: Tiempo (hh:mm:ss)', 'hist': 'Ciclismo', 't': 'tiempo', 'lbl': 'Tiempo', 'u': ''},
        'bike_dist': {'col': 'Ciclismo: Distancia (km)', 'hist': 'Ciclismo Distancia', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'bike_elev': {'col': 'Ciclismo: KOM/Desnivel (m)', 'hist': 'Ciclismo Desnivel', 't': 'float', 'lbl': 'Desnivel', 'u': 'm'},
        'bike_vel': {'col': 'Ciclismo: Vel. Media (km/h)', 'hist': 'Ciclismo Velocidad', 't': 'float', 'lbl': 'Velocidad', 'u': 'km/h'},
        
        'run_tiempo': {'col': 'Trote: Tiempo (hh:mm:ss)', 'hist': 'Trote', 't': 'tiempo', 'lbl': 'Tiempo', 'u': ''},
        'run_dist': {'col': 'Trote: Distancia (km)', 'hist': 'Trote Distancia', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'run_elev': {'col': 'Trote: KOM/Desnivel (m)', 'hist': 'Trote Desnivel', 't': 'float', 'lbl': 'Desnivel', 'u': 'm'},
        'run_ritmo': {'col': 'Trote: Ritmo (min/km)', 'hist': 'Trote Ritmo', 't': 'tiempo', 'lbl': 'Ritmo', 'u': '/km'}
    }

    # 1. Calcular Promedios del Club
    avgs_club = {}
    for k, m in METRICAS.items():
        if m['col'] in df_sem.columns:
            raw = df_sem[m['col']].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
            if m['t']=='tiempo':
                valid = raw[raw > pd.Timedelta(0)]
                avgs_club[k] = valid.mean() if not valid.empty else pd.Timedelta(0)
            else:
                valid = raw[raw > 0]
                avgs_club[k] = valid.mean() if not valid.empty else 0.0
        else: avgs_club[k] = None

    # 2. Calcular Promedios Históricos Globales
    avgs_hist = {}
    for k, m in METRICAS.items():
        target = next((s for s in dfs_hist if m['hist'].lower() in s.lower()), None)
        if target:
            cols = [c for c in dfs_hist[target].columns if 'sem' in c.lower()]
            vals = []
            for c in cols:
                raw = dfs_hist[target][c].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
                if m['t']=='tiempo': vals.extend([x.total_seconds() for x in raw if x.total_seconds()>0])
                else: vals.extend([x for x in raw if x>0])
            if vals:
                if m['t']=='tiempo': avgs_hist[k] = pd.Timedelta(seconds=sum(vals)/len(vals))
                else: avgs_hist[k] = sum(vals)/len(vals)
            else: avgs_hist[k] = None
        else: avgs_hist[k] = None

    # 3. Procesar Atletas Individuales
    data = []
    c_nom = next((c for c in df_sem.columns if c in ['Deportista', 'Nombre']), None)
    if not c_nom: return [], {}, {}

    for _, r in df_sem.iterrows():
        nom = str(r[c_nom]).strip()
        if nom.lower() in ['nan', 'totales', 'promedio']: continue
        
        metrics = {}
        for k, m in METRICAS.items():
            # Valor Actual
            curr = clean_time(r.get(m['col'])) if m['t']=='tiempo' else clean_float(r.get(m['col']))
            
            # Valor Histórico Personal
            hist_personal = None
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
                                if vs: hist_personal = pd.Timedelta(seconds=sum(vs)/len(vs))
                            else:
                                vs = [x for x in vs if x>0]
                                if vs: hist_personal = sum(vs)/len(vs)
            
            metrics[k] = {'val': curr, 'avg': avgs_club.get(k), 'hist': hist_personal, 'meta': m}
        data.append({'name': nom, 'metrics': metrics})
        
    return data, avgs_club, avgs_hist

# --- 4. GENERADOR WORD (LÓGICA COMPARATIVA V25 REINSTAURADA) ---
def generar_word(data, team_avg, hist_avg):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10.5)
    
    # PORTADA
    h1 = doc.add_heading("🦅 RESUMEN GLOBAL EQUIPO", 0)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Reporte Semanal Automático").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    t = doc.add_table(rows=1, cols=3)
    t.style = 'Table Grid'
    hdr = t.rows[0].cells
    hdr[0].text = "METRICA"
    hdr[1].text = "PROM SEMANA"
    hdr[2].text = "PROM ANUAL"
    
    keys = ['tot_tiempo', 'tot_dist', 'tot_elev', 'cv']
    for k in keys:
        m = data[0]['metrics'][k]['meta']
        r = t.add_row().cells
        r[0].text = m['lbl']
        r[1].text = f"{fmt_val(team_avg.get(k), m['t'])} {m['u']}"
        r[2].text = f"{fmt_val(hist_avg.get(k), m['t'])} {m['u']}"
    
    doc.add_page_break()

    # FICHAS ATLETAS
    for i, d in enumerate(data):
        doc.add_heading(f"🦅 {d['name']}", 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("─"*40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        m = d['metrics']
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"⏱️ {fmt_val(m['tot_tiempo']['val'], 'tiempo')} | 📏 {fmt_val(m['tot_dist']['val'], 'float')} km").bold = True
        
        # TABLAS POR DEPORTE (CON COMPARATIVAS REALES)
        def tabla_deporte(titulo, keys):
            # Check actividad
            act = False
            for k in keys:
                val = m[k]['val']
                if m[k]['meta']['t']=='tiempo' and val.total_seconds()>0: act=True
                elif m[k]['meta']['t']!='tiempo' and val>0: act=True
            
            p = doc.add_paragraph()
            p.add_run(titulo).bold = True
            p.add_run(" (Sin actividad)" if not act else "").font.color.rgb = RGBColor(150,150,150)
            
            if not act: return

            tb = doc.add_table(rows=1, cols=4)
            tb.autofit = True
            hd = tb.rows[0].cells
            hd[0].text="Métrica"; hd[1].text="Dato"; hd[2].text="Vs Eq"; hd[3].text="Vs Hist"
            
            for k in keys:
                item = m[k]
                meta = item['meta']
                val = item['val']
                avg = item['avg']
                hist = item['hist']
                
                # Filtrar ceros
                if (meta['t']=='tiempo' and val.total_seconds()==0) or (meta['t']!='tiempo' and val==0): continue
                
                r = tb.add_row().cells
                r[0].text = meta['lbl']
                r[1].text = f"{fmt_val(val, meta['t'])}{meta['u']}"
                
                # Lógica de Comparación (Vs Equipo)
                if avg:
                    if meta['t'] == 'tiempo':
                        diff = val - avg
                        txt = f"{'+' if diff.total_seconds()>=0 else '-'}{fmt_val(abs(diff.total_seconds()), 'float')}" # Simplificado para evitar error timedelta format
                        # Formateo manual bonito para diff tiempo
                        s = int(abs(diff.total_seconds()))
                        txt = f"{'+' if diff.total_seconds()>=0 else '-'}{s//60}m {s%60}s"
                        ok = diff.total_seconds() >= 0
                    else:
                        diff = val - avg
                        txt = f"{diff:+.1f}"
                        ok = diff >= 0
                    
                    if 'Ritmo' in meta['lbl']: ok = not ok # Ritmo menor es mejor
                    
                    run = r[2].paragraphs[0].add_run(txt)
                    run.font.color.rgb = RGBColor(0,100,0) if ok else RGBColor(180,0,0)
                else: r[2].text = "-"

                # Lógica de Comparación (Vs Histórico)
                if hist:
                    if meta['t'] == 'tiempo':
                        diff = val - hist
                        s = int(abs(diff.total_seconds()))
                        txt = f"{'+' if diff.total_seconds()>=0 else '-'}{s//60}m {s%60}s"
                        ok = diff.total_seconds() >= 0
                    else:
                        diff = val - hist
                        txt = f"{diff:+.1f}"
                        ok = diff >= 0
                    
                    if 'Ritmo' in meta['lbl']: ok = not ok
                    
                    run = r[3].paragraphs[0].add_run(txt)
                    run.font.color.rgb = RGBColor(0,100,0) if ok else RGBColor(180,0,0)
                else: 
                    r[3].text = "New"

        tabla_deporte("🏊 NATACIÓN", ['nat_tiempo','nat_dist','nat_ritmo'])
        tabla_deporte("🚴 CICLISMO", ['bike_tiempo','bike_dist','bike_elev','bike_vel'])
        tabla_deporte("🏃 TROTE", ['run_tiempo','run_dist','run_elev','run_ritmo'])
        
        doc.add_paragraph("")
        if i < len(data)-1: doc.add_page_break()

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 5. INTERFAZ WEB ---
st.title("🦅 Athlos 360")
st.caption("Sistema V31: Datos Completos + Comparativas + GitHub Automático")

if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.experimental_rerun()

with st.spinner("Cargando base de datos..."):
    df_s, dfs_h, err = cargar_datos(URL_HISTORICO, URL_SEMANA)

if err:
    st.error(f"Error de conexión: {err}")
else:
    datos, avs, avh = procesar(df_s, dfs_h)
    
    tab1, tab2 = st.tabs(["📊 Dashboard Detallado", "📥 Descargas"])
    
    with tab1:
        # SELECTOR DE ATLETA
        names = [d['name'] for d in datos]
        sel = st.selectbox("Seleccionar Atleta:", names)
        atleta = next((d for d in datos if d['name'] == sel), None)
        
        if atleta:
            m = atleta['metrics']
            
            # KPI PRINCIPALES
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Tiempo Total", fmt_val(m['tot_tiempo']['val'], 'tiempo'))
            k2.metric("Distancia Total", fmt_val(m['tot_dist']['val'], 'float') + " km")
            k3.metric("Desnivel", fmt_val(m['tot_elev']['val'], 'float') + " m")
            k4.metric("Consistencia", fmt_val(m['cv']['val'], 'float'))
            
            st.divider()
            
            # TABLAS DE DETALLE EN PANTALLA (LO QUE FALTABA)
            c_nat, c_bike, c_run = st.columns(3)
            
            with c_nat:
                st.markdown("### 🏊 Natación")
                st.write(f"⏱️ **Tiempo:** {fmt_val(m['nat_tiempo']['val'], 'tiempo')}")
                st.write(f"📏 **Distancia:** {fmt_val(m['nat_dist']['val'], 'float')} km")
                st.write(f"⚡ **Ritmo:** {fmt_val(m['nat_ritmo']['val'], 'tiempo')}/100m")
                
            with c_bike:
                st.markdown("### 🚴 Ciclismo")
                st.write(f"⏱️ **Tiempo:** {fmt_val(m['bike_tiempo']['val'], 'tiempo')}")
                st.write(f"📏 **Distancia:** {fmt_val(m['bike_dist']['val'], 'float')} km")
                st.write(f"⛰️ **Desnivel:** {fmt_val(m['bike_elev']['val'], 'float')} m")
                st.write(f"🚀 **Velocidad:** {fmt_val(m['bike_vel']['val'], 'float')} km/h")
                
            with c_run:
                st.markdown("### 🏃 Trote")
                st.write(f"⏱️ **Tiempo:** {fmt_val(m['run_tiempo']['val'], 'tiempo')}")
                st.write(f"📏 **Distancia:** {fmt_val(m['run_dist']['val'], 'float')} km")
                st.write(f"⛰️ **Desnivel:** {fmt_val(m['run_elev']['val'], 'float')} m")
                st.write(f"⚡ **Ritmo:** {fmt_val(m['run_ritmo']['val'], 'tiempo')}/km")

    with tab2:
        st.write("Generar Reporte Word con comparativas detalladas (Vs Equipo y Vs Histórico).")
        if st.button("📄 Generar Word V31", type="primary"):
            doc_io = generar_word(datos, avs, avh)
            st.download_button("📥 Descargar Reporte Completo", doc_io, "Reporte_Athlos_V31.docx")
