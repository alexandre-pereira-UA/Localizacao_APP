import sys
import requests
import json
import pandas as pd
from pprint import pprint
from colorama import Fore, Style
import csv
import os

# Função para carregar a API Key de forma segura
def get_api_key():
    try:
        import streamlit as st
        return st.secrets["GEOAPIFY_KEY"]
    except:
        return "682be55d456c44919e284b09e0a9b8d2" 

API_KEY = get_api_key()

def bemvindo() :
    print(f"\n{Fore.CYAN}Bem-vindo à aplicação GeoMotor{Style.RESET_ALL}")
    print("\nInstruções: Use pontos para decimais. Latitude (-90 a 90), Longitude (-180 a 180).")

def escolhas_utilizador_cord_dis(msg, v_min, v_max):
    while True:
        try:
            val = float(input(msg).strip())
            if v_min <= val <= v_max: return val
            print(f"Valor fora do intervalo ({v_min} a {v_max})")
        except: print("Entrada inválida. Digite um número.")

def distancia_viajar():
    while True:
        try:
            val = abs(float(input("\nDistância em metros: ")))
            return val
        except: print("Digite um número válido.")

def category_selector():
    categorias = {}
    with open('categories.txt', 'r', encoding="UTF-8") as f:
        for line in f:
            line = line.strip()
            if '.' in line:
                pai = line.split('.')[0]
                if pai not in categorias: categorias[pai] = []
                categorias[pai].append(line)
    
    pprint(sorted(list(categorias.keys())))
    escolha = input("\nEscolha a categoria principal (ex: accommodation): ").lower()
    
    if escolha in categorias:
        print("\nSub-categorias disponíveis:")
        pprint(categorias[escolha])
        sub = input("Escolha a sub-categoria completa ou prima Enter para tudo: ")
        return sub if sub in categorias[escolha] else escolha
    return escolha

def o_que_queres(lon, lat, dis, es, sit):
    mapeamento = {
        'name': 'Nome', 'country': 'País', 'city': 'Cidade', 
        'street': 'Rua', 'distance': 'Distância(m)', 'formatted': 'Morada'
    }
    
    url = f"https://api.geoapify.com/v2/places?categories={es}&filter=circle:{lon},{lat},{dis}&limit={sit}&apiKey={API_KEY}"
    
    try:
        data = requests.get(url).json()
        resultados = []
        for c in data.get("features", []):
            prop = c.get("properties", {})
            traduzido = {mapeamento.get(k, k): v for k, v in prop.items() if k in mapeamento}
            resultados.append(traduzido)
            
        for r in resultados:
            print("-" * 30)
            for k, v in r.items(): print(f"{k}: {v}")
        return resultados
    except Exception as e:
        print(f"Erro: {e}")

def main():
    bemvindo()
    while True:
        lat = escolhas_utilizador_cord_dis("\nLatitude: ", -90, 90)
        lon = escolhas_utilizador_cord_dis("Longitude: ", -180, 180)
        dist = distancia_viajar()
        cat = category_selector()
        qtd = input("Quantas sugestões? ")
        
        o_que_queres(lon, lat, dist, cat, qtd)
        
        if input("\nContinuar? (s/n): ").lower() != 's': break

if __name__ == "__main__":
    main()