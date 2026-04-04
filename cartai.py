import streamlit as st
import time
import os
import tempfile
import langchain
from google import genai
from google.genai import types
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

st.set_page_config(page_title="Meu Gem Particular", layout="wide")

# --- LOGIN / CONFIGURAÇÃO ---
with st.sidebar:
    st.title("🔑 Acesso")
    api_key = st.text_input("Gemini API Key:", type="password")
    if not api_key:
        st.info("Insira a chave para liberar as funções.")
        st.stop()

client = genai.Client(api_key=api_key)

# Criamos as abas para separar as funções
tab_admin, tab_chat = st.tabs(["📤 Carregar Base de Conhecimento", "💬 Conversar com o Gem"])

# --- ABA 1: ADMIN (CARGA) ---
with tab_admin:
    st.header("Gestão de Documentos")
    arquivos_novos = st.file_uploader("Upload de arquivos:", accept_multiple_files=True)
    
    if st.button("🚀 Sincronizar Base de Dados") and arquivos_novos:
        progresso_barra = st.progress(0)
        texto_status = st.empty()
        
        all_docs = []
        # Configuração do modelo de Embeddings (transforma texto em números)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
        
        for i, arq in enumerate(arquivos_novos):
            texto_status.text(f"📖 Processando: {arq.name}")
            
            # Salva temporariamente para o Loader do LangChain conseguir ler
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(arq.getvalue())
                loader = PyPDFLoader(tmp.name)
                all_docs.extend(loader.load())
            os.unlink(tmp.name) # Remove arquivo temporário
            
            progresso_barra.progress((i + 1) / len(arquivos_novos))

        # Divisão em pedaços (Chunks) para a busca ser precisa
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(all_docs)
        
        # Criação do banco de dados vetorial (FAISS)
        texto_status.text("🧠 Criando base de conhecimento inteligente...")
        vector_db = FAISS.from_documents(chunks, embeddings)
        
        # Guardar o banco na sessão
        st.session_state['vector_db'] = vector_db
        st.success(f"✅ Base pronta! {len(chunks)} trechos indexados.")

# --- ABA 2: CHAT (CONSULTA) ---
with tab_chat:
    st.header("💬 Consulta Carta de Serviços")
    
    if 'meu_conhecimento' not in st.session_state:
        st.warning("⚠️ Vai à aba 'Carregar Conhecimento' primeiro.")
    else:
        # Inicializar histórico se não existir
        if "mensagens" not in st.session_state:
            st.session_state.mensagens = []

        # 2. Mostrar Histórico com Horas
        for msg in st.session_state.mensagens:
            with st.chat_message(msg["role"]):
                # Criamos uma linha pequena com a hora e o conteúdo
                st.caption(f"🕒 {msg['hora']}") 
                st.markdown(msg["content"])

        # 3. Entrada de Pergunta
        if pergunta := st.chat_input("Pergunta algo..."):
            agora = datetime.now().strftime("%H:%M") # FORMATO: 14:30
            
            # Guardar pergunta do utilizador com hora
            st.session_state.mensagens.append({
                "role": "user", 
                "content": pergunta, 
                "hora": agora
            })
            
            with st.chat_message("user"):
                st.caption(f"🕒 {agora}")
                st.markdown(pergunta)

            # 4. Gerar Resposta do Assistente
            with st.chat_message("assistant"):
                placeholder = st.empty() # Espaço para a resposta ir "brotando"
                full_response = ""
                with st.spinner("⚡ A processar..."):
                    try:
                        # 1. Recuperar trechos relevantes (Top 5 trechos)
                        vector_db = st.session_state['vector_db']
                        docs_relevantes = vector_db.similarity_search(pergunta, k=5)
                        contexto_extraido = "\n\n".join([doc.page_content for doc in docs_relevantes])
                        
                        # 2. Montar o Prompt RAG
                        prompt_rag = f"""
                        CONTEXTO DOS DOCUMENTOS:
                        {contexto_extraido}
                        
                        PERGUNTA DO MUNÍCIPE:
                        {pergunta}
                        """

                        instrucao = """
                        Você é servidor público do Município de Presidente Prudente.
                        Responda usando APENAS o contexto fornecido acima. 
                        Se a resposta não estiver no contexto, diga que não localizou a informação.
                        """

                        # 3. Chamada ao Gemini (agora com prompt leve e rápido)
                        responses = client.models.generate_content_stream(
                            model="gemini-1.5-flash", # Flash é ideal para RAG pela velocidade
                            contents=[prompt_rag],
                            config=types.GenerateContentConfig(
                                system_instruction=instrucao,
                                temperature=0.0)
                        )
                        
                        for chunk in responses:
                            full_response += chunk.text
                            # Atualiza a tela em tempo real
                            placeholder.markdown(full_response + "▌")
        
                        placeholder.markdown(full_response) # Finaliza sem o cursor

                        # Pegamos a hora exata da resposta
                        hora_resp = datetime.now().strftime("%H:%M")

                        # Mostrar e guardar resposta com hora
                        st.caption(f"🕒 {hora_resp}")
                        #st.markdown(res.text)
                        st.session_state.mensagens.append({
                            "role": "assistant", 
                            "content": full_response, 
                            "hora": hora_resp
                        })
                        
                    except Exception as e:
                        st.error(f"Erro na consulta: {e}")
