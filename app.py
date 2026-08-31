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
# SIDEBAR
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
# FUNÇÕES DE API DAS IAs
# ==============================================================================
def call_gemini(prompt, api_key, model="gemini-3.6-flash"):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text

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
    ideia = st.text_area("Descreva a ideia:", placeholder="Ex: Válvula de retenção biomimética automatizada...")

    if st.button("🚀 Processar Invenção", type="primary"):
        if not ideia.strip():
            st.warning("Preencha a ideia primeiro.")
        else:
            try:
                with st.status("🕵️ Agente 1: Verificando viabilidade...", expanded=True):
                    r1 = call_gemini(f"Pesquisador Científico. Analise viabilidade de: {ideia}", gemini_key)
                with st.status("⚙️ Agente 2: Criando especificações...", expanded=True):
                    r2 = call_gemini(f"Engenheiro. Com base no parecer:\n{r1}\nElabore o projeto técnico detalhado.", gemini_key)
                with st.status("🛠️ Agente 3: Gerando Lista de Materiais...", expanded=True):
                    r3 = call_gemini(f"Maker. Com base no projeto:\n{r2}\nCrie a Lista de Materiais e passos de montagem.", gemini_key)

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
    st.subheader("📐 Gerador de Desenhos Técnicos")
    descricao_peca = st.text_input("Descrição da peça:", placeholder="Ex: Engrenagem reta de 12 dentes com furo central de 8mm")
    
    if st.button("🎨 Gerar Desenho Técnico 2D"):
        if not descricao_peca:
            st.warning("Descreva a peça primeiro.")
        else:
            with st.spinner("Desenhando esquemático com cotas técnicas..."):
                prompt_draw = f"""
                Atue como um gerador de gráficos Python (Matplotlib).
                Crie APENAS um código Python funcional que use matplotlib.pyplot para desenhar um esquema técnico 2D cotado da peça: '{descricao_peca}'.
                REGRAS:
                - Defina o tamanho da figura como: fig, ax = plt.subplots(figsize=(10, 6))
                - Use fundo escuro estilo blueprint (facecolor='#0a192f') no fig e ax.
                - Use linhas e textos em branco ou azul claro (ex: '#00d2ff').
                - Inclua dimensões e cotas indicativas no desenho.
                - NUNCA use plt.tight_layout().
                - Responda APENAS com código puro.
                """
                try:
                    codigo_python = call_gemini(prompt_draw, gemini_key).replace("```python", "").replace("```", "").strip()
                    plt.close('all')
                    fig, ax = plt.subplots(figsize=(10, 6))
                    exec_globals = {"plt": plt, "fig": fig, "ax": ax}
                    exec(codigo_python, exec_globals)
                    st.pyplot(plt.gcf(), use_container_width=True)
                    plt.close('all')
                except Exception as e:
                    plt.close('all')
                    st.error(f"Erro no desenho: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 3: ORÇAMENTOS TÉCNICOS
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("📋 Gerador de Orçamentos Técnicos")
    uploaded_files = st.file_uploader("Upload de PDFs/Planilhas/Imagens:", type=["pdf", "xlsx", "csv", "png", "jpg"], accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Processar Orçamento"):
        with st.spinner("Analisando documentos..."):
            txt_anexos = "\n".join([f"Arquivo: {f.name}" for f in uploaded_files])
            res_orc = call_gemini(f"Gere um orçamento detalhado com base nesses arquivos:\n{txt_anexos}", gemini_key)
            st.markdown(res_orc)
            
            st.session_state.historico_projetos.append({
                "titulo": f"Orçamento {uploaded_files[0].name}",
                "tipo": "Orçamento",
                "resumo": res_orc[:150],
                "conteudo": res_orc
            })
            
            pdf_orc = criar_pdf("ORCAMENTO TECNICO", res_orc)
            st.download_button("📄 Baixar Orçamento em PDF", data=pdf_orc, file_name="Orcamento.pdf", mime="application/pdf")

# ------------------------------------------------------------------------------
# ABA 4: OTIMIZADOR DE PLANO DE CORTE (NESTING)
# ------------------------------------------------------------------------------
with tabs[3]:
    st.subheader("✂️ Otimizador de Plano de Corte & Nesting de Materiais")
    st.markdown("Calcule a quantidade exata de chapas/barras necessárias para o seu projeto com diagrama visual do corte.")

    col_mat, col_esp = st.columns(2)
    with col_mat:
        tipo_material = st.selectbox(
            "Tipo de Matéria-Prima:",
            ["MDF / Madeira (Chapa Padrão 2750 x 1850 mm)", 
             "Tubos / Cantoneiras / Perfis (Barra de 6000 mm)", 
             "Chapas Metálicas em Geral (Dimensão Personalizada)"]
        )

    # Definição das dimensões brutas da matéria-prima com base na seleção
    if "MDF" in tipo_material:
        largura_bruta = 2750
        comprimento_bruto = 1850
        st.info(f"📏 Dimensão da Chapa Padrão de MDF: **{largura_bruta} x {comprimento_bruto} mm**")
    elif "Tubos" in tipo_material:
        largura_bruta = 6000
        comprimento_bruto = 0 # 0 indica perfil unidimensional/barra
        st.info(f"📏 Comprimento Padrão da Barra: **{largura_bruta} mm (6 metros)**")
    else:
        with col_esp:
            largura_bruta = st.number_input("Largura da Chapa do Fornecedor (mm):", min_value=100, value=3000, step=50)
            comprimento_bruto = st.number_input("Comprimento da Chapa do Fornecedor (mm):", min_value=100, value=1500, step=50)
            st.caption(f"📏 Dimensão Personalizada da Chapa: **{largura_bruta} x {comprimento_bruto} mm**")

    st.divider()
    st.markdown("### 📋 Digite a Lista de Peças a Cortar")
    
    lista_pecas_input = st.text_area(
        "Forneça a lista de peças no formato (Peça, Largura_mm, Comprimento_mm, Quantidade):",
        height=120,
        placeholder="Exemplo para Chapas:\nLateral, 500, 1800, 2\nTampa, 600, 800, 1\nFundo, 500, 750, 2\n\nExemplo para Tubos/Barra:\nTubo_Base, 1200, 0, 4\nTubo_Coluna, 850, 0, 8"
    )

    espessura_disco = st.number_input("Espessura da serra/largura do corte (Kerf em mm):", min_value=0.0, value=3.0, step=0.5)

    if st.button("✂️ Calcular Plano de Corte e Gerar Diagrama", type="primary"):
        if not lista_pecas_input.strip():
            st.warning("Preencha a lista de peças antes de prosseguir.")
        else:
            with st.spinner("Calculando o aproveitamento e gerando plano de otimização..."):
                prompt_corte = f"""
                Atue como Engenheiro de Processos especialista em Nesting de Corte.
                
                DADOS DA MATÉRIA-PRIMA:
                - Tipo: {tipo_material}
                - Largura Bruta: {largura_bruta} mm
                - Comprimento Bruto: {comprimento_bruto} mm (Se for 0, considerar perfil linear de {largura_bruta} mm)
                - Perda na Serra (Kerf): {espessura_disco} mm
                
                LISTA DE PEÇAS REQUISITADAS:
                {lista_pecas_input}
                
                Gere um relatório detalhado de aproveitamento contendo:
                1. Quantidade total de Chapas/Barras inteiras necessárias.
                2. Percentual de Aproveitamento de Área/Comprimento (%) e % de Retalho/Sobra.
                3. Instruções passo a passo da sequência dos cortes.
                4. Código Matplotlib embutido puro para desenhar a disposição das peças na chapa/barra.
                """
                
                try:
                    res_corte = call_gemini(prompt_corte, gemini_key)
                    st.markdown("### 📊 Relatório de Otimização de Corte")
                    st.markdown(res_corte)
                    
                    # Tenta desenhar o diagrama visual de corte
                    prompt_draw_nesting = f"""
                    Crie APENAS um código Python (Matplotlib) funcional para desenhar a disposição gráfica dos retângulos/barras de corte das peças:
                    Mátéria-Prima: {largura_bruta}x{comprimento_bruto}mm. Peças: {lista_pecas_input}.
                    
                    REGRAS OBRIGATÓRIAS:
                    - Desenhe os retângulos da chapa ({largura_bruta}x{comprimento_bruto}) com fundo cinza escuro.
                    - Desenhe as peças posicionadas com cores vivas e rótulos do nome da peça e dimensão.
                    - Use fig, ax = plt.subplots(figsize=(10, 6))
                    - NUNCA use plt.tight_layout().
                    - Responda APENAS com código puro, sem ```python.
                    """
                    codigo_nesting = call_gemini(prompt_draw_nesting, gemini_key).replace("```python", "").replace("```", "").strip()
                    
                    plt.close('all')
                    fig, ax = plt.subplots(figsize=(10, 6))
                    exec_globals = {"plt": plt, "fig": fig, "ax": ax, "patches": patches}
                    exec(codigo_nesting, exec_globals)
                    
                    st.markdown("### 📐 Diagrama de Disposição do Corte (Nesting)")
                    st.pyplot(plt.gcf(), use_container_width=True)
                    plt.close('all')

                    # Salva no Histórico do Sistema
                    st.session_state.historico_projetos.append({
                        "titulo": f"Plano de Corte ({tipo_material[:10]})",
                        "tipo": "Plano de Corte",
                        "resumo": f"Material: {tipo_material} | Pecas: {lista_pecas_input[:50]}...",
                        "conteudo": res_corte
                    })

                except Exception as e:
                    plt.close('all')
                    st.error(f"Erro no cálculo do plano de corte: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 5: VÍDEOS & NARRAÇÃO
# ------------------------------------------------------------------------------
with tabs[4]:
    st.subheader("🎬 Gerador de Conteúdo Multimídia (Roteiro + Narração)")
    topico_video = st.text_input("Tema do Vídeo:", placeholder="Ex: Apresentação comercial da nova invenção")
    idioma = st.selectbox("Idioma:", ["pt", "en", "es"])

    if st.button("🎬 Criar Roteiro e Gerar Narração em Áudio"):
        if not topico_video:
            st.warning("Digite o tema.")
        else:
            with st.spinner("Sintetizando locução em MP3..."):
                roteiro = call_gemini(f"Crie um roteiro de vídeo curto (1 min) para: '{topico_video}'. Divida em [CENA], [VISUAL] e [LOCUÇÃO].", gemini_key)
                st.markdown(roteiro)
                
                tts = gTTS(text=roteiro, lang=idioma, slow=False)
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                
                st.audio(fp, format="audio/mp3")
                st.download_button("🎵 Baixar Áudio MP3", data=fp, file_name="locucao.mp3", mime="audio/mp3")