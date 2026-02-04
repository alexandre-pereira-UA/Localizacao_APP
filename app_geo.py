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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GeoFinder Pro", page_icon="🌍", layout="wide")

# --- CARREGAMENTO DE FICHEIROS EXTERNOS ---

@st.cache_data
def load_external_files():
    # Carregar Categorias
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
    except Exception as e:
        st.error(f"Erro ao carregar categories.txt: {e}")

    # Carregar Moedas (usa o nome exato moedas.txt.txt)
    moedas_dict = {}
    try:
        with open('moedas.txt.txt', 'r', encoding="UTF-8") as f:
            conteudo = f.read()
            # Converte a string do dicionário em dicionário Python real
            moedas_dict = ast.literal_eval(conteudo)
    except Exception as e:
        st.error(f"Erro ao carregar moedas.txt.txt: {e}")

    return categorias_dict, sorted(lista_principais), moedas_dict

# Carregar dados globais
CATS_DICT, PRINCIPAIS, MOEDAS_DATA = load_external_files()

# --- FUNÇÕES DE SUPORTE ---

def get_enriched_info(row):
    """Calcula Hora Local, Moeda e Info do País"""
    # 1. Hora Local
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

    # 2. Moeda (Busca no ficheiro carregado)
    pais_upper = str(row.get('País', '')).upper()
    row['Moeda'] = MOEDAS_DATA.get(pais_upper, "N/A")
    
    # Fallback se não estiver no ficheiro
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
        st.error("Chave API não encontrada nos Secrets!")
        return []

    url = f"https://api.geoapify.com/v2/places?categories={categoria}&filter=circle:{lon},{lat},{dist}&bias=proximity:{lon},{lat}&limit={limite}&apiKey={api_key}"
    
    try:
        response = requests.get(url)
        features = response.json().get("features", [])
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

# --- INTERFACE STREAMLIT ---

st.title("🌍 GeoFinder Pro")

if 'dados' not in st.session_state: st.session_state.dados = None

# Sidebar
with st.sidebar:
    st.header("📍 Parâmetros")
    lat_in = st.number_input("Latitude", value=38.7071, format="%.6f")
    lon_in = st.number_input("Longitude", value=-9.1355, format="%.6f")
    raio = st.number_input("Raio (Metros)", value=1000)
    limit = st.slider("Resultados", 1, 50, 10)
    
    st.divider()
    if PRINCIPAIS:
        escolha_pai = st.selectbox("Categoria", PRINCIPAIS)
        categoria_final = escolha_pai
        if st.checkbox("Sub-categoria"):
            sub = st.selectbox("Detalhe", CATS_DICT.get(escolha_pai, []))
            categoria_final = f"{escolha_pai}.{sub}"
    else:
        categoria_final = "activity"

if st.button("🔍 PESQUISAR"):
    with st.spinner("A processar..."):
        st.session_state.dados = buscar_locais(lon_in, lat_in, raio, categoria_final, limit)
        st.session_state.pos = (lat_in, lon_in)

# Resultados em Abas
if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    st.success(f"Encontrados {len(df)} locais!")

    tab1, tab2, tab3 = st.tabs(["📊 Tabela Completa", "🗺️ Mapa Interativo", "💾 Exportar"])

    with tab1:
        cols = ['Nome', 'Distância (m)', 'Morada', 'Cidade', 'Moeda', 'Hora Local', 'Capital']
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True)

    with tab2:
        m = folium.Map(location=st.session_state.pos, zoom_start=14)
        folium.Marker(st.session_state.pos, popup="Pesquisa", icon=folium.Icon(color='black', icon='home')).add_to(m)
        for _, r in df.iterrows():
            folium.Marker(
                [r['lat'], r['lon']],
                popup=f"<b>{r['Nome']}</b><br>Hora: {r['Hora Local']}",
                tooltip=r['Nome'],
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        st_folium(m, use_container_width=True, height=500, key="mapa_final")

    with tab3:
        st.download_button("📥 Baixar CSV", df.to_csv(index=False).encode('utf-8'), "geofinder_results.csv", "text/csv")