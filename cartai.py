import streamlit as st
import time
from google import genai
from google.genai import types

st.set_page_config(page_title="Meu Gem Particular", layout="wide")

# --- LOGIN / CONFIGURAÇÃO ---
with st.sidebar:
    st.title("🔑 Acesso")
    api_key = st.text_input("Gemini API Key:", type="password")
    if not api_key:
        st.info("Insira a chave para libertar as funções.")
        st.stop()

client = genai.Client(api_key=api_key)

# Criamos as abas para separar as funções
tab_admin, tab_chat = st.tabs(["📤 Carregar Base de Conhecimento", "💬 Conversar com o Gem"])

# --- ABA 1: ADMIN (CARGA) ---
with tab_admin:
    st.header("Gestão de Documentos")
    arquivos_novos = st.file_uploader("Upload de arquivos:", accept_multiple_files=True)
    
    # Código para listar modelos disponíveis para a sua chave
    for m in client.models.list():
        st.write(f"ID: {m.name} | Suporta: {m.supported_actions}")


    if st.button("🚀 Sincronizar Base de Dados") and arquivos_novos:
        with st.status("A processar documentos...") as status:
            refs = []
            for arq in arquivos_novos:
                # Corrigido com o mime_type que resolvemos antes
                ref = client.files.upload(file=arq, config={"mime_type": arq.type})
                refs.append(ref)
            
            # Esperar indexação
            while not all(client.files.get(name=r.name).state.name == "ACTIVE" for r in refs):
                time.sleep(2)
            
            # GUARDAR NA MEMÓRIA DA SESSÃO
            st.session_state['meu_conhecimento'] = refs
            status.update(label="✅ Conhecimento pronto!", state="complete")
        st.success(f"{len(refs)} arquivos prontos para o chat!")

# --- ABA 2: CHAT (CONSULTA) ---
with tab_chat:
    st.header("Consulta Carta de Serviços")
    
    if 'meu_conhecimento' not in st.session_state:
        st.warning("⚠️ Vai à aba 'Carregar Conhecimento' primeiro.")
    else:
        # Histórico de Chat
        if "mensagens" not in st.session_state:
            st.session_state.mensagens = []

        for msg in st.session_state.mensagens:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if pergunta := st.chat_input("Pergunta algo..."):
            st.session_state.mensagens.append({"role": "user", "content": pergunta})
            with st.chat_message("user"):
                st.markdown(pergunta)

            with st.chat_message("assistant"):
                try:
                    res = client.models.generate_content(
                        model="gemini-1.5-flash-002",
                        config=types.GenerateContentConfig(
                            system_instruction="Responda com base nos arquivos fornecidos."
                        ),
                        contents=st.session_state['meu_conhecimento'] + [pergunta]
                    )
                    st.markdown(res.text)
                    st.session_state.mensagens.append({"role": "assistant", "content": res.text})
                except Exception as e:
                    st.error(f"Erro na consulta: {e}")