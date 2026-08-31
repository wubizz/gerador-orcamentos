import streamlit as st
import pandas as pd
from PIL import Image
import pypdf
from google import genai

# Configuração da página no Streamlit
st.set_page_config(
    page_title="Plataforma de Engenharia, Invenções & Orçamentos",
    page_icon="⚡",
    layout="wide"
)

# Barra lateral para configuração da chave API e Parâmetros
with st.sidebar:
    st.header("🔑 Configurações")
    gemini_key = st.text_input("Chave de API do Google Gemini:", type="password")
    
    st.divider()
    st.info("Obtenha sua chave de API gratuitamente em: https://aistudio.google.com/")

# Funções auxiliares para leitura de arquivos
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
    "🤖 Agentes Autônomos de Invenção", 
    "📋 Gerador de Orçamentos Técnicos"
])

# ==============================================================================
# ABA 1: AGENTES AUTÔNOMOS PARA INVENÇÃO (NATIVO GEMINI)
# ==============================================================================
with tab_inventor:
    st.title("🧪 Laboratório Multiagente de Invenções & Prototipagem")
    st.markdown("""
    Nesta seção, uma equipe de **3 Agentes Especialistas de IA** atuam em sequência autônoma para transformar
    qualquer ideia em um **dossiê técnico completo**, incluindo fórmula/esquemático e guia de prototipagem.
    """)

    col1, col2 = st.columns([2, 1])
    with col1:
        ideia_usuario = st.text_area(
            "Descreva a sua ideia de invenção:",
            height=150,
            placeholder="Ex: Um perfume biomimético com fixação estendida por microcápsulas de alginato..."
        )
    with col2:
        area_projeto = st.selectbox(
            "Área do Projeto:",
            ["Engenharia Química / Cosméticos", "Engenharia Mecânica / Robótica", 
             "Aeroespacial / Drones", "Eletrônica / IoT", "Biotecnologia & Materiais"]
        )

    if st.button("🚀 Iniciar Colaboração Autônoma dos Agentes", type="primary"):
        if not gemini_key:
            st.error("Por favor, insira sua Chave de API do Gemini na barra lateral.")
        elif not ideia_usuario.strip():
            st.warning("Por favor, descreva a ideia antes de prosseguir.")
        else:
            client = genai.Client(api_key=gemini_key)
            
            # --- AGENTE 1: Pesquisador Científico ---
            with st.status("🕵️ Agente 1 (Pesquisador): Validando viabilidade teórica e física...", expanded=True) as status1:
                prompt_a1 = f"""
                Atue como Pesquisador Científico Sênior.
                Área: {area_projeto}.
                Ideia do Usuário: "{ideia_usuario}".
                
                Sua tarefa:
                1. Analise a viabilidade científica, física e química desta ideia.
                2. Liste os princípios teóricos que fundamentam a ideia.
                3. Identifique potenciais gargalos ou riscos técnicos.
                """
                res_agente1 = client.models.generate_content(
                    model="gemini-3.6-flash", contents=prompt_a1
                ).text
                status1.update(label="✅ Agente 1: Análise de viabilidade concluída!", state="complete")

            # --- AGENTE 2: Engenheiro de Projetos ---
            with st.status("⚙️ Agente 2 (Engenheiro): Projetando arquitetura/formulação...", expanded=True) as status2:
                prompt_a2 = f"""
                Atue como Engenheiro de Projetos e Arquitetura Sênior.
                Com base no parecer científico do Pesquisador:
                {res_agente1}

                Sua tarefa:
                1. Elabore a especificação técnica detalhada do invento.
                2. Se for químico/perfumaria/cosmético: Dê a dosagem/fórmula completa em porcentagens (%), reagentes e fixadores.
                3. Se for mecânico/eletrônico: Dê o diagrama de blocos, componentes e esquemático de ligação.
                """
                res_agente2 = client.models.generate_content(
                    model="gemini-3.6-flash", contents=prompt_a2
                ).text
                status2.update(label="✅ Agente 2: Especificação técnica gerada!", state="complete")

            # --- AGENTE 3: Especialista em Prototipagem ---
            with st.status("🛠️ Agente 3 (Mestre Maker): Criando BOM e Guia de Montagem...", expanded=True) as status3:
                prompt_a3 = f"""
                Atue como Mestre em Prototipagem Rápida e Maker.
                Com base no projeto técnico do Engenheiro:
                {res_agente2}

                Sua tarefa:
                1. Crie a Lista de Materiais (BOM) completa com especificações e sugestão de fornecedores/fontes.
                2. Liste as ferramentas necessárias para a montagem ou síntese.
                3. Forneça o Guia Passo a Passo para construir e testar o primeiro protótipo funcional.
                """
                res_agente3 = client.models.generate_content(
                    model="gemini-3.6-flash", contents=prompt_a3
                ).text
                status3.update(label="✅ Agente 3: Guia de prototipagem e materiais finalizado!", state="complete")

            # Apresentação Final do Dossiê
            st.divider()
            st.subheader("📜 Dossiê Técnico Final da Invenção")
            
            with st.expander("🔬 Análise de Viabilidade (Pesquisador Científico)", expanded=False):
                st.markdown(res_agente1)
                
            with st.expander("⚙️ Arquitetura Técnica / Formulação (Engenheiro de Projetos)", expanded=False):
                st.markdown(res_agente2)

            st.markdown("### 🛠️ Lista de Materiais e Guia do Protótipo")
            st.markdown(res_agente3)

            dossie = f"# DOSSIÊ DE INVENÇÃO\n\n## 1. Viabilidade\n{res_agente1}\n\n## 2. Projeto Técnico\n{res_agente2}\n\n## 3. Guia do Protótipo & Materiais\n{res_agente3}"
            
            st.download_button(
                label="📄 Baixar Dossiê Completo (.md)",
                data=dossie,
                file_name="Dossie_Invention.md",
                mime="text/markdown"
            )

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
                            model="gemini-3.6-flash",
                            contents=[prompt_orcamento] + contents_payload
                        )
                        st.success("Orçamento Gerado!")
                        st.markdown(res.text)
                    except Exception as e:
                        st.error(f"Erro ao processar: {str(e)}")