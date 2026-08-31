import streamlit as st
import pandas as pd
from PIL import Image
import pypdf
import os
from google import genai

# Importações do CrewAI e LangChain
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

# Configuração da página
st.set_page_config(
    page_title="Plataforma de Engenharia, Invenções & Orçamentos",
    page_icon="⚡",
    layout="wide"
)

# Sidebar com Provedores e Chaves
with st.sidebar:
    st.header("🔑 Configurações de LLMs / APIs")
    
    provedor_ia = st.selectbox(
        "Selecione o Provedor Principal para os Agentes:",
        ["Google Gemini (Gratuito)", "Groq - Llama 3.3 (Gratuito/OpenSource)", "Ollama (Local/Sem Chave)"]
    )
    
    gemini_key = st.text_input("Chave Gemini API:", type="password")
    groq_key = st.text_input("Chave Groq API:", type="password")
    
    st.divider()
    st.info("""
    **Onde obter chaves gratuitas:**
    - Gemini: https://aistudio.google.com/
    - Groq: https://console.groq.com/
    """)

# Função para inicializar o Modelo de Linguagem (LLM) escolhido
def get_llm(provedor, key_gemini, key_groq):
    if provedor == "Google Gemini (Gratuito)":
        if not key_gemini:
            st.error("Por favor, informe a Chave da API do Gemini.")
            return None
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=key_gemini,
            temperature=0.7
        )
    elif provedor == "Groq - Llama 3.3 (Gratuito/OpenSource)":
        if not key_groq:
            st.error("Por favor, informe a Chave da API da Groq.")
            return None
        return ChatGroq(
            temperature=0.7,
            groq_api_key=key_groq,
            model_name="llama-3.3-70b-versatile"
        )
    elif provedor == "Ollama (Local/Sem Chave)":
        # Conecta ao servidor local do Ollama
        from langchain_community.llms import Ollama
        return Ollama(model="llama3")

# Funções auxiliares de leitura
def read_pdf(file):
    reader = pypdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def read_excel_or_csv(file):
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file).to_string()
        return pd.read_excel(file).to_string()
    except Exception as e:
        return f"Erro ao ler planilha: {str(e)}"

# NAVEGAÇÃO POR ABAS
tab_inventor, tab_orcamento = st.tabs([
    "🤖 Agentes Autônomos (CrewAI)", 
    "📋 Gerador de Orçamentos Técnicos"
])

# ==============================================================================
# ABA 1: CREWAI AGENTES AUTÔNOMOS
# ==============================================================================
with tab_inventor:
    st.title("🧪 Laboratório Multiagente de Invenções (CrewAI)")
    st.markdown("""
    Nesta aba, **3 Agentes Autônomos especializados** trabalham em equipe. 
    Eles analisam, criticam e refinam a ideia uns dos outros em tempo real até gerar o protótipo ideal.
    """)

    col1, col2 = st.columns([2, 1])
    with col1:
        ideia_usuario = st.text_area(
            "Descreva a sua ideia de invenção:",
            height=150,
            placeholder="Exemplo: Um perfume biomimético com feromônios sintéticos e óleos essenciais com fixação prolongada por microcápsulas..."
        )
    with col2:
        area_projeto = st.selectbox(
            "Área do Projeto:",
            ["Engenharia Química / Cosméticos", "Engenharia Mecânica / Robótica", 
             "Aeroespacial / Drones", "Eletrônica / IoT", "Biotecnologia"]
        )

    if st.button("🚀 Iniciar Colaboração Autônoma dos Agentes", type="primary"):
        llm_selecionado = get_llm(provedor_ia, gemini_key, groq_key)
        
        if llm_selecionado and ideia_usuario.strip():
            with st.spinner("Agentes reunidos! Iniciando o fluxo autônomo de trabalho..."):
                try:
                    # 1. Definição dos Agentes Autônomos
                    pesquisador = Agent(
                        role="Pesquisador Científico Sênior",
                        goal=f"Analisar a viabilidade física, química e teórica da ideia: '{ideia_usuario}' na área de {area_projeto}.",
                        backstory="Você é um cientista renomado com doutorado em física e química aplicada. Seu papel é validar leis científicas e identificar conceitos fundamentais.",
                        verbose=True,
                        llm=llm_selecionado
                    )

                    engenheiro = Agent(
                        role="Engenheiro de Projetos e Arquitetura",
                        goal="Desenvolver a estrutura técnica detalhada, esquemáticos e formulação com base nas descobertas do Pesquisador.",
                        backstory="Você é um engenheiro sênior focado em transformar teorias científicas em projetos reais. Você cria fórmulas químicas exatas ou desenhos estruturais.",
                        verbose=True,
                        llm=llm_selecionado
                    )

                    prototipador = Agent(
                        role="Mestre Maker e Especialista em Prototipagem",
                        goal="Criar a lista completa de materiais (BOM) e o guia passo a passo para construir o primeiro protótipo funcional.",
                        backstory="Você é um especialista em laboratórios de prototipagem rápida e fabricação digital. Você sabe exatamente como comprar materiais baratos e montar o protótipo.",
                        verbose=True,
                        llm=llm_selecionado
                    )

                    # 2. Definição das Tarefas Encadeadas
                    t1 = Task(
                        description=f"Analise a viabilidade teórica de: {ideia_usuario}. Liste os princípios fundamentais e possíveis gargalos técnicos.",
                        expected_output="Relatório de viabilidade teórica e científica.",
                        agent=pesquisador
                    )

                    t2 = Task(
                        description="Com base na análise teórica, crie a especificação técnica detalhada, incluindo dosagens/formulações em % ou arquitetura mecânica/eletrônica.",
                        expected_output="Especificação técnica e arquitetura de projeto detalhada.",
                        agent=engenheiro
                    )

                    t3 = Task(
                        description="Com base no projeto técnico, elabore a Lista de Materiais (BOM) com especificações e o Manual Passo a Passo de montagem/síntese do protótipo.",
                        expected_output="Lista de materiais e guia prático de montagem em Markdown.",
                        agent=prototipador
                    )

                    # 3. Criação do Crew (Equipe) e Execução
                    equipe = Crew(
                        agents=[pesquisador, engenheiro, prototipador],
                        tasks=[t1, t2, t3],
                        process=Process.sequential,
                        verbose=True
                    )

                    resultado = equipe.kickoff()

                    st.success("✅ Processo Autônomo Concluído com Sucesso!")
                    st.markdown("### 📜 Dossiê Final da Invenção")
                    st.markdown(resultado.raw)

                    st.download_button(
                        label="📄 Baixar Dossiê Autônomo (.md)",
                        data=resultado.raw,
                        file_name="Dossie_CrewAI_Invecao.md",
                        mime="text/markdown"
                    )

                except Exception as e:
                    st.error(f"Erro durante a execução do CrewAI: {str(e)}")

# ==============================================================================
# ABA 2: GERADOR DE ORÇAMENTOS TÉCNICOS
# ==============================================================================
with tab_orcamento:
    st.title("📋 Gerador de Orçamentos Técnicos & Análise de Projetos")
    st.markdown("Análise de **PDFs, planilhas e imagens 3D** com cálculo de corte e proporção de pixels.")

    scale_info = st.text_area(
        "Referência de medida para imagem/desenho (Ex: A porta tem 2.10m):",
        placeholder="Informe uma escala de referência..."
    )

    uploaded_files = st.file_uploader(
        "Carregue os arquivos do projeto:",
        type=["pdf", "xlsx", "xls", "csv", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.subheader("📎 Arquivos Carregados")
        cols = st.columns(min(len(uploaded_files), 4))
        contents_payload = []
        
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 4]:
                st.caption(f"**{file.name}**")
                if file.type.startswith("image"):
                    img = Image.open(file)
                    st.image(img, use_container_width=True)
                    contents_payload.append(img)
                elif file.type == "application/pdf":
                    pdf_text = read_pdf(file)
                    contents_payload.append(f"--- PDF '{file.name}' ---\n{pdf_text}")
                elif file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel", "text/csv"]:
                    sheet_text = read_excel_or_csv(file)
                    contents_payload.append(f"--- PLANILHA '{file.name}' ---\n{sheet_text}")

        prompt_orcamento = f"""
        Você é um Engenheiro Orçamentista e Especialista em Análise Dimensional.
        Análise todos os arquivos anexados.
        {f"ESCALA: {scale_info}" if scale_info else "Faça estimativas baseadas em proporção visual."}

        Gere um ORÇAMENTO TÉCNICO COMPLETO em Markdown com:
        1. Resumo Executivo
        2. Análise Dimensional Visual (Pixel Scaling)
        3. Tabela de Quantitativo de Materiais
        4. Plano de Aproveitamento e Otimização de Cortes
        5. Resumo Financeiro Final
        """

        if st.button("🚀 Gerar Orçamento Técnico", type="primary"):
            if not gemini_key:
                st.error("Por favor, insira a Chave de API do Gemini na barra lateral.")
            else:
                client = genai.Client(api_key=gemini_key)
                with st.spinner("Analisando documentos e gerando orçamento..."):
                    try:
                        res = client.models.generate_content(
                            model="gemini-1.5-flash",
                            contents=[prompt_orcamento] + contents_payload
                        )
                        st.success("Orçamento Gerado!")
                        st.markdown(res.text)
                    except Exception as e:
                        st.error(f"Erro ao processar: {str(e)}")