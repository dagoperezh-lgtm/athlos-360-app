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

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold; background-color: #003366; color: white;}
    .stButton>button:hover {background-color: #004080; color: white;}
    h1, h2, h3 {color: #003366;}
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES DE CARGA (CON CACHÉ) ---
# Usamos caché para que no descargue los archivos cada vez que tocas un botón
@st.cache_data(ttl=600)  # Se actualiza cada 10 minutos automáticamente
def cargar_datos_github(url_hist, url_sem):
    try:
        # Leer directamente desde la URL
        df_sem = pd.read_excel(url_sem, engine='openpyxl')
        df_sem.columns = [str(c).strip() for c in df_sem.columns]
        
        xls = pd.ExcelFile(url_hist, engine='openpyxl')
        dfs_hist = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}
        
        return df_sem, dfs_hist, None
    except Exception as e:
        return None, None, str(e)

# --- 3. FUNCIONES DE PROCESAMIENTO ---
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
    # Definición de Métricas
    METRICAS = {
        'tot_tiempo': {'col': 'Tiempo Total (hh:mm:ss)', 'hist': 'Total', 't': 'tiempo', 'lbl': 'Tiempo Total', 'u': ''},
        'tot_dist': {'col': 'Distancia Total (km)', 'hist': 'Distancia Total', 't': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'tot_elev': {'col': 'Altimetría Total (m)', 'hist': 'Altimetría', 't': 'float', 'lbl': 'Desnivel', 'u': 'm'},
        'cv': {'col': 'CV (Equilibrio)', 'hist': 'CV', 't': 'float', 'lbl': 'Consistencia', 'u': ''},
        'nat_tiempo': {'col': 'Nat: Tiempo (hh:mm:ss)', 'hist': 'Natación', 't': 'tiempo', 'lbl': 'Natación', 'u': ''},
        'bike_tiempo': {'col': 'Ciclismo: Tiempo (hh:mm:ss)', 'hist': 'Ciclismo', 't': 'tiempo', 'lbl': 'Ciclismo', 'u': ''},
        'run_tiempo': {'col': 'Trote: Tiempo (hh:mm:ss)', 'hist': 'Trote', 't': 'tiempo', 'lbl': 'Trote', 'u': ''}
    }

    # 1. Promedios Club
    avgs_club = {}
    for k, m in METRICAS.items():
        if m['col'] in df_sem.columns:
            vals = df_sem[m['col']].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
            v = vals[vals > (pd.Timedelta(0) if m['t']=='tiempo' else 0)]
            avgs_club[k] = v.mean() if not v.empty else (pd.Timedelta(0) if m['t']=='tiempo' else 0)
        else: avgs_club[k] = None

    # 2. Históricos Globales
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

    # 3. Atletas Individuales
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
        
    return lista_final, avgs_club, avgs_hist_global

def generar_word_v27(data, team_avg, hist_avg):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10.5)
    
    h1 = doc.add_heading("🦅 RESUMEN GLOBAL EQUIPO", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER; h1.runs[0].font.color.rgb = RGBColor(0, 51, 102)
    doc.add_paragraph(f"Reporte Automático Semanal").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
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
        doc.add_paragraph("─"*40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        m = d['metrics']
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"⏱️ {fmt_val(m['tot_tiempo']['val'],'tiempo')} | 📏 {fmt_val(m['tot_dist']['val'],'float')} km").bold=True
        
        tb = doc.add_table(rows=1, cols=4); tb.autofit = True
        hd = tb.rows[0].cells; hd[0].text="Métrica"; hd[1].text="Dato"; hd[2].text="Vs Eq"; hd[3].text="Vs Hist"
        
        for k, item in m.items():
            meta = item['meta']; val = item['val']; avg = item['avg']; hval = item['hist']
            if (meta['t']=='tiempo' and val.total_seconds()==0) or (meta['t']!='tiempo' and val==0): continue
            
            row = tb.add_row().cells
            row[0].text = meta['lbl']
            row[1].text = f"{fmt_val(val, meta['t'])}{meta['u']}"
            
            if avg:
                ok = (val-avg).total_seconds()>=0 if meta['t']=='tiempo' else (val-avg)>=0
                row[2].text = "+" if ok else "-"
            else: row[2].text = "-"
            
            if hval:
                ok = (val-hval).total_seconds()>=0 if meta['t']=='tiempo' else (val-hval)>=0
                row[3].text = "+" if ok else "-"
            else: row[3].text = "New"
        
        doc.add_paragraph("")
        if d != data[-1]: doc.add_page_break()

    bio = io.BytesIO()
    doc.save(bio); bio.seek(0)
    return bio

# --- 4. INTERFAZ PRINCIPAL (SIN SIDEBAR) ---

st.title("🦅 Athlos 360")
st.caption("Panel de Control del Club TYM")

# Verificación de Links
if "PEGAR_AQUI" in URL_HISTORICO or "PEGAR_AQUI" in URL_SEMANA:
    st.warning("⚠️ Configuración Incompleta: Por favor edita 'app.py' en GitHub y pega los links RAW de tus archivos.")
else:
    # Botón para forzar recarga (limpiar caché)
    if st.button("🔄 Actualizar Datos desde GitHub"):
        st.cache_data.clear()
        st.experimental_rerun()

    # Carga de Datos Automática
    with st.spinner("Conectando con la base de datos..."):
        df_s, dfs_h, err = cargar_datos_github(URL_HISTORICO, URL_SEMANA)

    if err:
        st.error(f"❌ Error de Conexión: {err}")
        st.info("Asegúrate de que los links sean 'Raw' y que el repositorio sea 'Public'.")
    else:
        # Procesar
        datos, avs, avh, err_proc = procesar_logica(df_s, dfs_h)
        
        if err_proc:
            st.error(f"Error al procesar datos: {err_proc}")
        else:
            # --- PESTAÑAS ---
            tab1, tab2 = st.tabs(["📊 Dashboard Atletas", "📄 Reporte Mensual"])
            
            with tab1:
                st.subheader("Resumen Semanal")
                
                # KPIs
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Tiempo Equipo", fmt_val(avs['tot_tiempo'], 'tiempo'))
                c2.metric("Distancia Equipo", fmt_val(avs['tot_dist'], 'float') + " km")
                c3.metric("Desnivel Equipo", fmt_val(avs['tot_elev'], 'float') + " m")
                c4.metric("Consistencia (CV)", fmt_val(avs['cv'], 'float'))
                
                st.markdown("---")
                
                # Buscador
                nombres = [d['name'] for d in datos]
                sel = st.selectbox("👤 Selecciona un Atleta:", nombres)
                
                # Detalle Atleta
                atleta = next((d for d in datos if d['name'] == sel), None)
                if atleta:
                    m = atleta['metrics']
                    st.info(f"Mostrando datos de: **{atleta['name']}**")
                    
                    co1, co2, co3 = st.columns(3)
                    with co1:
                        st.write("🏊 **Natación**")
                        st.write(f"⏱️ {fmt_val(m['nat_tiempo']['val'], 'tiempo')}")
                    with co2:
                        st.write("🚴 **Ciclismo**")
                        st.write(f"⏱️ {fmt_val(m['bike_tiempo']['val'], 'tiempo')}")
                    with co3:
                        st.write("🏃 **Trote**")
                        st.write(f"⏱️ {fmt_val(m['run_tiempo']['val'], 'tiempo')}")

            with tab2:
                st.subheader("Generación de Documentos")
                st.write("Genera el reporte oficial en Word basado en los datos actuales de GitHub.")
                
                if st.button("📄 Generar Word Ejecutivo", type="primary"):
                    doc_io = generar_word_v27(datos, avs, avh)
                    st.download_button(
                        "📥 Descargar .DOCX",
                        doc_io,
                        "Reporte_Athlos_Auto.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
