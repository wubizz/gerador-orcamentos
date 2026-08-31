import streamlit as st
import pandas as pd
import requests
from PIL import Image
import pypdf
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Multi-AI Online Engine",
    page_icon="🤖",
    layout="wide"
)

# Sidebar para chaves de API
with st.sidebar:
    st.header("🔑 Chaves de API Gratuitas (Nuvem)")
    gemini_key = st.text_input("1. Google Gemini API Key:", type="password")
    groq_key = st.text_input("2. Groq API Key:", type="password")
    openrouter_key = st.text_input("3. OpenRouter API Key (Opcional):", type="password")
    hf_key = st.text_input("4. Hugging Face Token (Opcional):", type="password")
    
    st.divider()
    st.markdown("""
    **Links para obter as chaves grátis:**
    * [Google AI Studio](https://aistudio.google.com/)
    * [Groq Cloud](https://console.groq.com/)
    * [OpenRouter](https://openrouter.ai/)
    * [Hugging Face](https://huggingface.co/settings/tokens)
    """)

# Funções para chamada das APIs gratuitas online
def call_gemini(prompt, api_key, model="gemini-2.5-flash"):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text

def call_groq(prompt, api_key, model="llama-3.3-70b-versatile"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code == 200:
        return res.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Erro Groq: {res.text}")

def call_openrouter_free(prompt, api_key, model="meta-llama/llama-3.3-70b-instruct:free"):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code == 200:
        return res.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Erro OpenRouter: {res.text}")

# Interface Principal
st.title("⚡ Multi-Engine IA: Invenções & Engenharia Online")
st.caption("Rode modelos Open Source e proprietários diretamente na nuvem (sem necessidade de GPU local)")

tabs = st.tabs(["🧪 Gerador Multiagente", "💬 Teste de Provedores de IA"])

with tabs[0]:
    st.subheader("Agentes Autônomos de Invenção")
    
    col_prov, col_area = st.columns(2)
    with col_prov:
        provedor = st.selectbox(
            "Selecione o Provedor Cloud dos Agentes:",
            ["Google Gemini (Recomendado)", "Groq (Llama 3.3 70B)", "OpenRouter Free"]
        )
    with col_area:
        area_projeto = st.selectbox(
            "Área do Projeto:",
            ["Engenharia Química / Cosméticos", "Engenharia Mecânica", "Eletrônica / IoT", "Biotecnologia"]
        )
        
    ideia = st.text_area("Descreva a ideia da invenção:", height=120)

    if st.button("🚀 Processar com Agentes Cloud", type="primary"):
        if not ideia.strip():
            st.warning("Por favor, digite a ideia.")
        else:
            try:
                # Função de roteamento para a API escolhida
                def executar_agente(prompt):
                    if "Gemini" in provedor:
                        if not gemini_key: raise Exception("Insira a chave do Gemini na sidebar.")
                        return call_gemini(prompt, gemini_key)
                    elif "Groq" in provedor:
                        if not groq_key: raise Exception("Insira a chave do Groq na sidebar.")
                        return call_groq(prompt, groq_key)
                    elif "OpenRouter" in provedor:
                        if not openrouter_key: raise Exception("Insira a chave do OpenRouter na sidebar.")
                        return call_openrouter_free(prompt, openrouter_key)

                with st.status("🕵️ Agente 1 (Pesquisador): Verificando viabilidade...", expanded=True):
                    p1 = f"Atue como Pesquisador Sênior na área {area_projeto}. Analise a viabilidade técnica de: {ideia}"
                    r1 = executar_agente(p1)
                
                with st.status("⚙️ Agente 2 (Engenheiro): Criando especificação técnica...", expanded=True):
                    p2 = f"Atue como Engenheiro de Projetos. Com base na análise: {r1}. Elabore a especificação/formulação detalhada."
                    r2 = executar_agente(p2)

                with st.status("🛠️ Agente 3 (Maker): Gerando BOM e protótipo...", expanded=True):
                    p3 = f"Atue como Especialista em Prototipagem. Com base em: {r2}. Liste materiais (BOM) e passos para montar o protótipo."
                    r3 = executar_agente(p3)

                st.success("Dossiê gerado com sucesso na nuvem!")
                st.markdown("### 🔬 Parecer de Viabilidade")
                st.write(r1)
                st.markdown("### ⚙️ Projeto Técnico")
                st.write(r2)
                st.markdown("### 🛠️ Materiais e Protótipo")
                st.write(r3)

            except Exception as e:
                st.error(f"Erro na execução: {str(e)}")

with tabs[1]:
    st.subheader("Testar Modelo Específico no Browser")
    prompt_teste = st.text_input("Pergunta para o modelo:")
    modelo_sel = st.selectbox("Escolha o modelo:", [
        "Gemini 2.5 Flash (Google)",
        "Llama 3.3 70B (Groq)",
        "DeepSeek R1 Free (OpenRouter)",
        "Qwen 2.5 Coder Free (OpenRouter)"
    ])
    
    if st.button("Enviar Consulta"):
        if prompt_teste:
            try:
                if "Gemini" in modelo_sel:
                    res = call_gemini(prompt_teste, gemini_key)
                elif "Groq" in modelo_sel:
                    res = call_groq(prompt_teste, groq_key)
                elif "DeepSeek" in modelo_sel:
                    res = call_openrouter_free(prompt_teste, openrouter_key, "deepseek/deepseek-r1:free")
                elif "Qwen" in modelo_sel:
                    res = call_openrouter_free(prompt_teste, openrouter_key, "qwen/qwen-2.5-coder-32b-instruct:free")
                
                st.markdown("**Resposta:**")
                st.write(res)
            except Exception as e:
                st.error(f"Erro: {str(e)}")