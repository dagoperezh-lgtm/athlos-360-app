import streamlit as st
import pandas as pd
import io
import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- TUS ENLACES DE GITHUB ---
URL_HISTORICO = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/00%20Estadi%CC%81sticas%20TYM_ACTUALIZADO_V21%20(1).xlsx"
URL_SEMANA    = "https://raw.githubusercontent.com/dagoperezh-lgtm/athlos-360-app/main/06%20Sem%20(tst).xlsx"

st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #f4f6f9;}
    h1, h2, h3 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 1. MOTOR MATEMÁTICO (Lógica V25 - Precisión Total)
# =============================================================================

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

def fmt_time(td):
    if not isinstance(td, pd.Timedelta) or td.total_seconds() == 0: return "-"
    total_s = int(abs(td.total_seconds()))
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    if h > 0: return f"{h}h {m}m"
    return f"{m}m {s}s"

def fmt_decimal(val):
    if val == 0: return "-"
    return f"{val:.1f}"

def get_comparison_data(val, avg, is_time, invert_logic=False):
    """
    Retorna: (Diferencia Numérica, Texto Formateado, Color)
    Color: 'green' (bueno), 'red' (malo), 'grey' (neutro/sin datos)
    """
    if not avg or (is_time and avg.total_seconds() == 0) or (not is_time and avg == 0):
        return None, "-", "grey"
    
    diff = val - avg
    # Determinar si es positivo matemáticamente
    is_positive = diff.total_seconds() >= 0 if is_time else diff >= 0
    
    # Texto
    sign = "+" if is_positive else "-"
    if is_time:
        txt = f"{sign}{fmt_time(abs(diff))}"
    else:
        txt = f"{sign}{fmt_decimal(abs(diff))}"

    # Lógica Semáforo (V25)
    # Normal: Mayor es mejor (+) -> Verde
    # Invertido (Ritmo): Menor es mejor (-) -> Verde
    is_good = is_positive
    if invert_logic:
        is_good = not is_positive

    color = "green" if is_good else "red"
    return diff, txt, color

@st.cache_data(ttl=600)
def cargar_y_procesar(url_h, url_s):
    try:
        df_sem = pd.read_excel(url_s, engine='openpyxl')
        df_sem.columns = [str(c).strip() for c in df_sem.columns]
        xls = pd.ExcelFile(url_h, engine='openpyxl')
        dfs_hist = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}

        # Configuración de Métricas V25
        M = {
            'tot_tiempo': {'c': 'Tiempo Total (hh:mm:ss)', 'h': 'Total', 't': 'time', 'l': 'Tiempo Total', 'u': '', 'inv': False},
            'tot_dist':   {'c': 'Distancia Total (km)', 'h': 'Distancia Total', 't': 'float', 'l': 'Distancia Total', 'u': 'km', 'inv': False},
            'tot_elev':   {'c': 'Altimetría Total (m)', 'h': 'Altimetría', 't': 'float', 'l': 'Desnivel Total', 'u': 'm', 'inv': False},
            'cv':         {'c': 'CV (Equilibrio)', 'h': 'CV', 't': 'float', 'l': 'Consistencia', 'u': '', 'inv': False},
            
            'nat_tiempo': {'c': 'Nat: Tiempo (hh:mm:ss)', 'h': 'Natación', 't': 'time', 'l': 'Tiempo', 'u': '', 'inv': False},
            'nat_dist':   {'c': 'Nat: Distancia (km)', 'h': 'Nat Distancia', 't': 'float', 'l': 'Distancia', 'u': 'km', 'inv': False},
            'nat_ritmo':  {'c': 'Nat: Ritmo (min/100m)', 'h': 'Nat Ritmo', 't': 'time', 'l': 'Ritmo', 'u': '/100m', 'inv': True},
            
            'bike_tiempo': {'c': 'Ciclismo: Tiempo (hh:mm:ss)', 'h': 'Ciclismo', 't': 'time', 'l': 'Tiempo', 'u': '', 'inv': False},
            'bike_dist':   {'c': 'Ciclismo: Distancia (km)', 'h': 'Ciclismo Distancia', 't': 'float', 'l': 'Distancia', 'u': 'km', 'inv': False},
            'bike_elev':   {'c': 'Ciclismo: KOM/Desnivel (m)', 'h': 'Ciclismo Desnivel', 't': 'float', 'l': 'Desnivel', 'u': 'm', 'inv': False},
            'bike_vel':    {'c': 'Ciclismo: Vel. Media (km/h)', 'h': 'Ciclismo Velocidad', 't': 'float', 'l': 'Velocidad', 'u': 'km/h', 'inv': False},
            
            'run_tiempo': {'c': 'Trote: Tiempo (hh:mm:ss)', 'h': 'Trote', 't': 'time', 'l': 'Tiempo', 'u': '', 'inv': False},
            'run_dist':   {'c': 'Trote: Distancia (km)', 'h': 'Trote Distancia', 't': 'float', 'l': 'Distancia', 'u': 'km', 'inv': False},
            'run_elev':   {'c': 'Trote: KOM/Desnivel (m)', 'h': 'Trote Desnivel', 't': 'float', 'l': 'Desnivel', 'u': 'm', 'inv': False},
            'run_ritmo':  {'c': 'Trote: Ritmo (min/km)', 'h': 'Trote Ritmo', 't': 'time', 'l': 'Ritmo', 'u': '/km', 'inv': True},
        }

        # 1. Promedios Club
        avgs_team = {}
        for k, meta in M.items():
            if meta['c'] in df_sem.columns:
                raw = df_sem[meta['c']].apply(lambda x: clean_time(x) if meta['t']=='time' else clean_float(x))
                if meta['t'] == 'time':
                    valid = raw[raw > pd.Timedelta(0)]
                    avgs_team[k] = valid.mean() if not valid.empty else pd.Timedelta(0)
                else:
                    valid = raw[raw > 0]
                    avgs_team[k] = valid.mean() if not valid.empty else 0.0
            else: avgs_team[k] = None

        # 2. Promedios Históricos Globales
        avgs_hist_global = {}
        for k, meta in M.items():
            target_s = next((s for s in dfs_hist if meta['h'].lower() in s.lower()), None)
            if target_s:
                dfh = dfs_hist[target_s]
                cols = [c for c in dfh.columns if 'sem' in c.lower()]
                vals = []
                for c in cols:
                    raw = dfh[c].apply(lambda x: clean_time(x) if meta['t']=='time' else clean_float(x))
                    if meta['t']=='time': vals.extend([x.total_seconds() for x in raw if x.total_seconds()>0])
                    else: vals.extend([x for x in raw if x>0])
                
                if vals:
                    if meta['t']=='time': avgs_hist_global[k] = pd.Timedelta(seconds=sum(vals)/len(vals))
                    else: avgs_hist_global[k] = sum(vals)/len(vals)
                else: avgs_hist_global[k] = None
            else: avgs_hist_global[k] = None

        # 3. Procesar Atletas
        atletas_procesados = []
        c_nom = next((c for c in df_sem.columns if c in ['Deportista', 'Nombre']), None)
        
        if c_nom:
            for _, row in df_sem.iterrows():
                nom = str(row[c_nom]).strip()
                if nom.lower() in ['nan', 'totales', 'promedio']: continue
                
                atleta_res = {'name': nom, 'data': {}}
                
                for k, meta in M.items():
                    val = clean_time(row.get(meta['c'])) if meta['t']=='time' else clean_float(row.get(meta['c']))
                    val_fmt = (fmt_time(val) if meta['t']=='time' else fmt_decimal(val)) + (" " + meta['u'] if val!=0 and meta['t']!='time' else "")
                    
                    # Histórico Personal
                    hist_val = None
                    target_s = next((s for s in dfs_hist if meta['h'].lower() in s.lower()), None)
                    if target_s:
                        dfh = dfs_hist[target_s]
                        cnh = next((c for c in dfh.columns if c.lower() in ['nombre','deportista']), None)
                        if cnh:
                            rh = dfh[dfh[cnh].astype(str).str.lower().str.strip() == nom.lower()]
                            if not rh.empty:
                                cols = [c for c in dfh.columns if 'sem' in c.lower()]
                                vals_h = [clean_time(rh.iloc[0][c]) if meta['t']=='time' else clean_float(rh.iloc[0][c]) for c in cols]
                                if meta['t']=='time':
                                    valid = [x.total_seconds() for x in vals_h if x.total_seconds()>0]
                                    if valid: hist_val = pd.Timedelta(seconds=sum(valid)/len(valid))
                                else:
                                    valid = [x for x in vals_h if x>0]
                                    if valid: hist_val = sum(valid)/len(valid)

                    _, txt_eq, col_eq = get_comparison_data(val, avgs_team.get(k), meta['t']=='time', meta['inv'])
                    _, txt_hist, col_hist = get_comparison_data(val, hist_val, meta['t']=='time', meta['inv'])
                    
                    if not hist_val: 
                        txt_hist = "New"
                        col_hist = "blue"

                    atleta_res['data'][k] = {
                        'val': val, 'fmt': val_fmt, 
                        'vs_eq': txt_eq, 'col_eq': col_eq,
                        'vs_hist': txt_hist, 'col_hist': col_hist,
                        'meta': meta
                    }
                
                atletas_procesados.append(atleta_res)

        return atletas_procesados, avgs_team, avgs_hist_global, None

    except Exception as e:
        return [], {}, {}, str(e)

# =============================================================================
# 2. GENERADOR WORD (Fiel a la V25)
# =============================================================================
def generar_word_v33(datos, avs_team, avs_hist):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10)
    
    h1 = doc.add_heading("🦅 RESUMEN GLOBAL EQUIPO", 0)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER; h1.runs[0].font.color.rgb = RGBColor(0, 51, 102)
    doc.add_paragraph("Reporte V33 - Análisis Completo").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Tabla Resumen
    t = doc.add_table(rows=1, cols=3); t.style = 'Table Grid'
    hdr = t.rows[0].cells; hdr[0].text="MÉTRICA"; hdr[1].text="SEM ACTUAL"; hdr[2].text="HIST ANUAL"
    
    keys_res = ['tot_tiempo', 'tot_dist', 'tot_elev', 'cv']
    for k in keys_res:
        if not datos: break
        meta = datos[0]['data'][k]['meta']
        r = t.add_row().cells
        r[0].text = meta['l']
        
        val_team = avs_team.get(k)
        r[1].text = fmt_time(val_team) if meta['t']=='time' else fmt_decimal(val_team)
        val_hist = avs_hist.get(k)
        r[2].text = fmt_time(val_hist) if meta['t']=='time' else fmt_decimal(val_hist)
    doc.add_page_break()

    # Fichas
    for d in datos:
        doc.add_heading(f"🦅 {d['name']}", 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("─"*40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        m = d['data']
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"⏱️ {m['tot_tiempo']['fmt']} | 📏 {m['tot_dist']['fmt']} km | ⛰️ {m['tot_elev']['fmt']} m").bold = True
        
        def tabla_bloque(titulo, keys):
            has_act = False
            for k in keys:
                if m[k]['meta']['t']=='time' and m[k]['val'].total_seconds()>0: has_act=True
                elif m[k]['meta']['t']!='time' and m[k]['val']>0: has_act=True
            
            p_tit = doc.add_paragraph(); r_tit = p_tit.add_run(titulo); r_tit.bold=True; r_tit.font.color.rgb = RGBColor(0,51,102)
            if not has_act: p_tit.add_run(" (Sin actividad)").font.color.rgb = RGBColor(150,150,150); return

            tb = doc.add_table(rows=1, cols=4); tb.autofit = True
            hd = tb.rows[0].cells
            hd[0].text="Métrica"; hd[1].text="Dato"; hd[2].text="Vs Equipo"; hd[3].text="Vs Histórico"
            
            for k in keys:
                item = m[k]
                if (item['meta']['t']=='time' and item['val'].total_seconds()==0) or (item['meta']['t']!='time' and item['val']==0): continue
                
                row = tb.add_row().cells
                row[0].text = item['meta']['l']
                row[1].text = item['fmt']
                
                req = row[2].paragraphs[0].add_run(item['vs_eq'])
                req.font.color.rgb = RGBColor(0,100,0) if item['col_eq']=='green' else (RGBColor(180,0,0) if item['col_eq']=='red' else RGBColor(100,100,100))
                
                rhist = row[3].paragraphs[0].add_run(item['vs_hist'])
                rhist.font.color.rgb = RGBColor(0,100,0) if item['col_hist']=='green' else (RGBColor(180,0,0) if item['col_hist']=='red' else RGBColor(0,0,128))
            doc.add_paragraph("")

        tabla_bloque("🏊 NATACIÓN", ['nat_tiempo','nat_dist','nat_ritmo'])
        tabla_bloque("🚴 CICLISMO", ['bike_tiempo','bike_dist','bike_elev','bike_vel'])
        tabla_bloque("🏃 TROTE", ['run_tiempo','run_dist','run_elev','run_ritmo'])
        
        pcv = doc.add_paragraph()
        pcv.add_run(f"⚖️ Consistencia: {m['cv']['fmt']} ").bold=True
        pcv.add_run(m['cv']['vs_eq']).font.color.rgb = RGBColor(0,100,0) if m['cv']['col_eq']=='green' else RGBColor(180,0,0)
        
        doc.add_paragraph("─"*40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        if d != datos[-1]: doc.add_page_break()

    bio = io.BytesIO()
    doc.save(bio); bio.seek(0)
    return bio

# =============================================================================
# 3. DASHBOARD WEB (NUEVA ESTRUCTURA TABULAR CLARA)
# =============================================================================
st.title("🦅 Athlos 360")
st.caption("Dashboard de Alto Rendimiento - V33")

if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.experimental_rerun()

with st.spinner("Procesando datos..."):
    datos, avs_team, avs_hist, err = cargar_y_procesar(URL_HISTORICO, URL_SEMANA)

if err:
    st.error(f"Error: {err}")
else:
    tab1, tab2 = st.tabs(["📊 Dashboard Atleta", "📄 Descargas"])
    
    with tab1:
        nombres = [d['name'] for d in datos]
        sel = st.selectbox("Buscar Atleta:", nombres)
        atleta = next((d for d in datos if d['name'] == sel), None)
        
        if atleta:
            m = atleta['data']
            
            # KPI Header
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Tiempo Total", m['tot_tiempo']['fmt'])
            k2.metric("Distancia", m['tot_dist']['fmt'])
            k3.metric("Desnivel", m['tot_elev']['fmt'])
            k4.metric("Consistencia", m['cv']['fmt'])
            st.divider()

            # FUNCIÓN PARA PINTAR TABLAS EN PANTALLA (NO TARJETAS CONFUSAS)
            def render_table(title, keys):
                st.markdown(f"#### {title}")
                # Construimos un mini dataframe para mostrar limpio
                rows = []
                for k in keys:
                    item = m[k]
                    # Solo mostrar si hay dato
                    if (item['meta']['t']=='time' and item['val'].total_seconds()==0) or (item['meta']['t']!='time' and item['val']==0): continue
                    
                    rows.append({
                        "Métrica": item['meta']['l'],
                        "Dato": item['fmt'],
                        "Vs Equipo": item['vs_eq'],
                        "Vs Histórico": item['vs_hist']
                    })
                
                if rows:
                    df_show = pd.DataFrame(rows)
                    st.table(df_show) # st.table se ve mejor que st.dataframe para esto
                else:
                    st.caption("Sin actividad registrada.")

            c1, c2 = st.columns(2)
            with c1: render_table("🏊 Natación", ['nat_tiempo','nat_dist','nat_ritmo'])
            with c2: render_table("🚴 Ciclismo", ['bike_tiempo','bike_dist','bike_elev','bike_vel'])
            
            render_table("🏃 Trote", ['run_tiempo','run_dist','run_elev','run_ritmo'])

    with tab2:
        st.success("✅ Datos listos.")
        if st.button("Generar Reporte Word (V33)", type="primary"):
            doc_io = generar_word_v33(datos, avs_team, avs_hist)
            st.download_button("📥 Descargar .DOCX", doc_io, "Reporte_Athlos_V33.docx")
