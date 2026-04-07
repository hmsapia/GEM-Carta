import streamlit as st
import os
from google import genai
from google.genai import types

st.set_page_config(page_title="Chat Gemini", page_icon="🤖")
st.title("🤖 Consulta a Carta de Serviços")

#api_key = st.sidebar.text_input("API Key:", type="password")
api_key = st.secrets["GEMINI_API_KEY"]

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

def carregar_contexto(client):
    if not os.path.exists("database.txt"):
        return None
    with open("database.txt", "r") as f:
        nomes = f.read().splitlines()
    return [client.files.get(name=n) for n in nomes]

if api_key:
    client = genai.Client(api_key=api_key)
    
    # Mostrar Histórico
    for msg in st.session_state.mensagens:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Entrada de Pergunta
    if pergunta := st.chat_input("O que desejas saber?"):
        st.session_state.mensagens.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            try:
                contexto = carregar_contexto(client)
                if not contexto:
                    st.error("Nenhum conhecimento carregado. Usa a App Admin primeiro.")
                else:
                    instrucao = "Responda apenas com base nos documentos fornecidos."
                    resposta = client.models.generate_content(
                        model="gemini-1.5-flash",
                        config=types.GenerateContentConfig(system_instruction=instrucao),
                        contents=contexto + [pergunta]
                    )
                    st.markdown(resposta.text)
                    st.session_state.mensagens.append({"role": "assistant", "content": resposta.text})
            except Exception as e:
                st.error(f"Erro: Os ficheiros podem ter expirado (48h). Recarregue no Admin. {e}")