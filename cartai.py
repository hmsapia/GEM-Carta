import streamlit as st
import time
from google import genai
from google.genai import types
from datetime import datetime

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
    
    if st.button("🚀 Sincronizar Base de Dados") and arquivos_novos:
        # 1. Criamos a barra de progresso e um texto de status
        progresso_barra = st.progress(0)
        texto_status = st.empty()
        
        refs = []
        total = len(arquivos_novos)

        # 2. Loop de Upload com atualização da barra
        for i, arq in enumerate(arquivos_novos):
            # Atualiza o texto e a barra (valor entre 0.0 e 1.0)
            percentagem = (i + 1) / total
            texto_status.text(f"📤 A enviar ({i+1}/{total}): {arq.name}")
            progresso_barra.progress(percentagem)
            
            # Upload para o Gemini
            ref = client.files.upload(file=arq, config={"mime_type": arq.type})
            refs.append(ref)
        
        # 3. Segunda fase: Indexação (Aguarda os arquivos ficarem 'ACTIVE')
        texto_status.text("🔍 A indexar arquivos no Google AI... (quase pronto)")
        while not all(client.files.get(name=r.name).state.name == "ACTIVE" for r in refs):
            time.sleep(2)
        
        # Guardar na sessão e finalizar
        st.session_state['meu_conhecimento'] = refs
        texto_status.text("✅ Conhecimento pronto!")
        st.success(f"Sucesso! {len(refs)} arquivos carregados.")

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
                with st.spinner("🤖 A analisar..."):
                    try:
                        # Pegamos a hora exata da resposta
                        hora_resp = datetime.now().strftime("%H:%M")
                        
                        contexto = st.session_state['meu_conhecimento']
                        prompt_completo = contexto + [pergunta]

                        res = client.models.generate_content(
                            model="gemini-1.5-flash-002", 
                            config=types.GenerateContentConfig(
                                system_instruction="Responda com base nos arquivos fornecidos.",
                                temperature=0.0
                            ),
                            contents=prompt_completo
                        )
                        
                        # Mostrar e guardar resposta com hora
                        st.caption(f"🕒 {hora_resp}")
                        st.markdown(res.text)
                        st.session_state.mensagens.append({
                            "role": "assistant", 
                            "content": res.text, 
                            "hora": hora_resp
                        })
                        
                    except Exception as e:
                        st.error(f"Erro na consulta: {e}")
