import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime
import time
import pytz

st.set_page_config(
    page_title="Dashboard Critpomoneda - con histórico",
    page_icon="💰",
    layout="wide", #Qiue el contenido se expande
)
INTERVALO_SEGUNDOS = 60

#API
URL = "https://api.coingecko.com/api/v3/simple/price"
PARAMS = {
    "ids": "bitcoin,ethereum,solana",
    "vs_currencies": "eur",
    "include_24hr_change": "true",
}
MONEDAS = {"bitcoin": "Bitcoin", "ethereum": "Ethereum", "solana": "Solana"}

def obtener_precios():
    """Llama a la API y devuelve un diccionario limpio con precio y cambio 24h.
    Si la API falla (sin internet, límite de peticiones - 30 peticiones por minuto), devuelve None.
    """
    try:
        r = requests.get(URL, params=PARAMS, timeout=5)
        r.raise_for_status()   # Lanza error si status != 200
        raw = r.json()
        
        resultado = {}
        for clave, nombre in MONEDAS.items():
            resultado[nombre] = {
                "precio": raw[clave]["eur"],
                "cambio": raw[clave]["eur_24h_change"],
            }
        resultado["timestamp"] = datetime.now().strftime("%H:%M:%S")
        return resultado
    
    except Exception as e:
        print(f"Error al llamar a la API: {e}")
        return None

#Inicializar session state
if 'historial' not in st.session_state:
     st.session_state['historial'] = []

precios = obtener_precios()

nuevo_punto = {
        'tiempo': precios["timestamp"],
        'Bitcoin': precios['Bitcoin']['precio'],
        'Ethereum': precios['Ethereum']['precio'],
        'Solana': precios['Solana']['precio'],
}

st.session_state['historial'].append(nuevo_punto)


if precios is None:
        st.error("No se pudo conectar coj la API. Reintentando....")
        time.sleep(INTERVALO_SEGUNDOS)
        st.rerun()

st.title("Dashboard Cripto monedas")
st.caption(f'Última actualización: {precios["timestamp"]}')
st.divider()

kpi1,kpi2,kpi3 = st.columns(3)
kpi1.metric("Bitcoin", f"{precios['Bitcoin']['precio']:,.0f} €",f"{precios['Bitcoin']['cambio']:+.2f} % (24h)")
kpi2.metric("Ethereum", f"{precios['Ethereum']['precio']:,.0f} €",f"{precios['Ethereum']['cambio']:+.2f} % (24h)")
kpi3.metric("Solana", f"{precios['Solana']['precio']:,.0f} €",f"{precios['Solana']['cambio']:+.2f} % (24h)")

st.divider()

#Gráficos
col_izq, col_der = st.columns(2)

with col_izq:
    #Gráfico del histórico
    df = pd.DataFrame(st.session_state['historial'])
    fig_lineas = px.line(
        df,
        x='tiempo',
        y= ['Bitcoin','Ethereum','Solana'],
        title='Evolucion de precio durante la sesión',
        template='plotly_dark',
        markers=True,
    )
    fig_lineas.update_layout(showlegend=True)
    st.plotly_chart(fig_lineas,width="stretch")
with col_der: 
    nombres= ['Bitcoin','Ethereum','Solana']
    colores = ['orange','royalblue','purple']  
    precios_lista = [precios[m]['precio'] for m in nombres]
    fig_barras = px.bar(
        x=nombres,
        y=precios_lista,
        color=nombres,
        color_discrete_sequence=colores,
        labels={'x': 'Moneda', 'y':'Precio (€)'},
        title='Precio actual en €',
        template='plotly_dark',
    )
    fig_barras.update_layout(showlegend=False)
    st.plotly_chart(fig_barras,width="stretch")

time.sleep(INTERVALO_SEGUNDOS)
st.rerun()