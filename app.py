# -----------------------------------------------------------------------------
# 1. CARGA DE DATOS Y SELECTOR DE ATLETAS (CORREGIDO)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    # Intenta leer el archivo maestro
    try:
        # Leemos la hoja 'Distancia Total' que siempre tiene a todos los atletas
        df = pd.read_excel("06 Sem (tst).xlsx", sheet_name="Distancia Total")
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return pd.DataFrame()

df_main = load_data()

# Preparar la lista de nombres
lista_atletas = []

if not df_main.empty:
    # BÚSQUEDA INTELIGENTE DE LA COLUMNA DE NOMBRE
    # A veces se llama 'Nombre', a veces 'Deportista', a veces tiene espacios extra
    posibles_nombres = ['Nombre', 'Deportista', 'Atleta', 'Nombre ']
    columna_nombre_detectada = None
    
    for col in df_main.columns:
        if col.strip() in posibles_nombres:
            columna_nombre_detectada = col
            break
    
    if columna_nombre_detectada:
        # Extraemos los nombres únicos, quitamos vacíos y ordenamos
        nombres_sucios = df_main[columna_nombre_detectada].unique()
        lista_atletas = [n for n in nombres_sucios if str(n) != 'nan' and str(n) != '0']
        lista_atletas.sort()
    else:
        st.error("⚠️ No encontré la columna 'Nombre' en el Excel.")

# --- SELECTOR EN LA BARRA LATERAL ---
# Insertamos la instrucción al principio para que no salga un nombre por defecto
lista_atletas.insert(0, "Selecciona un triatleta...")

st.sidebar.header("Filtros")
atleta_seleccionado = st.sidebar.selectbox(
    "Busca tu nombre:", 
    options=lista_atletas,
    index=0
)

# -----------------------------------------------------------------------------
# 2. LÓGICA DE VISUALIZACIÓN (SÓLO SI SELECCIONA ALGUIEN)
# -----------------------------------------------------------------------------
if atleta_seleccionado == "Selecciona un triatleta...":
    st.info("👈 Por favor, selecciona un atleta en el menú de la izquierda para ver sus estadísticas.")
    st.stop() # Detiene la ejecución aquí hasta que elijan a alguien

# ... AQUÍ SIGUE EL RESTO DE TU CÓDIGO (Gráficos, KPIs, etc.) ...
