import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from timezonefinder import TimezoneFinder
from countryinfo import CountryInfo
import pycountry
import pytz
from datetime import datetime
import ast

st.set_page_config(page_title="GeoFinder Pro", page_icon="🌍", layout="wide")

# Ficheiros externos
@st.cache_data
def load_external_files():
    categorias_dict = {}
    lista_principais = []
    try:
        with open('categories.txt', 'r', encoding="UTF-8") as f:
            for line in f:
                line = line.strip()
                if '.' in line:
                    ponto_idx = line.find('.')
                    pai = line[:ponto_idx]
                    filho = line[ponto_idx + 1:]
                    if pai not in categorias_dict: categorias_dict[pai] = []
                    categorias_dict[pai].append(filho)
                    if pai not in lista_principais: lista_principais.append(pai)
    except: pass

    moedas_dict = {}
    try:
        with open('moedas.txt.txt', 'r', encoding="UTF-8") as f:
            moedas_dict = ast.literal_eval(f.read())
    except: pass

    return categorias_dict, sorted(lista_principais), moedas_dict

CATS_DICT, PRINCIPAIS, MOEDAS_DATA = load_external_files()

# Funções de suporte

def get_enriched_info(row):
    """Calcula Hora Local Real, Moeda e Info do País"""
    # 1. Hora Local Real (AM/PM)
    try:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=row['lon'], lat=row['lat'])
        if tz_name:
            timezone = pytz.timezone(tz_name)
            row['Hora Local'] = datetime.now(timezone).strftime("%H:%M (%I:%M %p)")
        else:
            row['Hora Local'] = "N/A"
    except:
        row['Hora Local'] = "N/A"

    # 2. Moeda (Ficheiro + Fallback)
    pais_upper = str(row.get('País', '')).upper()
    row['Moeda'] = MOEDAS_DATA.get(pais_upper, "N/A")
    if row['Moeda'] == "N/A":
        try:
            c_res = pycountry.countries.search_fuzzy(row.get('País', ''))[0]
            row['Moeda'] = pycountry.currencies.get(numeric=c_res.numeric).name
        except: pass

    # 3. Capital
    try:
        row['Capital'] = CountryInfo(row.get('País', '')).capital()
    except:
        row['Capital'] = "N/A"
        
    return row

def buscar_locais(lon, lat, dist, categoria, limite):
    try:
        api_key = st.secrets["GEOAPIFY_KEY"]
    except:
        st.error("ERRO: Configura a GEOAPIFY_KEY nos Segredos do Streamlit!")
        return None

    url = f"https://api.geoapify.com/v2/places?categories={categoria}&filter=circle:{lon},{lat},{dist}&bias=proximity:{lon},{lat}&limit={limite}&apiKey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        features = data.get("features", [])
        
        if not features:
            return []

        res_list = []
        for item in features:
            p = item.get("properties", {})
            g = item.get("geometry", {}).get("coordinates", [0, 0])
            res = {
                'Nome': p.get("name", "Sem nome"),
                'Distância (m)': p.get("distance"),
                'Morada': p.get("formatted"),
                'Cidade': p.get("city"),
                'País': p.get("country"),
                'lat': g[1], 'lon': g[0]
            }
            res = get_enriched_info(res)
            res_list.append(res)
        return res_list
    except:
        return []

# Interface

st.title("🌍 GeoFinder Pro: Localização e Informação Real")

if 'dados' not in st.session_state:
    st.session_state.dados = None
if 'aviso_erro' not in st.session_state:
    st.session_state.aviso_erro = False

# Barra Lateral
with st.sidebar:
    st.header("📍 Configurações")
    lat_in = st.number_input("Latitude", value=38.7071, format="%.6f")
    lon_in = st.number_input("Longitude", value=-9.1355, format="%.6f")
    raio = st.number_input("Raio (Metros)", value=1000)
    limit = st.slider("Resultados", 1, 50, 10)
    
    st.divider()
    if PRINCIPAIS:
        escolha_pai = st.selectbox("Categoria", PRINCIPAIS)
        categoria_final = escolha_pai
        if st.checkbox("Sub-categoria específica"):
            sub = st.selectbox("Detalhe", CATS_DICT.get(escolha_pai, []))
            categoria_final = f"{escolha_pai}.{sub}"
    else:
        categoria_final = "activity"

# Botão de Pesquisa
if st.button("🔍 PROCURAR LOCAIS"):
    with st.spinner("A pesquisar e a calcular horários..."):
        res = buscar_locais(lon_in, lat_in, raio, categoria_final, limit)
        
        if res: # Se encontrou resultados
            st.session_state.dados = res
            st.session_state.pos = (lat_in, lon_in)
            st.session_state.aviso_erro = False
        else: # Se a lista veio vazia ou erro
            st.session_state.dados = None
            st.session_state.aviso_erro = True

# Caso não encontre nada

if st.session_state.aviso_erro:
    st.warning("⚠️ Não foi possível encontrar o que queria com esses critérios. Tente aumentar a distância ou mudar a categoria.")

if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    st.success(f"Encontrados {len(df)} locais!")

    tab1, tab2, tab3 = st.tabs(["📊 Tabela Completa", "🗺️ Mapa Interativo", "💾 Exportar"])

    with tab1:
        cols = ['Nome', 'Distância (m)', 'Morada', 'Cidade', 'Moeda', 'Hora Local', 'Capital']
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True)

    with tab2:
        st.subheader("Visualização no Mapa")
        m = folium.Map(location=st.session_state.pos, zoom_start=14)
        
        # Pin da Pesquisa
        folium.Marker(st.session_state.pos, popup="Ponto de Pesquisa", icon=folium.Icon(color='black', icon='home')).add_to(m)
        
        # Pins dos Resultados
        for _, r in df.iterrows():
            folium.Marker(
                [r['lat'], r['lon']],
                popup=f"<b>{r['Nome']}</b><br>Hora: {r['Hora Local']}<br>Moeda: {r['Moeda']}",
                tooltip=r['Nome'],
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        st_folium(m, use_container_width=True, height=500, key="mapa_vFinal")

    with tab3:
        st.subheader("Download de Dados")
        csv_buffer = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Resultados (CSV)",
            data=csv_buffer,
            file_name='pesquisa_geofinder.csv',
            mime='text/csv'
        )