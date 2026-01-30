import streamlit as st
import pandas as pd
import io
import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Athlos 360", page_icon="🦅")

# --- FUNCIONES DE LÓGICA (EL CEREBRO) ---
def clean_time(val):
    # Convierte cualquier cosa a tiempo o devuelve 0
    if pd.isna(val) or str(val).strip() in ['NC', '0', '', 'NAN', '-']: 
        return pd.Timedelta(0)
    try:
        # Si ya es tiempo
        if isinstance(val, (datetime.time, datetime.datetime)):
            return pd.Timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
        # Si es texto "hh:mm:ss"
        parts = list(map(int, str(val).split(':')))
        if len(parts) == 3: return pd.Timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
        if len(parts) == 2: return pd.Timedelta(minutes=parts[0], seconds=parts[1])
    except:
        pass
    return pd.Timedelta(0)

def clean_float(val):
    # Convierte texto a número decimal
    try:
        return float(str(val).replace(',', '.'))
    except:
        return 0.0

def fmt_val(val, tipo):
    # Da formato bonito para el Word
    if val is None: return "-"
    if tipo == 'tiempo':
        if val.total_seconds() == 0: return "-"
        s = int(val.total_seconds())
        if s < 3600: return f"{s//60}m {s%60}s"
        return f"{s//3600}h {(s%3600)//60}m"
    else:
        return f"{val:.1f}" if val > 0 else "-"

def procesar_datos(file_hist, file_sem):
    # 1. Cargar Archivos
    df_sem = pd.read_excel(file_sem, engine='openpyxl')
    df_sem.columns = [str(c).strip() for c in df_sem.columns] # Limpiar nombres columnas
    
    xls = pd.ExcelFile(file_hist, engine='openpyxl')
    dfs_hist = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}

    # 2. Configurar Métricas
    METRICAS = {
        'tot_tiempo': {'col': 'Tiempo Total (hh:mm:ss)', 'hist': 'Total', 'tipo': 'tiempo', 'lbl': 'Tiempo Total', 'u': ''},
        'tot_dist':   {'col': 'Distancia Total (km)', 'hist': 'Distancia Total', 'tipo': 'float', 'lbl': 'Distancia', 'u': 'km'},
        'tot_elev':   {'col': 'Altimetría Total (m)', 'hist': 'Altimetría', 'tipo': 'float', 'lbl': 'Desnivel', 'u': 'm'},
        'cv':         {'col': 'CV (Equilibrio)', 'hist': 'CV', 'tipo': 'float', 'lbl': 'Consistencia', 'u': ''},
        'nat_tiempo': {'col': 'Nat: Tiempo (hh:mm:ss)', 'hist': 'Natación', 'tipo': 'tiempo', 'lbl': 'Tiempo Nat', 'u': ''},
        'bike_tiempo': {'col': 'Ciclismo: Tiempo (hh:mm:ss)', 'hist': 'Ciclismo', 'tipo': 'tiempo', 'lbl': 'Tiempo Bici', 'u': ''},
        'run_tiempo': {'col': 'Trote: Tiempo (hh:mm:ss)', 'hist': 'Trote', 'tipo': 'tiempo', 'lbl': 'Tiempo Trote', 'u': ''}
        # Puedes agregar más aquí si funcionan las básicas
    }

    # 3. Calcular Promedios Equipo
    avgs_club = {}
    for k, info in METRICAS.items():
        if info['col'] in df_sem.columns:
            vals = df_sem[info['col']].apply(lambda x: clean_time(x) if info['tipo'] == 'tiempo' else clean_float(x))
            if info['tipo'] == 'tiempo': 
                validos = vals[vals > pd.Timedelta(0)]
                avgs_club[k] = validos.mean() if not validos.empty else pd.Timedelta(0)
            else:
                validos = vals[vals > 0]
                avgs_club[k] = validos.mean() if not validos.empty else 0.0
        else:
            avgs_club[k] = None

    # 4. Calcular Históricos Globales
    avgs_hist_global = {}
    for k, info in METRICAS.items():
        target = next((s for s in dfs_hist.keys() if info['hist'].lower() in s.lower()), None)
        if target:
            df = dfs_hist[target]
            cols = [c for c in df.columns if 'sem' in c.lower()]
            vals = []
            for c in cols:
                v_col = df[c].apply(lambda x: clean_time(x) if info['tipo'] == 'tiempo' else clean_float(x))
                if info['tipo'] == 'tiempo': vals.extend([v.total_seconds() for v in v_col if v.total_seconds() > 0])
                else: vals.extend([v for v in v_col if v > 0])
            
            if vals:
                if info['tipo'] == 'tiempo': avgs_hist_global[k] = pd.Timedelta(seconds=sum(vals)/len(vals))
                else: avgs_hist_global[k] = sum(vals)/len(vals)
            else: avgs_hist_global[k] = None
        else:
            avgs_hist_global[k] = None

    # 5. Procesar cada atleta
    lista_final = []
    # Buscar columna nombre
    c_nom = next((c for c in df_sem.columns if c in ['Deportista', 'Nombre', 'Atleta']), None)
    if not c_nom:
        st.error(f"❌ No encuentro la columna 'Deportista' en el archivo semanal. Columnas vistas: {list(df_sem.columns)}")
        return [], {}, {}

    for _, row in df_sem.iterrows():
        nombre = str(row[c_nom]).strip()
        if nombre.lower() in ['nan', 'totales', 'promedio']: continue
        
        datos_atleta = {'name': nombre, 'metrics': {}}

        for k, info in METRICAS.items():
            # Dato actual
            val_curr = clean_time(row.get(info['col'])) if info['tipo']=='tiempo' else clean_float(row.get(info['col']))
            
            # Dato histórico
            val_hist = None
            target = next((s for s in dfs_hist.keys() if info['hist'].lower() in s.lower()), None)
            if target:
                df_h = dfs_hist[target]
                c_n_h = next((c for c in df_h.columns if c.lower() in ['nombre','deportista']), None)
                if c_n_h:
                    fila = df_h[df_h[c_n_h].astype(str).str.lower().str.strip() == nombre.lower()]
                    if not fila.empty:
                        cols = [c for c in df_h.columns if 'sem' in c.lower()]
                        if cols:
                            vs = [clean_time(fila.iloc[0][c]) if info['tipo']=='tiempo' else clean_float(fila.iloc[0][c]) for c in cols]
                            if info['tipo']=='tiempo':
                                vs = [v.total_seconds() for v in vs if v.total_seconds()>0]
                                if vs: val_hist = pd.Timedelta(seconds=sum(vs)/len(vs))
                            else:
                                vs = [v for v in vs if v > 0]
                                if vs: val_hist = sum(vs)/len(vs)
            
            datos_atleta['metrics'][k] = {'val': val_curr, 'avg': avgs_club.get(k), 'hist': val_hist, 'meta': info}
        
        lista_final.append(datos_atleta)
    
    return lista_final, avgs_club, avgs_hist_global

def generar_word(lista, semana, avgs_sem, avgs_hist):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10.5)

    # PORTADA
    h = doc.add_heading("🦅 RESUMEN GLOBAL DEL EQUIPO", 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Semana: {semana}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text = "Métrica"
    hdr[1].text = "Promedio Semana"
    hdr[2].text = "Promedio Anual"
    
    keys = ['tot_tiempo', 'tot_dist', 'tot_elev', 'cv']
    for k in keys:
        if k in avgs_sem: # Solo si existe la métrica
            row = table.add_row().cells
            # Obtenemos etiqueta y tipo de alguna ficha (truco sucio pero efectivo)
            sample_meta = lista[0]['metrics'][k]['meta']
            
            row[0].text = sample_meta['lbl']
            row[1].text = f"{fmt_val(avgs_sem[k], sample_meta['tipo'])} {sample_meta['u']}"
            row[2].text = f"{fmt_val(avgs_hist[k], sample_meta['tipo'])} {sample_meta['u']}"

    doc.add_page_break()

    # FICHAS
    for i, d in enumerate(lista):
        if i > 0: doc.add_page_break()
        doc.add_heading(f"🦅 REPORTE: {d['name']}", level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("─"*40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        m = d['metrics']
        
        # Resumen
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        t_total = fmt_val(m['tot_tiempo']['val'], 'tiempo')
        d_total = fmt_val(m['tot_dist']['val'], 'float')
        p.add_run(f"⏱️ {t_total}   |   📏 {d_total} km").bold = True
        
        # Comparativa Texto
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Vs Equipo
        val = m['tot_tiempo']['val']
        avg = m['tot_tiempo']['avg']
        if val.total_seconds() > 0 and avg:
            diff = val - avg
            sign = "+" if diff.total_seconds() >= 0 else "-"
            txt = f"Vs. Equipo: {sign}{fmt_val(abs(diff), 'tiempo')}"
            run = p2.add_run(txt)
            run.font.color.rgb = RGBColor(0,128,0) if diff.total_seconds() >= 0 else RGBColor(200,0,0)

        p2.add_run("   |   ")

        # Vs Histórico
        hist = m['tot_tiempo']['hist']
        if hist:
            diff = val - hist
            sign = "+" if diff.total_seconds() >= 0 else "-"
            txt = f"Vs. Anual: {sign}{fmt_val(abs(diff), 'tiempo')}"
            run = p2.add_run(txt)
            run.font.color.rgb = RGBColor(0,128,0) if diff.total_seconds() >= 0 else RGBColor(200,0,0)
        else:
            p2.add_run("Vs. Anual: Nuevo Registro")

        doc.add_paragraph("─"*40).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Tabla Detalles
        t = doc.add_table(rows=1, cols=4)
        t.autofit = True
        h = t.rows[0].cells
        h[0].text="Métrica"; h[1].text="Tu Dato"; h[2].text="Vs Equipo"; h[3].text="Vs Anual"
        
        for k, item in m.items():
            meta = item['meta']
            val = item['val']
            
            # Si es 0 saltamos para ahorrar espacio
            if meta['tipo']=='tiempo' and val.total_seconds()==0: continue
            if meta['tipo']=='float' and val==0: continue
            
            r = t.add_row().cells
            r[0].text = meta['lbl']
            r[1].text = f"{fmt_val(val, meta['tipo'])} {meta['u']}"
            
            # Vs Eq
            avg = item['avg']
            if avg:
                if meta['tipo']=='tiempo': 
                    diff = val - avg
                    ok = diff.total_seconds() >= 0
                    txt = f"{'+' if ok else '-'}{fmt_val(abs(diff), 'tiempo')}"
                else:
                    diff = val - avg
                    ok = diff >= 0
                    txt = f"{'+' if ok else '-'}{fmt_val(abs(diff), 'float')}"
                r[2].text = txt
            else:
                r[2].text = "-"

            # Vs Hist
            hist = item['hist']
            if hist:
                if meta['tipo']=='tiempo': 
                    diff = val - hist
                    ok = diff.total_seconds() >= 0
                    txt = f"{'+' if ok else '-'}{fmt_val(abs(diff), 'tiempo')}"
                else:
                    diff = val - hist
                    ok = diff >= 0
                    txt = f"{'+' if ok else '-'}{fmt_val(abs(diff), 'float')}"
                r[3].text = txt
            else:
                r[3].text = "New"

        doc.add_paragraph("")
        p_ins = doc.add_paragraph()
        run = p_ins.add_run("💡 Insight: ")
        run.bold = True
        run.font.color.rgb = RGBColor(255, 100, 0)
        p_ins.add_run("La consistencia construye campeones.")

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- INTERFAZ DE USUARIO (LO QUE VES) ---
st.title("🦅 Athlos 360")
st.write("Sube tus archivos para generar los reportes.")

c1, c2 = st.columns(2)
f_hist = c1.file_uploader("1. Histórico", type="xlsx")
f_sem = c2.file_uploader("2. Semana", type="xlsx")

if f_hist and f_sem:
    if st.button("Generar Reporte", type="primary"):
        with st.spinner("Procesando..."):
            try:
                # Ejecutar lógica
                datos, avg_s, avg_h = procesar_datos(f_hist, f_sem)
                
                if not datos:
                    st.warning("No se encontraron atletas o los archivos están vacíos.")
                else:
                    st.success(f"¡Listo! {len(datos)} atletas procesados.")
                    
                    # Generar Word
                    word_file = generar_word(datos, f_sem.name, avg_s, avg_h)
                    
                    st.download_button(
                        label="📥 Descargar Word",
                        data=word_file,
                        file_name=f"Reporte_Athlos_{f_sem.name.replace('.xlsx','')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            except Exception as e:
                st.error("Ocurrió un error inesperado:")
                st.error(e)