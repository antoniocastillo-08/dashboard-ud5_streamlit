import json
import os
import time
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración inicial de la página (Debe ser la primera línea de Streamlit)
st.set_page_config(page_title="Dashboard YouTube Insights", layout="wide")


@st.cache_data(ttl=60)  # Optimización mediante caché para evitar relecturas innecesarias
def cargar_y_procesar_datos(ruta_fichero):
    """
    Carga el archivo de datos externo JSON y utiliza json_normalize
    para aplanar las estructuras jerárquicas complejas de la API de YouTube.
    """
    if not os.path.exists(ruta_fichero):
        st.error(f"No se encontró el archivo de datos en: {ruta_fichero}")
        return pd.DataFrame()

    try:
        with open(ruta_fichero, 'r', encoding='utf-8') as f:
            datos_json = json.load(f)

        # Aplanado de diccionarios anidados (statistics.*, snippet.*)
        df_plano = pd.json_normalize(datos_json)

        # Saneamiento y conversión de tipos (la API de YouTube devuelve números como strings)
        df_plano['statistics.viewCount'] = pd.to_numeric(df_plano['statistics.viewCount'], errors='coerce').fillna(
            0).astype(int)
        df_plano['statistics.likeCount'] = pd.to_numeric(df_plano['statistics.likeCount'], errors='coerce').fillna(
            0).astype(int)
        df_plano['statistics.commentCount'] = pd.to_numeric(df_plano['statistics.commentCount'],errors='coerce').fillna(0).astype(int)
        df_plano['search_year'] = pd.to_numeric(df_plano['search_year'], errors='coerce').fillna(2026).astype(int)

        return df_plano
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo JSON: {e}")
        return pd.DataFrame()


# JSON que recoge los datos e inicio del session state
FICHERO_DATOS = 'top_gaming_spain.json'

# Inicializamos el dataframe en session_state para mantener la consistencia entre refrescos
if 'df_videos' not in st.session_state:
    st.session_state.df_videos = cargar_y_procesar_datos(FICHERO_DATOS)
    st.session_state.ultima_actualizacion = datetime.now().strftime('%H:%M:%S')

df = st.session_state.df_videos

# Títulos del Dashboard
st.title("Popularidad del sector Gaming en España")
st.caption("Sistemas de Big Data - UD5: Visualización y comunicación de datos")

if df.empty:
    st.warning("⚠️ El conjunto de datos está vacío. Asegúrate de tener el archivo JSON en el mismo directorio.")
    st.stop()

# Seccion de control
st.sidebar.header("Panel de Control de Fechas")

# Slider para rango de años
anios_disponibles = sorted(df['search_year'].unique().tolist())
rango_anios = st.sidebar.slider(
    "Selecciona Rango de Años de Búsqueda:",
    min_value=int(min(anios_disponibles)),
    max_value=int(max(anios_disponibles)),
    value=(int(min(anios_disponibles)), int(max(anios_disponibles)))
)

# Filtrado sobre el DataFrame original
df_filtrado = df[
    (df['search_year'] >= rango_anios[0]) &
    (df['search_year'] <= rango_anios[1])
    ]


# ---KPI con comparativa al año anterior---

st.subheader("Indicadores Clave de Rendimiento (KPIs Enriquecidos)")
kpi1, kpi2, kpi3 = st.columns(3)

if not df_filtrado.empty:
    anio_actual = rango_anios[1]
    anio_anterior = anio_actual - 1

    # Datos del año actual
    df_actual = df_filtrado[df_filtrado['search_year'] == anio_actual]
    # Datos del año anterior
    df_anterior = df[df['search_year'] == anio_anterior]

    # --- Cálculo de métricas del año actual ---
    vistas_actual = df_actual['statistics.viewCount'].sum()
    likes_actual = df_actual['statistics.likeCount'].sum()
    comentarios_actual = df_actual['statistics.commentCount'].sum()

    # --- CÁLCULO CORE DE VISITAS TOTALES FILTRADAS ---
    # 🔥 Aquí calculamos la suma absoluta de todo el segmento temporal seleccionado por el usuario
    vistas_totales_filtradas = df_filtrado['statistics.viewCount'].sum()

    # --- Cálculo de métricas del año anterior (referencia para el delta) ---
    vistas_anterior = df_anterior['statistics.viewCount'].sum()
    likes_anterior = df_anterior['statistics.likeCount'].sum()
    comentarios_anterior = df_anterior['statistics.commentCount'].sum()

    # --- Engagement del año actual ---
    if vistas_actual > 0:
        medidor_engagement = ((likes_actual + comentarios_actual) / vistas_actual) * 100
    else:
        medidor_engagement = 0.0

    # --- Engagement del año anterior (para el delta) ---
    if vistas_anterior > 0:
        engagement_anterior = ((likes_anterior + comentarios_anterior) / vistas_anterior) * 100
    else:
        engagement_anterior = 0.0

    # 🔥 RENDERIZADO DEL KPI 1 CORREGIDO
    kpi1.metric(
        label="Visitas Totales Acumuladas",
        value=f"{vistas_totales_filtradas:,}",  # Aplica comas de millar para una lectura excelente
    )

    kpi2.metric(
        label="Media de Likes",
        value=f"{df_actual['statistics.likeCount'].mean():.2f}" if not df_actual.empty else "0",
        delta=f"{df_actual['statistics.likeCount'].mean() - df_anterior['statistics.likeCount'].mean():.2f} vs {anio_anterior}"
        if not df_anterior.empty else "Sin datos previos"
    )

    kpi3.metric(
        label="Engagement",
        value=f"{medidor_engagement:.2f} %",
        delta=f"{medidor_engagement - engagement_anterior:.2f} pp vs {anio_anterior}"
        if not df_anterior.empty else "Sin datos previos"
    )
else:
    medidor_engagement = 0.0
    kpi1.metric("Visitas totales", "0")
    kpi2.metric("Media de Likes", "0")
    kpi3.metric("Engagement", "0 %")

st.divider()

col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("Volumen de Consumo por Canal de YouTube")
    if not df_filtrado.empty:

        # GRÁFICO TIPO 1: Gráfico de Barras Agrupadas
        # Agrupamos por canal para ver los creadores de contenido mas populares
        df_canales = df_filtrado.groupby('snippet.channelTitle')['statistics.viewCount'].sum().reset_index()
        df_canales = df_canales.sort_values(by='statistics.viewCount', ascending=False).head(10)

        fig_barras = px.bar(
            df_canales,
            x="statistics.viewCount",
            y="snippet.channelTitle",
            orientation='h',  # Barras horizontales para una legibilidad excelente de los nombres
            labels={
                "statistics.viewCount": "Número de Reproducciones Acumuladas",
                "snippet.channelTitle": "Nombre del Canal de YouTube"
            },
            color="statistics.viewCount",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_barras, width='stretch')
    else:
        st.info("Ajusta los filtros interactivos para representar la gráfica de barras.")

with col_grafico2:
    st.subheader("Correlación: Popularidad vs Interacción de Usuarios")
    if not df_filtrado.empty:

        # GRÁFICO TIPO 2: Gráfico de Dispersión (Scatter Plot)
        # Muestra la relación directa entre el éxito masivo (visitas) y la respuesta del usuario (likes)
        fig_dispersion = px.scatter(
            df_filtrado,
            x="statistics.viewCount",
            y="statistics.likeCount",
            size="statistics.commentCount",  # El tamaño del punto representa el volumen de debate
            hover_name="snippet.title",
            labels={
                "statistics.viewCount": "Volumen de Reproducciones",
                "statistics.likeCount": "Me Gusta (Likes) Recibidos",
                "statistics.commentCount": "Nº de Comentarios"
            }
        )
        st.plotly_chart(fig_dispersion, width='stretch')
    else:
        st.info("Ajusta los filtros interactivos para representar la gráfica de dispersión.")

col_grafico3, col_grafico4 = st.columns(2)

with col_grafico3:

    st.subheader("Volumen de Vistas por año")
    # Este grafico no se actualiza es simplemente informativo

    # GRAFICO 3: Cantidad de Visitas por cada año
    #Agrupamos en un nuevo dataframe para que los datos se muestren en un solo bloque por año
    if not df_filtrado.empty:
        df_agrupado_anual = df.groupby(['search_year', 'region_origin'])[
            'statistics.viewCount'].sum().reset_index()

        fig_bloque_unico = px.bar(
            df_agrupado_anual,
            x="search_year",
            y="statistics.viewCount",
            labels={
                "statistics.viewCount": "Total de Reproducciones",
                "search_year": "Año de Búsqueda",
                "region_origin": "País de Región"
            }
        )

        st.plotly_chart(fig_bloque_unico, use_container_width=True)
    else:
        st.info("Ajusta los filtros interactivos para representar la gráfica de interés anual.")

with col_grafico4:
    st.subheader("Análisis de Tendencias: Productos y Conceptos Clave")

    # GRAFICO 4: Detección de los tags almacenados en los videos más populares
    if not df_filtrado.empty:
        # 1. Filtramos las filas que no tengan tags para evitar errores (algunos vídeos no llevan)
        df_con_tags = df_filtrado[df_filtrado['snippet.tags'].notna()]

        if not df_con_tags.empty:
            # 2. .explode() convierte cada elemento de la lista de tags en una fila independiente
            tags_explotados = df_con_tags['snippet.tags'].explode()

            # 3. Limpieza: minúsculas para unificar "Gaming" y "gaming" como el mismo término
            tags_limpios = tags_explotados.astype(str).str.strip().str.lower()

            # 4. Contamos frecuencia de cada etiqueta
            top_tags = tags_limpios.value_counts().reset_index()
            top_tags.columns = ['Etiqueta/Producto', 'Frecuencia']

            # Ponemos la columna como índice para poder borrar por nombre
            top_tags_filtrado = top_tags.set_index('Etiqueta/Producto')

            # Excluimos términos genéricos que no aportan valor analítico
            palabras_a_excluir = ['games', 'game', 'gameplay', 'videogames', 'video game','video games', 'gaming']
            top_tags_filtrado = top_tags_filtrado.drop(index=palabras_a_excluir, errors='ignore')

            # Volvemos a recuperar la columna y nos quedamos con el top 10
            top_tags = top_tags_filtrado.reset_index().head(10)

            # 5. TREEMAP: cada rectángulo es un tag, su tamaño representa la frecuencia de aparición
            # px.treemap necesita una columna 'path' (jerarquía) y 'values' (tamaño del bloque)
            fig_tags = px.treemap(
                top_tags,
                path=['Etiqueta/Producto'],   # Un único nivel jerárquico: el propio tag
                values='Frecuencia',           # El tamaño de cada bloque = nº de apariciones
                color='Frecuencia',            # El color también refleja la frecuencia
                color_continuous_scale='Viridis'
            )

            # Añadimos el texto con el nombre del tag y su frecuencia dentro de cada bloque
            fig_tags.update_traces(textinfo='label+value')

            st.plotly_chart(fig_tags, use_container_width=True)
        else:
            st.info("Ninguno de los vídeos seleccionados contiene etiquetas en sus metadatos.")
    else:
        st.info("Ajusta los filtros para calcular las tendencias de etiquetas.")
st.sidebar.write(f"*Última sincronización de sesión: {st.session_state.ultima_actualizacion}*")

auto_refresco = st.sidebar.checkbox("Habilitar Auto-Refresco del JSON (Cada 10s)", value=False)

if auto_refresco:
    # Validamos si ha transcurrido el intervalo de 10 segundos
    time.sleep(INTERVALO_TIEMPO := 10)

    # Forzamos la relectura del JSON físico en segundo plano para actualizar la sesión
    st.session_state.df_videos = cargar_y_procesar_datos(FICHERO_DATOS)
    st.session_state.ultima_actualizacion = datetime.now().strftime('%H:%M:%S')

    # Rerun nativo de Streamlit para actualizar el dashboard
    st.rerun()