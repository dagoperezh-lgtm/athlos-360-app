import streamlit as st
import pandas as pd
import io
import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- TUS ENLACES CONFIGURADOS ---
URL_HISTORICO = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/00%20Estadi%CC%81sticas%20TYM_ACTUALIZADO_V21%20(1).xlsx"
URL_SEMANA    = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/06%20Sem%20(tst).xlsx"

st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold; background-color: #003366; color: white;}
    h1, h2, h3 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES BASE (MOTOR V25 RECUPERADO) ---
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
        # MÉTRICAS COMPLETAS V25
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

        avgs_club = {}
        for k, m in METRICAS.items():
            if m['col'] in df_sem.columns:
                vals = df_sem[m['col']].apply(lambda x: clean_time(x) if m['t']=='tiempo' else clean_float(x))
                v = vals[vals > (pd.Timedelta(0) if m['t']=='tiempo' else 0)]
                avgs_club[k] = v.mean() if not v.empty else (pd.Timedelta(0) if m['t']=='tiempo' else 0)
            else: avgs_club[k] = None

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

# --- GENERADOR WORD (LÓGICA DETALLADA RECUPERADA) ---
def agregar_tabla_deporte(doc, m, titulo, keys_dep):
    act = False
    for k in keys_dep:
        if m[k]['meta']['t']=='tiempo' and m[k]['val'].total_seconds()>0: act=True
        elif m[k]['meta']['t']!='tiempo' and m[k]['val']>0: act=True
    
    p_tit = doc.add_paragraph()
    tr = p_tit.add_run(titulo); tr.bold = True; tr.font.color.rgb = RGBColor(0, 51, 102)
    if not act: 
        p_tit.add_run(" (Sin actividad)").font.color.rgb = RGBColor(150,150,150)
        return

    tb = doc.add_table(rows=1, cols=4); tb.autofit = True
    hd = tb.rows[0].cells
    hd[0].text="Métrica"; hd[1].text="Dato"; hd[2].text="Vs Eq"; hd[3].text="Vs Hist"
    
    for k in keys_dep:
        item = m[k]; meta = item['meta']; val = item['val']; avg = item['avg']; hval = item['hist']
        if (meta['t']=='tiempo' and val.total_seconds()==0) or (meta['t']!='tiempo' and val==0): continue
        
        row = tb.add_row().cells
        row[0].text = meta['lbl']
        row[1].text = f"{fmt_val(val, meta['t'])}{meta['u']}"
        
        # Vs Equipo (Cálculo Detallado)
        pe = row[2].paragraphs[0]
        if avg:
            if meta['t']=='tiempo': 
                diff = val - avg
                ok = diff.total_seconds() >= 0
                txt = f"{'+' if ok else '-'}{fmt_val(abs(diff), 'tiempo')}"
            else:
                diff = val - avg
                ok = diff >= 0
                txt = f"{'+' if ok else '-'}{fmt_val(abs(diff), 'float')}"
            
            if 'Ritmo' in meta['lbl']: ok = not ok
            run = pe.add_run(txt)
            run.font.color.rgb = RGBColor(0, 100, 0) if ok else RGBColor(180, 0, 0)
        else: pe.text = "-"

        # Vs Histórico (Cálculo Detallado)
        ph = row[3].paragraphs[0]
        if hval:
            if meta['t']=='tiempo': 
                diff = val - hval
                ok = diff.total_seconds() >= 0
                txt = f"{'+' if ok else '-'}{fmt_val(abs(diff), 'tiempo')}"
            else:
                diff = val - hval
                ok = diff >= 0
                txt = f"{'+' if ok else '-'}{fmt_val(abs(diff), 'float')}"
            
            if 'Ritmo' in meta['lbl']: ok = not ok
            run = ph.add_run(txt)
            run.font.color.rgb = RGBColor(0, 100, 0) if ok else RGBColor(180, 0, 0)
        else: ph.add_run("New").font.color.rgb = RGBColor(0, 0, 128)
        
    doc.add_paragraph("")

def generar_word_v31(data, team_avg, hist_avg):
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
        doc.add_paragraph("─"*40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        m = d['metrics']
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"⏱️ {fmt_val(m['tot_tiempo']['val'],'tiempo')} | 📏 {fmt_val(m['tot_dist']['val'],'float')} km").bold=True
        
        agregar_tabla_deporte(doc, m, "🏊 NATACIÓN", ['nat_tiempo','nat_dist','nat_ritmo'])
        agregar_tabla_deporte(doc, m, "🚴 CICLISMO", ['bike_tiempo','bike_dist','bike_elev','bike_vel'])
        agregar_tabla_deporte(doc, m, "🏃 TROTE", ['run_tiempo','run_dist','run_elev','run_ritmo'])
        
        doc.add_paragraph("─"*40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("💡 Insight: La consistencia es el camino al éxito.").italic = True
        if d != data[-1]: doc.add_page_break()

    bio = io.BytesIO()
    doc.save(bio); bio.seek(0)
    return bio

# --- INTERFAZ ---
st.title("🦅 Athlos 360")
st.caption("Panel de Control - V31 Full Suite")

if st.button("🔄 Refrescar Datos"):
    st.cache_data.clear()
    st.experimental_rerun()

with st.spinner("Cargando desde GitHub..."):
    df_s, dfs_h, err = cargar_datos_github(URL_HISTORICO, URL_SEMANA)

if err:
    st.error(f"Error: {err}")
else:
    datos, avs, avh, err_proc = procesar_logica(df_s, dfs_h)
    
    if err_proc:
        st.error(f"Error lógico: {err_proc}")
    else:
        tab1, tab2 = st.tabs(["📊 Dashboard Detallado", "📄 Reporte Ejecutivo"])
        
        with tab1:
            st.metric("Tiempo Total Equipo", fmt_val(avs['tot_tiempo'], 'tiempo'))
            sel = st.selectbox("Seleccionar Atleta:", [d['name'] for d in datos])
            atleta = next((d for d in datos if d['name'] == sel), None)
            
            if atleta:
                m = atleta['metrics']
                # AQUÍ MOSTRAMOS TODO EN PANTALLA TAMBIÉN
                st.markdown(f"### Detalles de {atleta['name']}")
                
                with st.expander("🏊 NATACIÓN", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tiempo", fmt_val(m['nat_tiempo']['val'], 'tiempo'))
                    c2.metric("Distancia", fmt_val(m['nat_dist']['val'], 'float') + " km")
                    c3.metric("Ritmo", fmt_val(m['nat_ritmo']['val'], 'tiempo') + "/100m")

                with st.expander("🚴 CICLISMO", expanded=True):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tiempo", fmt_val(m['bike_tiempo']['val'], 'tiempo'))
                    c2.metric("Distancia", fmt_val(m['bike_dist']['val'], 'float') + " km")
                    c3.metric("Desnivel", fmt_val(m['bike_elev']['val'], 'float') + " m")
                    c4.metric("Velocidad", fmt_val(m['bike_vel']['val'], 'float') + " km/h")

                with st.expander("🏃 TROTE", expanded=True):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tiempo", fmt_val(m['run_tiempo']['val'], 'tiempo'))
                    c2.metric("Distancia", fmt_val(m['run_dist']['val'], 'float') + " km")
                    c3.metric("Desnivel", fmt_val(m['run_elev']['val'], 'float') + " m")
                    c4.metric("Ritmo", fmt_val(m['run_ritmo']['val'], 'tiempo') + "/km")

        with tab2:
            st.success("✅ Datos procesados. Listo para generar informe detallado.")
            if st.button("Descargar Reporte Word (V31)", type="primary"):
                doc_io = generar_word_v31(datos, avs, avh)
                st.download_button("📥 Descargar .DOCX", doc_io, "Reporte_Athlos_V31.docx")
