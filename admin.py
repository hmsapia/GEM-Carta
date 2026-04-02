import streamlit as st
import time
from google import genai

st.set_page_config(page_title="Admin - Carga Gemini", icon="📤")
st.title("📤 Carregador de Conhecimento")

# Configuração da API
api_key = st.sidebar.text_input("Insere a tua Gemini API Key:", type="password")

if api_key:
    client = genai.Client(api_key=api_key)
    
    # Upload de ficheiros via Browser
    ficheiros_novos = st.file_uploader("Escolhe os documentos (PDF, TXT, etc.)", 
                                      accept_multiple_files=True)

    if st.button("🚀 Sincronizar com Gemini") and ficheiros_novos:
        refs_nomes = []
        progresso = st.progress(0)
        status = st.empty()

        for i, arquivo in enumerate(ficheiros_novos):
            status.text(f"A enviar: {arquivo.name}...")
            # O Streamlit passa o ficheiro diretamente para a API do Gemini
            ref = client.files.upload(path=arquivo)
            refs_nomes.append(ref.name)
            progresso.progress((i + 1) / len(ficheiros_novos))

        # Guardar os IDs num ficheiro local para a App de Usuário ler
        with open("database.txt", "w") as f:
            f.write("\n".join(refs_nomes))
        
        status.text("✅ Todos os ficheiros foram indexados!")
        st.success(f"Base de conhecimento atualizada com {len(refs_nomes)} ficheiros.")
else:
    st.info("Por favor, insere a tua API Key na barra lateral para começar.")