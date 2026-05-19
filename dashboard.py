# KPIs + dos gráficos + filtro
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- Los mismos datos de StreamFlow ---
datos_mensuales = pd.DataFrame({
    'mes': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
    'mes_num': range(1, 13),
    'mau': [1200000, 1250000, 1310000, 1350000, 1380000, 1340000,
            1290000, 1260000, 1350000, 1420000, 1500000, 1580000],
    'ingresos_k': [320, 335, 352, 360, 370, 355,
                   338, 325, 358, 385, 410, 468],
    'horas_escucha': [1.8, 1.9, 2.0, 1.9, 1.8, 1.7,
                      1.6, 1.5, 1.8, 2.0, 2.1, 2.3],
    'churn_pct': [3.2, 3.0, 2.8, 2.9, 3.1, 3.5,
                  3.8, 4.0, 3.3, 2.7, 2.5, 2.3],
    'conversion_pct': [4.5, 4.7, 5.0, 4.8, 4.6, 4.3,
                       4.1, 3.9, 4.5, 5.1, 5.5, 6.2],
})
np.random.seed(42)
n_usuarios = 500
usuarios = pd.DataFrame({
    'plan': np.random.choice(['Free', 'Premium', 'Familiar', 'Estudiante'],
                              n_usuarios, p=[0.40, 0.30, 0.15, 0.15]),
    'edad': np.random.randint(16, 65, n_usuarios),
    'horas_mes': np.clip(np.random.normal(45, 20, n_usuarios), 5, 150).round(1),
    'pais': np.random.choice(
        ['España', 'México', 'Argentina', 'Colombia', 'Chile', 'Perú'],
        n_usuarios, p=[0.30, 0.25, 0.15, 0.13, 0.10, 0.07]),
    'playlists_creadas': np.random.poisson(5, n_usuarios),
})
usuarios.loc[usuarios['plan'] == 'Premium', 'horas_mes'] *= 1.6
usuarios.loc[usuarios['plan'] == 'Free', 'horas_mes'] *= 0.7
usuarios['horas_mes'] = usuarios['horas_mes'].round(1)
usuarios['gasto_mensual'] = usuarios['plan'].map({
    'Free': 0, 'Premium': 9.99, 'Familiar': 14.99, 'Estudiante': 4.99
})



#Configuarmos la página
st.set_page_config(
    page_title="StreamFlow - Panel de control",
    page_icon="🎶",
    layout="wide", #Qiue el contenido se expande
)
st.title("Dashboard StreamFlow")
st.write("Panel de métricas")
st.divider()
#KPIs
kpi1,kpi2,kpi3 = st.columns(3)

kpi1.metric("MAU", f"{datos_mensuales['mau'].iloc[-1]:,.0f}")
kpi2.metric("Ingresos (dic)", f"{datos_mensuales['ingresos_k'].iloc[-1]:,.0f}")
kpi3.metric("Churn", f"{datos_mensuales['churn_pct'].iloc[-1]}%")

#Gráficos
col_izq, col_der = st.columns(2)
with col_izq:
    fig_ingresos = px.line(
    datos_mensuales, 
    x = 'mes',
    y='ingresos_k',
    title='Evolución de los ingresos',
    markers=True,
    labels={'ingresos_k':'Ingresos (miles €)', 'mes': 'Mes'},
    template='plotly_white',
    )
    st.plotly_chart(fig_ingresos,width="stretch")

with col_der:
    fig_churn = px.line(
    datos_mensuales, 
    x = 'mes',
    y='churn_pct',
    title='Evolución de los ingresos',
    markers=True,
    labels={'churn_pct':'Churn', 'mes': 'Mes'},
    template='plotly_white',
    )
    st.plotly_chart(fig_churn,width="stretch")

# Sección interactiva (cambio con el filtro)
st.divider()
st.header("Análisis por país")

paises = ['Todos'] + sorted(usuarios['pais'].unique().tolist())
pais = st.selectbox("Selecciona un país:",paises)

#Filtrar los datos
if pais == 'Todos':
    datos = usuarios
else:
    datos = usuarios[usuarios['pais'] == pais ]

col_izq2, col_der2 = st.columns(2)
with col_izq2:
    cuenta = datos['plan'].value_counts().reset_index()
    cuenta.columns = ['plan','cantidad']

    fig = px.bar(
        cuenta,
        x='plan',
        y='cantidad',
        title=f'Distribución por plan - {pais}',
        text='cantidad',
        color='plan',
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig,width="stretch")

with col_der2:
    fig2 = px.box(
        datos,
        x='plan',
        y='horas_mes',
        color='plan',
        title=f'Horas de escucha por plan - {pais}',
        )
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2,width="stretch")
    