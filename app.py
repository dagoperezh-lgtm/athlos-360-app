import streamlit as st
import pandas as pd
import io
import datetime
import openpyxl
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅", layout="centered")

# Estilos CSS para que se vea profesional
st.markdown("""
    <style>
    .main {background-color: #f0f2f6;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #003366; color: white; font-weight: bold; padding: 10px;}
    .stButton>button:hover {background-color: #004080; color: white;}
    h1 {color: #003366;}
    </style>
""", unsafe_allow_html=True)

st.title("🦅 Athlos 360")
st.markdown("### Generador de Reportes de Alto Rendimiento")
st.write("---")

# --- 2. BARRA LATERAL (CARGA) ---
with st.sidebar:
    st.header("📂 Tus Archivos")
    st.info("Sube aquí los Excel del Club TYM.")
    f_hist = st.file_uploader("1. Histórico Anual", type=["xlsx"])
    f_sem = st.file_uploader("2. Semana Actual", type=["xlsx"])

# --- 3. FUNCIONES DE LIMPIEZA ---
def clean_time(val):
    if pd.isna(val) or val in ['NC', '0', '', 'NAN', '-']: return pd.Timedelta(0)
    s = str(val).strip()
    try:
        if isinstance(val, (datetime.time, datetime.datetime)):
            return pd.Timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
        parts = list(map(int, s.split(':')))
        if len(parts) == 3: return pd.Timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
    except: pass
    return pd.Timedelta(0)

def fmt_val(val, tipo):
    if val is None: return "-"
    if tipo == 'tiempo':
        if val.total_seconds() == 0: return "-"
        s = int(val.total_seconds())
        if s < 3600: return f"{s//60}m {s%60}s"
        return f"{s//3600}h {(s%3600)//60}m"
    else: return f"{val:.1f}" if val > 0 else "-"

# --- 4. LÓGICA DE PROCESAMIENTO ---
def procesar_datos_web(file_hist, file_sem):
    # Leer archivos
    df_sem = pd.read_excel(file_sem, engine='openpyxl')
    df_sem.columns = [str(c).strip() for c in df_sem.columns]
    
    xls = pd.ExcelFile(file_hist, engine='openpyxl')
    dfs_hist = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}

    # Definir Métricas
    METRICAS = {
        'tot_tiempo': {'col': 'Tiempo Total (hh:mm:ss)', 'hist': 'Total', 'tipo': 'tiempo', 'label': 'Tiempo Total', 'unit': ''},
        'tot_dist':   {'col': 'Distancia Total (km)', 'hist': 'Distancia Total', 'tipo': 'float', 'label': 'Distancia Total', 'unit': 'km'},
        'tot_elev':   {'col': 'Altimetría Total (m)', 'hist': 'Altimetría', 'tipo': 'float', 'label': 'Desnivel Total', 'unit': 'm'},
        'cv':         {'col': 'CV (Equilibrio)', 'hist': 'CV', 'tipo': 'float', 'label': 'Consistencia', 'unit': ''},
        'nat_tiempo': {'col': 'Nat: Tiempo (hh:mm:ss)', 'hist': 'Natación', 'tipo': 'tiempo', 'label': 'Tiempo', 'unit': ''},
        'nat_dist':   {'col': 'Nat: Distancia (km)', 'hist': 'Nat Distancia', 'tipo': 'float', 'label': 'Distancia', 'unit': 'km'},
        'nat_ritmo':  {'col': 'Nat: Ritmo (min/100m)', 'hist': 'Nat Ritmo', 'tipo': 'tiempo', 'label': 'Ritmo', 'unit': '/100m'},
        'bike_tiempo': {'col': 'Ciclismo: Tiempo (hh:mm:ss)', 'hist': 'Ciclismo', 'tipo': 'tiempo', 'label': 'Tiempo', 'unit': ''},
        'bike_dist':   {'col': 'Ciclismo: Distancia (km)', 'hist': 'Ciclismo Distancia', 'tipo': 'float', 'label': 'Distancia', 'unit': 'km'},
        'bike_elev':   {'col': 'Ciclismo: KOM/Desnivel (m)', 'hist': 'Ciclismo Desnivel', 'tipo': 'float', 'label': 'Desnivel', 'unit': 'm'},
        'bike_vel':    {'col': 'Ciclismo: Vel. Media (km/h)', 'hist': 'Ciclismo Velocidad', 'tipo': 'float', 'label': 'Vel. Media', 'unit': 'km/h'},
        'run_tiempo': {'col': 'Trote: Tiempo (hh:mm:ss)', 'hist': 'Trote', 'tipo': 'tiempo', 'label': 'Tiempo', 'unit': ''},
        'run_dist':   {'col': 'Trote: Distancia (km)', 'hist': 'Trote Distancia', 'tipo': 'float', 'label': 'Distancia', 'unit': 'km'},
        'run_elev':   {'col': 'Trote: KOM/Desnivel (m)', 'hist': 'Trote Desnivel', 'tipo': 'float', 'label': 'Desnivel', 'unit': 'm'},
        'run_ritmo':  {'col': 'Trote: Ritmo (min/km)', 'hist': 'Trote Ritmo', 'tipo': 'tiempo', 'label': 'Ritmo', 'unit': '/km'},
    }

    # Promedios Club
    avgs_club = {}
    for k, info in METRICAS.items():
        if info['col'] in df_sem.columns:
            vals = df_sem[info['col']].apply(lambda x: clean_time(x) if info['tipo'] == 'tiempo' else clean_float(x))
            if info['tipo'] == 'tiempo': vals = vals[vals > pd.Timedelta(0)]; avgs_club[k] = vals.mean() if not vals.empty else pd.Timedelta(0)
            else: vals = vals[vals > 0]; avgs_club[k] = vals.mean() if not vals.empty else 0.0
        else: avgs_club[k] = None

    # Históricos Globales
    avgs_hist_global = {}
    for k, info in METRICAS.items():
        target_sheet = next((s for s in dfs_hist.keys() if info['hist'].lower() in s.lower()), None)
        if target_sheet:
            df_h = dfs_hist[target_sheet]
            cols_vals = [c for c in df_h.columns if 'sem' in c.lower()]
            all_vals = []
            for c in cols_vals:
                vals_col = df_h[c].apply(lambda x: clean_time(x) if info['tipo'] == 'tiempo' else clean_float(x))
                if info['tipo'] == 'tiempo': all_vals.extend([v.total_seconds() for v in vals_col if v.total_seconds() > 0])
                else: all_vals.extend([v for v in vals_col if v > 0])
            if all_vals:
                if info['tipo'] == 'tiempo': avgs_hist_global[k] = pd.Timedelta(seconds=sum(all_vals)/len(all_vals))
                else: avgs_hist_global[k] = sum(all_vals)/len(all_vals)
            else: avgs_hist_global[k] = None
        else: avgs_hist_global[k] = None

    # Procesar Atletas
    lista_final = []
    c_nom = next((c for c in df_sem.columns if c in ['Deportista', 'Nombre']), None)
    if not c_nom: raise ValueError("No encuentro la columna 'Deportista' en el archivo semanal.")

    for _, row in df_sem.iterrows():
        nombre = str(row[c_nom]).strip()
        if nombre.lower() in ['nan', 'totales']: continue
        atleta_data = {'name': nombre, 'metrics': {}}

        for k, info in METRICAS.items():
            val_curr = clean_time(row.get(info['col'])) if info['tipo']=='tiempo' else clean_float(row.get(info['col']))
            val_hist = None
            
            target_sheet = next((s for s in dfs_hist.keys() if info['hist'].lower() in s.lower()), None)
            if target_sheet:
                df_h = dfs_hist[target_sheet]
                c_n_h = next((c for c in df_h.columns if c.lower() in ['nombre','deportista']), None)
                if c_n_h:
                    r_h = df_h[df_h[c_n_h].astype(str).str.lower().str.strip() == nombre.lower()]
                    if not r_h.empty:
                        cols_sem = [c for c in df_h.columns if 'sem' in c.lower()]
                        if len(cols_sem) > 0:
                            vals = [clean_time(r_h.iloc[0][c]) if info['tipo']=='tiempo' else clean_float(r_h.iloc[0][c]) for c in cols_sem]
                            if info['tipo'] == 'tiempo':
                                vals = [v.total_seconds() for v in vals if v.total_seconds() > 0]
                                if vals: val_hist = pd.Timedelta(seconds=sum(vals)/len(vals))
                            else:
                                vals = [v for v in vals if v > 0]
                                if vals: val_hist = sum(vals)/len(vals)

            atleta_data['metrics'][k] = {'val': val_curr, 'avg': avgs_club.get(k), 'hist': val_hist, 'meta': info}
        lista_final.append(atleta_data)
    
    return lista_final, avgs_club, avgs_hist_global

# --- 5. GENERAR WORD ---
def generar_word_en_memoria(lista_atletas, nombre_semana, team_avg_sem, team_avg_hist):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10.5)
    style.paragraph_format.space_after = Pt(2)

    # Carátula
    h1 = doc.add_heading("🦅 RESUMEN GLOBAL DEL EQUIPO", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER; h1.runs[0].font.color.rgb = RGBColor(0, 51, 102)
    p = doc.add_paragraph(f"Reporte: {nombre_semana}"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    table = doc.add_table(rows=1, cols=3); table.style = 'Table Grid'
    hdr = table.rows[0].cells; hds = ["MÉTRICA", "PROMEDIO SEMANA", "PROMEDIO ANUAL"]
    for i, txt in enumerate(hds): 
        r=hdr[i].paragraphs[0].add_run(txt); r.bold=True; hdr[i].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER

    keys_cov = ['tot_tiempo', 'tot_dist', 'tot_elev', 'cv', 'nat_tiempo', 'bike_tiempo', 'run_tiempo']
    labels_cov = ['Tiempo Total', 'Distancia Total', 'Desnivel Total', 'Consistencia (CV)', 'Tiempo Natación', 'Tiempo Ciclismo', 'Tiempo Trote']

    for k, lbl in zip(keys_cov, labels_cov):
        tipo = 'tiempo' if 'tiempo' in k or 'ritmo' in k else 'float'
        unit = 'km' if 'dist' in k else ('m' if 'elev' in k else '')
        r = table.add_row().cells
        r[0].text = lbl; r[0].paragraphs[0].runs[0].bold=True
        r[1].text = f"{fmt_val(team_avg_sem.get(k), tipo)} {unit}"; r[1].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
        r[2].text = f"{fmt_val(team_avg_hist.get(k), tipo)} {unit}"; r[2].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()

    # Fichas
    for s in doc.sections: s.top_margin = Cm(1.27); s.bottom_margin = Cm(1.27); s.left_margin = Cm(1.5); s.right_margin = Cm(1.5)

    for i, d in enumerate(lista_atletas):
        if i > 0: doc.add_page_break()
        h = doc.add_heading(level=1); run = h.add_run(f"🦅 REPORTE 360°: {d['name']}")
        run.font.color.rgb = RGBColor(0, 51, 102); run.font.bold = True; h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("─" * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

        m = d['metrics']
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"⏱️ {fmt_val(m['tot_tiempo']['val'], 'tiempo')}  |  📏 {fmt_val(m['tot_dist']['val'], 'float')} km  |  ⛰️ {fmt_val(m['tot_elev']['val'], 'float')} m").bold=True; p.runs[0].font.size=Pt(13)

        p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        val=m['tot_tiempo']['val']; avg=m['tot_tiempo']['avg']; hist=m['tot_tiempo']['hist']
        if val.total_seconds()>0 and avg:
            diff=val-avg; sign="+" if diff.total_seconds()>=0 else "-"
            c=RGBColor(0,100,0) if diff.total_seconds()>=0 else RGBColor(180,0,0)
            p2.add_run(f"👥 Vs Equipo: {sign}{fmt_val(abs(diff),'tiempo')}   ").font.color.rgb=c
        if hist:
            diff=val-hist; sign="+" if diff.total_seconds()>=0 else "-"
            c=RGBColor(0,100,0) if diff.total_seconds()>=0 else RGBColor(180,0,0)
            p2.add_run(f"📅 Vs Promedio Anual: {sign}{fmt_val(abs(diff),'tiempo')}").font.color.rgb=c
        else: p2.add_run("📅 Vs Promedio Anual: 🆕 1er Reg").font.color.rgb=RGBColor(0,0,128)
        
        doc.add_paragraph("").paragraph_format.space_after = Pt(12)

        def tabla_sin_bordes(titulo, keys):
            act = any((m[k]['meta']['tipo']=='tiempo' and m[k]['val'].total_seconds()>0) or (m[k]['meta']['tipo']!='tiempo' and m[k]['val']>0) for k in keys)
            p=doc.add_paragraph(); t=p.add_run(titulo); t.bold=True; t.font.size=Pt(12); t.font.color.rgb=RGBColor(0,51,102)
            if not act: p.add_run(" (Sin actividad)").font.color.rgb=RGBColor(150,150,150); return

            tbl = doc.add_table(rows=1, cols=4)
            hdr = tbl.rows[0].cells; hds=["Métrica","Dato","Vs Equipo","Vs Prom. Anual"]
            for j,txt in enumerate(hds): 
                r=hdr[j].paragraphs[0].add_run(txt); r.bold=True; r.font.color.rgb=RGBColor(100,100,100); hdr[j].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
            
            for k in keys:
                item=m[k]; meta=item['meta']; val=item['val']; avg=item['avg']; h_val=item['hist']
                if (meta['tipo']=='tiempo' and val.total_seconds()==0) or (meta['tipo']!='tiempo' and val==0): continue
                row=tbl.add_row().cells
                row[0].text=meta['label']; row[0].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
                row[1].text=f"{fmt_val(val,meta['tipo'])} {meta.get('unit','')}"; row[1].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER; row[1].paragraphs[0].runs[0].bold=True
                
                pe=row[2].paragraphs[0]; pe.alignment=WD_ALIGN_PARAGRAPH.CENTER
                if avg:
                    if meta['tipo']=='tiempo': diff=val-avg; ok=diff.total_seconds()>=0
                    else: diff=val-avg; ok=diff>=0
                    if 'Ritmo' in meta['label']: ok=not ok
                    sign="+" if ok else "-"; txt=f"{sign}{fmt_val(abs(diff),meta['tipo'])}"
                    pe.add_run(txt).font.color.rgb=RGBColor(0,100,0) if ok else RGBColor(180,0,0)
                else: pe.add_run("-")

                ph=row[3].paragraphs[0]; ph.alignment=WD_ALIGN_PARAGRAPH.CENTER
                if h_val:
                    if meta['tipo']=='tiempo': diff=val-h_val; ok=diff.total_seconds()>=0
                    else: diff=val-h_val; ok=diff>=0
                    if 'Ritmo' in meta['label']: ok=not ok
                    sign="+" if ok else "-"; txt=f"{sign}{fmt_val(abs(diff),meta['tipo'])}"
                    ph.add_run(txt).font.color.rgb=RGBColor(0,100,0) if ok else RGBColor(180,0,0)
                else: ph.add_run("🆕").font.color.rgb=RGBColor(0,0,128)
            doc.add_paragraph("").paragraph_format.space_after=Pt(6)

        tabla_sin_bordes("🏊 NATACIÓN", ['nat_tiempo','nat_dist','nat_ritmo'])
        tabla_sin_bordes("🚴 CICLISMO", ['bike_tiempo','bike_dist','bike_elev','bike_vel'])
        tabla_sin_bordes("🏃 TROTE", ['run_tiempo','run_dist','run_elev','run_ritmo'])

        p_cv = doc.add_paragraph(); p_cv.add_run(f"⚖️ CONSISTENCIA (CV): {fmt_val(m['cv']['val'], 'float')}").bold=True
        if m['cv']['avg']:
            ok=m['cv']['val']<m['cv']['avg']; txt=" (Mejor que prom.)" if ok else " (Menor que prom.)"
            p_cv.add_run(txt).font.color.rgb=RGBColor(0,100,0) if ok else RGBColor(180,0,0)

        doc.add_paragraph("─" * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ins=doc.add_paragraph(); run_i=p_ins.add_run("💡 Insight: "); run_i.bold=True; run_i.font.color.rgb=RGBColor(255,102,0)
        p_ins.add_run("La consistencia es el camino al éxito.").italic=True

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 6. INTERFAZ Y DESCARGA ---
if f_hist and f_sem:
    st.success("✅ Archivos cargados. ¡Listo para procesar!")
    if st.button("▶️ GENERAR REPORTE ATHLOS", type="primary"):
        with st.spinner("🦅 Procesando atletas... (Esto es rápido)"):
            try:
                # Procesar
                datos, avg_sem, avg_hist = procesar_datos_web(f_hist, f_sem)
                st.balloons()
                st.success(f"✅ ¡Éxito! Se generó el reporte para {len(datos)} atletas.")

                # Generar Word
                doc_buffer = generar_word_en_memoria(datos, f_sem.name, avg_sem, avg_hist)

                # Botón Descarga
                st.download_button(
                    label="📥 DESCARGAR REPORTE EXECUTIVE (.DOCX)",
                    data=doc_buffer,
                    file_name=f"Reporte_Athlos_{f_sem.name.replace('.xlsx','')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            except Exception as e:
                st.error(f"❌ Ocurrió un error: {e}")
else:
    st.info("👈 Sube los 2 archivos Excel en la barra lateral para comenzar.")