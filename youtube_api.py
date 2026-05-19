"""
Este es el script que recoge el JSON de videos mediante Youtube Data API v3
Para usarlo se necesita una api key de youtube y las request utilizadas son limitadas por día
Añado este script solo para informar de donde obtengo los JSON para mi dashboard
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build


load_dotenv()

# Configuración de YouTube
API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=API_KEY)


def obtener_videos_tech_y_actualidad():
    paises = ['ES']
    anio_actual = datetime.now().year
    anios = list(range(2022, anio_actual + 1))

    categorias_objetivo = {
        "20": "Gaming"
    }

    biblioteca_videos = []

    termino_busqueda = "gameplay|walkthrough|review|español|trailer"

    for pais in paises:
        print(f"\n--- PROCESANDO PAÍS: {pais} ---")

        for anio in anios:
            fecha_inicio = f"{anio}-01-01T00:00:00Z"
            fecha_fin = f"{anio}-12-31T23:59:59Z"

            for cat_id, cat_nombre in categorias_objetivo.items():
                print(f"[{cat_nombre}] Buscando los más vistos del año {anio}...")

                try:
                    # Paso 1: Buscar videos filtrando por categoría, rango de fechas y duración
                    search_request = youtube.search().list(
                        part="snippet",
                        q=termino_busqueda,  # 🔥 Ahora sí enviamos una query válida para la API
                        type="video",
                        regionCode=pais,
                        publishedAfter=fecha_inicio,
                        publishedBefore=fecha_fin,
                        order="viewCount",
                        videoDuration="medium",  # Evita Shorts (4 a 20 min)
                        videoCategoryId=cat_id,
                        maxResults=50
                    )
                    search_response = search_request.execute()
                    search_items = search_response.get('items', [])

                    if not search_items:
                        print(f"No se encontraron resultados en el Paso 1 para el año {anio}")
                        continue

                    video_ids = [item['id']['videoId'] for item in search_items]

                    # Paso 2: Consultar estadísticas completas (Métricas de rendimiento)
                    stats_request = youtube.videos().list(
                        part="snippet,statistics",
                        id=",".join(video_ids)
                    )
                    stats_response = stats_request.execute()
                    stats_items = stats_response.get('items', [])

                    for video in stats_items:
                        # Metadatos personalizados para indexar el DataFrame del Dashboard
                        video['search_year'] = anio
                        video['region_origin'] = pais
                        video['custom_category_group'] = cat_nombre

                        # Guardamos el video real en la lista global
                        biblioteca_videos.append(video)

                except Exception as e:
                    print(f"Error en {pais} | Año {anio} | Cat {cat_nombre}: {e}")

    # --- GUARDADO LOCAL ---
    v_file = 'top_gaming_spain.json'

    with open(v_file, 'w', encoding='utf-8') as f:
        json.dump(biblioteca_videos, f, ensure_ascii=False, indent=4)

    print(f"\nProceso finalizado")
    print(f"Total de videos guardados: {len(biblioteca_videos)}")


obtener_videos_tech_y_actualidad()