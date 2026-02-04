# 🌍 GeoFinder Pro

O **GeoFinder Pro** é uma aplicação de geolocalização que permite descobrir pontos de interesse em qualquer parte do mundo, fornecendo dados contextuais ricos como hora local, moeda, capital e visualização interativa em mapas.

---

## 🚀 Funcionalidades Principais

- **Interface Web Interativa**: Desenvolvida com Streamlit para uma experiência de utilizador fluida.
- **Mapa com Pins**: Visualização exata dos locais com marcadores personalizados (Pins) e popups.
- **Cálculo de Hora Local**: Exibe a hora atual do local pesquisado (formato 24h e AM/PM) ajustada ao fuso horário real.
- **Informação de Moedas**: Identificação automática da moeda do país (através de base de dados local e API).
- **Dados do País**: Consulta automática da capital e informações geográficas.
- **Exportação de Dados**: Permite descarregar todos os resultados da pesquisa num ficheiro `.csv`.
- **Modo Terminal**: Inclui um motor secundário (`motor.py`) para consultas rápidas via linha de comandos.

---

## 📂 Ficheiros de Dados (.txt)

A aplicação é dinâmica e lê os seguintes ficheiros para funcionar:

1.  **`categories.txt`**: Define as categorias de pesquisa (ex: hotéis, restaurantes, farmácias). Se adicionares novas categorias neste ficheiro, elas aparecerão automaticamente no menu do site.
2.  **`moedas.txt.txt`**: Um dicionário estruturado que mapeia nomes de países às suas moedas oficiais. É utilizado para garantir que sabes sempre que moeda levar para o local pesquisado.

---

## 🛠️ Instalação e Configuração

### 1. Obter a API Key
Este projeto utiliza a API da **Geoapify**.
1. Cria uma conta gratuita em [Geoapify MyProjects](https://myprojects.geoapify.com/).
2. Cria um novo projeto e copia a tua **API Key**.

### 2. Instalar Bibliotecas (CMD/Terminal)
Executa o seguinte comando para instalar todas as dependências:

```bash
pip install streamlit requests pandas folium streamlit-folium timezonefinder countryinfo pycountry pytz

👥 Autores
Alexandre Pereira — Nº 119871
Alexandre Ferreira — Nº 120527