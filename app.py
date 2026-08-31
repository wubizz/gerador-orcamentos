import streamlit as st
import pandas as pd
import requests
from PIL import Image
import pypdf
from google import genai
from fpdf import FPDF
from gtts import gTTS
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import json

# Configuração da página
st.set_page_config(
    page_title="Multi-Engine IA: Invenções, Engenharia & Plano de Corte",
    page_icon="⚡",
    layout="wide"
)

# ==============================================================================
# INICIALIZAÇÃO DO HISTÓRICO DE SESSÃO
# ==============================================================================
if "historico_projetos" not in st.session_state:
    st.session_state.historico_projetos = []

# ==============================================================================
# FUNÇÃO PARA GERAR PDF DOS DOSSIÊS E ORÇAMENTOS
# ==============================================================================
def criar_pdf(titulo, conteudo_texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, titulo.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    
    linhas = conteudo_texto.split('\n')
    for linha in linhas:
        texto_limpo = linha.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, texto_limpo)
        
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# ==============================================================================
# SIDEBAR: CONFIGURAÇÕES E HISTÓRICO DE PROJETOS
# ==============================================================================
with st.sidebar:
    st.header("🔑 Configurações de APIs")
    default_gemini = st.secrets.get("GEMINI_API_KEY", "")
    default_groq = st.secrets.get("GROQ_API_KEY", "")
    default_openrouter = st.secrets.get("OPENROUTER_API_KEY", "")

    gemini_key = st.text_input("1. Gemini API Key:", value=default_gemini, type="password")
    groq_key = st.text_input("2. Groq API Key:", value=default_groq, type="password")
    openrouter_key = st.text_input("3. OpenRouter API Key:", value=default_openrouter, type="password")
    
    st.divider()
    
    st.header("📁 Pastas de Projetos")
    if st.session_state.historico_projetos:
        for idx, item in enumerate(st.session_state.historico_projetos):
            with st.expander(f"📌 {item['titulo']}"):
                st.caption(f"Tipo: {item['tipo']}")
                st.write(item['resumo'][:100] + "...")
                pdf_data = criar_pdf(item['titulo'], item['conteudo'])
                st.download_button(
                    "📄 Baixar PDF",
                    data=pdf_data,
                    file_name=f"{item['titulo'].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"btn_pdf_{idx}"
                )
    else:
        st.info("Nenhum projeto salvo na sessão.")

# ==============================================================================
# FUNÇÕES DE API COM TRATAMENTO DE ERRO 503 (FALLBACK AUTOMÁTICO)
# ==============================================================================
def call_gemini(prompt, api_key, model="gemini-3.6-flash"):
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "high demand" in error_msg.lower():
            fallback_model = "gemini-1.5-flash"
            st.warning(f"⚠️ O modelo principal ({model}) está com alta demanda. Utilizando o modelo de reserva ({fallback_model})...")
            try:
                response_fallback = client.models.generate_content(model=fallback_model, contents=prompt)
                return response_fallback.text
            except Exception as e2:
                raise Exception(f"Erro no modelo de reserva: {str(e2)}")
        else:
            raise e

def call_groq(prompt, api_key, model="llama-3.3-70b-versatile"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code == 200:
        return res.json()['choices'][0]['message']['content']
    raise Exception(f"Erro Groq: {res.text}")

def call_openrouter_free(prompt, api_key, model="meta-llama/llama-3.3-70b-instruct:free"):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code == 200:
        return res.json()['choices'][0]['message']['content']
    raise Exception(f"Erro OpenRouter: {res.text}")

# ==============================================================================
# NAVEGAÇÃO PRINCIPAL POR ABAS
# ==============================================================================
st.title("⚡ Multi-Engine IA: Invenções & Engenharia Pro")

tabs = st.tabs([
    "🧪 Agentes de Invenção", 
    "📐 Blueprint & Peças", 
    "📋 Orçamentos Técnicos", 
    "✂️ Otimizador de Corte (Nesting)",
    "🎬 Vídeos & Narração"
])

# ------------------------------------------------------------------------------
# ABA 1: AGENTES DE INVENÇÃO
# ------------------------------------------------------------------------------
with tabs[0]:
    st.subheader("Laboratório Multiagente de Prototipagem")
    
    col1, col2 = st.columns(2)
    with col1:
        provedor = st.selectbox("Provedor dos Agentes:", ["Google Gemini", "Groq (Llama 3.3)", "OpenRouter Free"])
    with col2:
        area_projeto = st.selectbox("Área:", ["Engenharia Química", "Mecânica/Robótica", "Eletrônica/IoT", "Biotecnologia"])
        
    ideia = st.text_area("Descreva a ideia:", placeholder="Ex: Válvula de retenção biomimética automatizada...")

    if st.button("🚀 Processar Invenção", type="primary"):
        if not ideia.strip():
            st.warning("Preencha a ideia primeiro.")
        else:
            try:
                def exec_agente(p):
                    if "Gemini" in provedor: return call_gemini(p, gemini_key)
                    elif "Groq" in provedor: return call_groq(p, groq_key)
                    else: return call_openrouter_free(p, openrouter_key)

                with st.status("🕵️ Agente 1 (Pesquisador): Verificando viabilidade...", expanded=True):
                    r1 = exec_agente(f"Pesquisador Científico em {area_projeto}. Analise viabilidade de: {ideia}")
                with st.status("⚙️ Agente 2 (Engenheiro): Criando especificações...", expanded=True):
                    r2 = exec_agente(f"Engenheiro. Com base no parecer:\n{r1}\nElabore o projeto técnico detalhado.")
                with st.status("🛠️ Agente 3 (Maker): Gerando Lista de Materiais...", expanded=True):
                    r3 = exec_agente(f"Maker. Com base no projeto:\n{r2}\nCrie a Lista de Materiais e passos de montagem.")

                st.success("Dossiê Gerado!")
                dossie_completo = f"DOSSIÊ TÉCNICO: {ideia[:30]}\n\n--- 1. VIABILIDADE ---\n{r1}\n\n--- 2. PROJETO ---\n{r2}\n\n--- 3. MATERIAIS ---\n{r3}"
                
                st.session_state.historico_projetos.append({
                    "titulo": f"Invenção: {ideia[:20]}...",
                    "tipo": "Invenção",
                    "resumo": r1[:150],
                    "conteudo": dossie_completo
                })

                st.markdown(dossie_completo)

                pdf_bytes = criar_pdf("DOSSIE DE INVENCAO", dossie_completo)
                st.download_button("📄 Baixar Dossiê Completo em PDF", data=pdf_bytes, file_name="Dossie_Invention.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"Erro: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 2: BLUEPRINT & DESENHO DE PEÇAS
# ------------------------------------------------------------------------------
with tabs[1]:
    st.subheader("📐 Gerador de Desenhos Técnicos e Esquema de Peças")
    st.markdown("Forneça a descrição da peça ou mecanismo para a IA gerar as cotas e o desenho técnico.")
    
    descricao_peca = st.text_input("Descrição da peça:", placeholder="Ex: Engrenagem reta de 12 dentes com furo central de 8mm")
    
    if st.button("🎨 Gerar Desenho Técnico 2D"):
        if not descricao_peca:
            st.warning("Descreva a peça primeiro.")
        else:
            with st.spinner("Desenhando esquemático com cotas técnicas..."):
                prompt_draw = f"""
                Atue como um gerador de gráficos Python (Matplotlib).
                Crie APENAS um código Python funcional que use matplotlib.pyplot para desenhar um esquema técnico 2D cotado da peça: '{descricao_peca}'.
                
                REGRAS OBRIGATÓRIAS:
                - Defina o tamanho da figura obrigatoriamente como: fig, ax = plt.subplots(figsize=(10, 6))
                - Use fundo escuro estilo blueprint (facecolor='#0a192f') no fig e ax.
                - Use linhas e textos em branco ou azul claro (ex: '#00d2ff').
                - Inclua dimensões e cotas indicativas no desenho.
                - NUNCA use plt.tight_layout().
                - NÃO coloque explicações ou blocos ```python. Responda APENAS com o código puro.
                """
                try:
                    codigo_python = call_gemini(prompt_draw, gemini_key).replace("```python", "").replace("```", "").strip()
                    plt.close('all')
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    exec_globals = {"plt": plt, "fig": fig, "ax": ax}
                    
                    exec(codigo_python, exec_globals)
                    
                    st.pyplot(plt.gcf(), use_container_width=True)
                    plt.close('all')
                    st.success("Desenho Técnico Gerado com Sucesso!")
                except Exception as e:
                    plt.close('all')
                    st.error(f"Não foi possível desenhar a peça automaticamente. Erro: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 3: ORÇAMENTOS TÉCNICOS (INTEGRADA COM DESENHOS DE PEÇAS)
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("📋 Gerador de Orçamentos Técnicos & Análise Visual")
    
    scale_info = st.text_input("Referência de medida/escala (Ex: O vão principal tem 3.50m):", placeholder="Informe a referência se houver...")
    uploaded_files = st.file_uploader("Upload de PDFs/Planilhas/Imagens:", type=["pdf", "xlsx", "csv", "png", "jpg", "jpeg"], accept_multiple_files=True, key="orc_files")

    if uploaded_files:
        prompt_orcamento = f"""
        Você é um Engenheiro Orçamentista.
        Examine os arquivos anexados.
        {f"ESCALA DE REFERÊNCIA: {scale_info}" if scale_info else ""}

        Gere um ORÇAMENTO TÉCNICO COMPLETO contendo:
        1. Resumo Executivo
        2. Tabela de Quantitativo de Materiais e Peças
        3. Resumo Financeiro Final
        
        IMPORTANTE: Ao final da resposta, inclua obrigatoriamente um bloco JSON estrito no seguinte formato listando as 3 a 5 principais peças/componentes estruturais para desenho técnico:
        ```json
        {{
          "pecas_para_desenho": [
            {{"nome": "Nome da Peça 1", "descricao": "Descrição técnica da Peça 1 com dimensões estimadas"}},
            {{"nome": "Nome da Peça 2", "descricao": "Descrição técnica da Peça 2 com dimensões estimadas"}}
          ]
        }}