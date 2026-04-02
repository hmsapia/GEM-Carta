import streamlit as st
import time
from google import genai

st.set_page_config(page_title="Admin - Carga Gemini", layout="centered")
st.title("📤 Carregar Base de Conhecimento")

# Configuração da API
# api_key = st.secrets["GEMINI_API_KEY"]
api_key = st.sidebar.text_input("Insere a tua Gemini API Key:", type="password")

if api_key:
    client = genai.Client(api_key=api_key)
    
    # Upload de arquivos via Browser
    arquivos_novos = st.file_uploader("Escolhe os documentos (PDF, TXT, etc.)", 
                                      accept_multiple_files=True)

    if st.button("🚀 Sincronizar com Gemini") and arquivos_novos:
        refs_nomes = []
        progresso = st.progress(0)
        status = st.empty()

        for i, arquivo in enumerate(arquivos_novos):
            status.text(f"A enviar: {arquivo.name}...")
            # O Streamlit passa o arquivo diretamente para a API do Gemini
            ref = client.files.upload(path=arquivo)
            refs_nomes.append(ref.name)
            progresso.progress((i + 1) / len(arquivos_novos))

        # Guardar os IDs num arquivo local para a App de Usuário ler
        with open("database.txt", "w") as f:
            f.write("\n".join(refs_nomes))
        
        status.text("✅ Todos os arquivos foram indexados!")
        st.success(f"Base de conhecimento atualizada com {len(refs_nomes)} arquivos.")
else:
    st.info("Erro na API Key.")