import streamlit as st
import pandas as pd
import requests
from PIL import Image
import pypdf
from google import genai
from fpdf import FPDF
from gtts import gTTS
import matplotlib.pyplot as plt
import io
import json

# Configuração da página
st.set_page_config(
    page_title="Multi-Engine IA: Invenções & Engenharia Pro",
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
    
    # Trata quebras de linha e codificação de caracteres do Português
    linhas = conteudo_texto.split('\n')
    for linha in linhas:
        texto_limpo = linha.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, texto_limpo)
        
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# ==============================================================================
# SIDEBAR: CHAVES DE API E HISTÓRICO DE PROJETOS
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
    
    # --- ABA DE HISTÓRICO NO SIDEBAR ---
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
# FUNÇÕES DE API DAS IAs
# ==============================================================================
def call_gemini(prompt, api_key, model="gemini-3.6-flash"):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text

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
# APICAÇÃO PRINCIPAL POR ABAS
# ==============================================================================
st.title("⚡ Multi-Engine IA: Invenções & Engenharia Pro")

tabs = st.tabs([
    "🧪 Agentes de Invenção", 
    "📐 Blueprint & Desenho de Peças", 
    "📋 Orçamentos Técnicos", 
    "🎬 Gerador de Vídeos & Narração"
])

# ------------------------------------------------------------------------------
# ABA 1: AGENTES DE INVENÇÃO (COM SALVAMENTO DE HISTÓRICO E PDF)
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
                
                # Salvando no Histórico
                st.session_state.historico_projetos.append({
                    "titulo": f"Invenção: {ideia[:20]}...",
                    "tipo": "Invenção",
                    "resumo": r1[:150],
                    "conteudo": dossie_completo
                })

                st.markdown(dossie_completo)

                # Download PDF Direct
                pdf_bytes = criar_pdf("DOSSIE DE INVENCAO", dossie_completo)
                st.download_button("📄 Baixar Dossiê Completo em PDF", data=pdf_bytes, file_name="Dossie_Invention.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"Erro: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 2: BLUEPRINT & DESENHO DE PEÇAS 2D/3D
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
                Regras:
                - Use fundo escuro tipo blueprint (facecolor='#0a192f') e linhas em azul claro ou branco.
                - Inclua dimensões e cotas indicativas no desenho.
                - NÃO coloque explicações ou blocos ```python. Responda APENAS com o código puro.
                """
                try:
                    codigo_python = call_gemini(prompt_draw, gemini_key).replace("```python", "").replace("```", "").strip()
                    
                    # Executa o código de desenho gerado pela IA
                    fig, ax = plt.subplots(figsize=(8, 6))
                    exec_globals = {"plt": plt, "fig": fig, "ax": ax}
                    exec(codigo_python, exec_globals)
                    st.pyplot(plt.gcf())
                    plt.close()
                    st.success("Desenho Técnico Gerado com Sucesso!")
                except Exception as e:
                    st.error(f"Não foi possível desenhar a peça automaticamente. Erro: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 3: ORÇAMENTOS TÉCNICOS
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("📋 Gerador de Orçamentos Técnicos")
    uploaded_files = st.file_uploader("Upload de PDFs/Planilhas/Imagens:", type=["pdf", "xlsx", "csv", "png", "jpg"], accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Processar Orçamento"):
        if not gemini_key:
            st.error("Insira a chave Gemini na barra lateral.")
        else:
            with st.spinner("Analisando documentos..."):
                # Código de leitura simplificado
                txt_anexos = "\n".join([f"Arquivo: {f.name}" for f in uploaded_files])
                prompt_orc = f"Gere um orçamento detalhado com base nesses arquivos:\n{txt_anexos}"
                res_orc = call_gemini(prompt_orc, gemini_key)
                
                st.markdown(res_orc)
                
                # Salva no Histórico
                st.session_state.historico_projetos.append({
                    "titulo": f"Orçamento {uploaded_files[0].name}",
                    "tipo": "Orçamento",
                    "resumo": res_orc[:150],
                    "conteudo": res_orc
                })
                
                pdf_orc = criar_pdf("ORCAMENTO TECNICO", res_orc)
                st.download_button("📄 Baixar Orçamento em PDF", data=pdf_orc, file_name="Orcamento.pdf", mime="application/pdf")

# ------------------------------------------------------------------------------
# ABA 4: VÍDEOS, NARRATIVAS E ÁUDIO MULTIMÍDIA
# ------------------------------------------------------------------------------
with tabs[3]:
    st.subheader("🎬 Gerador de Conteúdo Multimídia (Roteiro + Narração)")
    st.markdown("Crie um roteiro completo de apresentação para a sua invenção com locução automática em MP3.")
    
    topico_video = st.text_input("Tema do Vídeo/Apresentação:", placeholder="Ex: Apresentação comercial do meu novo projeto de robótica")
    idioma = st.selectbox("Idioma da Narração:", ["pt", "en", "es"])

    if st.button("🎬 Criar Roteiro e Gerar Narração em Áudio"):
        if not topico_video:
            st.warning("Digite o tema do vídeo.")
        else:
            with st.spinner("Escrevendo roteiro cinematográfico..."):
                prompt_roteiro = f"Crie um roteiro de vídeo curto (1 minuto) para apresentar o projeto: '{topico_video}'. Divida em [CENA], [ROTEIRO VISUAL] e [LOCUÇÃO]."
                roteiro = call_gemini(prompt_roteiro, gemini_key)
                
                st.markdown("### 📜 Roteiro Sugerido")
                st.markdown(roteiro)
                
            with st.spinner("Sintetizando locução em MP3..."):
                try:
                    # Extrai a locução para áudio com gTTS
                    tts = gTTS(text=roteiro, lang=idioma, slow=False)
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    
                    st.markdown("### 🎙️ Narração do Roteiro Gerada (Áudio MP3)")
                    st.audio(fp, format="audio/mp3")
                    st.download_button("🎵 Baixar Áudio da Locução (.mp3)", data=fp, file_name="locucao_projeto.mp3", mime="audio/mp3")
                except Exception as e:
                    st.error(f"Erro ao gerar áudio: {str(e)}")