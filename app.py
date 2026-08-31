import streamlit as st
import pandas as pd
from PIL import Image
import pypdf
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Plataforma de Engenharia & Invenções IA",
    page_icon="⚡",
    layout="wide"
)

# Barra lateral com chaves das APIs
with st.sidebar:
    st.header("🔑 Configurações de APIs")
    gemini_key = st.text_input("Chave Gemini API (Google):", type="password")
    groq_key = st.text_input("Chave Groq API (Opcional):", type="password")
    
    st.divider()
    st.info("Para obter chaves gratuitas:\n- Gemini: aistudio.google.com\n- Groq: console.groq.com")

# Funções auxiliares de leitura de arquivos
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
    "💡 Agente Inventor Multiagentes", 
    "📋 Gerador de Orçamentos Técnicos"
])

# ==============================================================================
# ABA 1: AGENTE INVENTOR MULTIAGENTES
# ==============================================================================
with tab_inventor:
    st.title("🧪 Laboratório de Invenções e Prototipagem (Multiagentes)")
    st.markdown("""
    Descreva qualquer ideia (mecânica, aeroespacial, química, eletrônica ou de bens de consumo).
    O sistema acionará uma equipe de **agentes especialistas em IA** para projetar o protótipo e especificar os materiais.
    """)

    col1, col2 = st.columns([2, 1])
    
    with col1:
        ideia_usuario = st.text_area(
            "Descreva a sua ideia de invenção em detalhes:",
            height=180,
            placeholder="Ex: Um purificador de ar portátil baseando-se em filtragem de microalgas com fotossíntese LED..."
        )
    
    with col2:
        area_projeto = st.selectbox(
            "Área principal do projeto:",
            ["Engenharia Mecânica / Robótica", "Engenharia Química / Cosméticos / Perfumes", 
             "Aeroespacial / Drones", "Eletrônica / IoT", "Biotecnologia / Materiais"]
        )
        nivel_detalhe = st.select_slider(
            "Nível de detalhamento do protótipo:",
            options=["Conceitual", "Funcional DIY (Hacker)", "Industrial / Produção"]
        )

    if st.button("🚀 Iniciar Ciclo de Invenção Multiagente", type="primary"):
        if not gemini_key:
            st.error("Por favor, insira a Chave de API do Gemini na barra lateral.")
        elif not ideia_usuario.strip():
            st.warning("Por favor, descreva a sua ideia antes de prosseguir.")
        else:
            client = genai.Client(api_key=gemini_key)
            
            # --- AGENTE 1: Pesquisa de Viabilidade ---
            with st.status("🕵️ Agente 1: Analisando viabilidade técnica e teórica...", expanded=True) as status1:
                prompt_agente1 = f"""
                Atue como um Físico/Químico Pesquisador Principal.
                Área: {area_projeto}. Ideia: "{ideia_usuario}".
                Analise os princípios científicos por trás dessa ideia. Liste os desafios técnicos e as melhores abordagens teóricas para fazê-la funcionar na prática.
                """
                res_agente1 = client.models.generate_content(
                    model="gemini-3.6-flash", contents=prompt_agente1
                ).text
                status1.update(label="✅ Agente 1: Viabilidade teórica concluída!", state="complete")

            # --- AGENTE 2: Design de Engenharia ---
            with st.status("🛠️ Agente 2: Criando arquitetura técnica e formulação...", expanded=True) as status2:
                prompt_agente2 = f"""
                Atue como Engenheiro de Projetos/Formulador Sênior.
                Com base na análise do Pesquisador:
                {res_agente1}

                Elabore a arquitetura completa do invento. Se for químico/perfume, dê a fórmula/composição detalhada em % e reagentes. Se for mecânico/eletrônico, dê o esquema estrutural, componentes e diagramas de blocos.
                """
                res_agente2 = client.models.generate_content(
                    model="gemini-3.6-flash", contents=prompt_agente2
                ).text
                status2.update(label="✅ Agente 2: Arquitetura e formulação concluídas!", state="complete")

            # --- AGENTE 3: Prototipagem e Materiais ---
            with st.status("📦 Agente 3: Mapeando lista de materiais e guia de montagem...", expanded=True) as status3:
                prompt_agente3 = f"""
                Atue como Especialista em Prototipagem Rápida e Maker. Nível: {nivel_detalhe}.
                Com base na arquitetura:
                {res_agente2}

                Crie o relatório final contendo:
                1. Lista de Materiais e Componentes (BOM) com especificações técnicas.
                2. Ferramentas necessárias para montagem/síntese.
                3. Guia Passo a Passo para montagem do primeiro protótipo funcional.
                4. Dicas de segurança e testes iniciais.
                """
                res_agente3 = client.models.generate_content(
                    model="gemini-3.6-flash", contents=prompt_agente3
                ).text
                status3.update(label="✅ Agente 3: Guia de prototipagem finalizado!", state="complete")

            # Apresentação do Dossiê Completo
            st.divider()
            st.header("📄 Dossiê Técnico da Invenção")
            
            exp1 = st.expander("🔬 Fase 1: Análise Científica e Viabilidade", expanded=False)
            exp1.markdown(res_agente1)

            exp2 = st.expander("⚙️ Fase 2: Arquitetura Técnica / Formulação Química", expanded=False)
            exp2.markdown(res_agente2)

            st.subheader("🛠️ Fase 3: Lista de Materiais e Manual do Protótipo")
            st.markdown(res_agente3)

            # Unificação dos dados para download
            dossie_completo = f"# DOSSIÊ DE INVENÇÃO: {ideia_usuario}\n\n## 1. Viabilidade Científica\n{res_agente1}\n\n## 2. Arquitetura/Formulação\n{res_agente2}\n\n## 3. Guia do Protótipo & Materiais\n{res_agente3}"
            
            st.download_button(
                label="📥 Baixar Dossiê Completo da Invenção (.md)",
                data=dossie_completo,
                file_name="Dossie_Invenção_Prototipo.md",
                mime="text/markdown"
            )

# ==============================================================================
# ABA 2: GERADOR DE ORÇAMENTOS TÉCNICOS (CÓDIGO ANTERIOR)
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
                            model="gemini-3.6-flash",
                            contents=[prompt_orcamento] + contents_payload
                        )
                        st.success("Orçamento Gerado!")
                        st.markdown(res.text)
                    except Exception as e:
                        st.error(f"Erro ao processar: {str(e)}")