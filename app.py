import streamlit as st
import pandas as pd
import requests
from PIL import Image
import pypdf
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Multi-Engine IA: Invenções & Engenharia",
    page_icon="⚡",
    layout="wide"
)

# ==============================================================================
# SIDEBAR COM CHAVES DE API (Busca nos Secrets do Streamlit Cloud)
# ==============================================================================
with st.sidebar:
    st.header("🔑 Configurações de APIs Gratuitas")
    
    # Tenta buscar a chave nos 'Secrets' do Streamlit; se não encontrar, usa texto vazio ""
    default_gemini = st.secrets.get("GEMINI_API_KEY", "")
    default_groq = st.secrets.get("GROQ_API_KEY", "")
    default_openrouter = st.secrets.get("OPENROUTER_API_KEY", "")

    # Campos de entrada preenchidos automaticamente com o padrão do Secrets
    gemini_key = st.text_input("1. Google Gemini API Key:", value=default_gemini, type="password")
    groq_key = st.text_input("2. Groq API Key:", value=default_groq, type="password")
    openrouter_key = st.text_input("3. OpenRouter API Key:", value=default_openrouter, type="password")
    
    st.divider()
    st.markdown("""
    **Links para obter chaves gratuitas:**
    - [Google AI Studio](https://aistudio.google.com/)
    - [Groq Cloud](https://console.groq.com/)
    - [OpenRouter](https://openrouter.ai/)
    """)

# ==============================================================================
# FUNÇÕES DE CHAMADA ÀS APIS NA NUVEM
# ==============================================================================
def call_gemini(prompt, api_key, model="gemini-3.6-flash"):
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
        raise Exception(f"Erro Groq ({res.status_code}): {res.text}")

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
        raise Exception(f"Erro OpenRouter ({res.status_code}): {res.text}")

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

# ==============================================================================
# NAVEGAÇÃO PRINCIPAL POR ABAS
# ==============================================================================
st.title("⚡ Multi-Engine IA: Invenções & Engenharia Online")

tabs = st.tabs(["🧪 Agentes Autônomos de Invenção", "📋 Gerador de Orçamentos Técnicos", "💬 Teste de Provedores"])

# ------------------------------------------------------------------------------
# ABA 1: AGENTES AUTÔNOMOS
# ------------------------------------------------------------------------------
with tabs[0]:
    st.subheader("Laboratório Multiagente de Invenções & Prototipagem")
    st.markdown("""
    Nesta seção, 3 Agentes de IA conversam em cadeia para transformar sua ideia em um dossiê técnico.
    """)

    col_prov, col_area = st.columns(2)
    with col_prov:
        provedor = st.selectbox(
            "Selecione o Provedor Cloud dos Agentes:",
            ["Google Gemini (Recomendado)", "Groq (Llama 3.3 70B)", "OpenRouter Free"]
        )
    with col_area:
        area_projeto = st.selectbox(
            "Área Principal do Projeto:",
            ["Engenharia Química / Cosméticos", "Engenharia Mecânica / Robótica", "Eletrônica / IoT", "Biotecnologia & Materiais"]
        )
        
    ideia = st.text_area("Descreva a ideia da sua invenção:", height=130, placeholder="Ex: Perfume sintético de fixação prolongada por microcápsulas...")

    if st.button("🚀 Iniciar Processamento dos Agentes", type="primary"):
        if not ideia.strip():
            st.warning("Por favor, descreva a sua ideia antes de prosseguir.")
        else:
            try:
                # Função roteadora para chamar a API selecionada
                def executar_agente(prompt_texto):
                    if "Gemini" in provedor:
                        if not gemini_key: raise Exception("Insira a chave do Gemini na sidebar ou nos Secrets.")
                        return call_gemini(prompt_texto, gemini_key)
                    elif "Groq" in provedor:
                        if not groq_key: raise Exception("Insira a chave do Groq na sidebar ou nos Secrets.")
                        return call_groq(prompt_texto, groq_key)
                    elif "OpenRouter" in provedor:
                        if not openrouter_key: raise Exception("Insira a chave do OpenRouter na sidebar ou nos Secrets.")
                        return call_openrouter_free(prompt_texto, openrouter_key)

                # Execução Sequencial (Comunicação entre Agentes)
                with st.status("🕵️ Agente 1 (Pesquisador): Verificando viabilidade científica...", expanded=True) as status1:
                    p1 = f"Atue como Pesquisador Científico Sênior na área de {area_projeto}. Analise a viabilidade física/química e gargalos de: {ideia}"
                    r1 = executar_agente(p1)
                    status1.update(label="✅ Agente 1: Viabilidade concluída!", state="complete")
                
                with st.status("⚙️ Agente 2 (Engenheiro): Criando especificação/formulação...", expanded=True) as status2:
                    p2 = f"Atue como Engenheiro de Projetos. Com base na análise científica:\n{r1}\n\nElabore a especificação técnica detalhada ou fórmula percentual completa."
                    r2 = executar_agente(p2)
                    status2.update(label="✅ Agente 2: Projeto técnico concluído!", state="complete")

                with st.status("🛠️ Agente 3 (Maker): Gerando Lista de Materiais e Protótipo...", expanded=True) as status3:
                    p3 = f"Atue como Especialista em Prototipagem. Com base no projeto técnico:\n{r2}\n\nCrie a Lista de Materiais (BOM) e o guia passo a passo de montagem."
                    r3 = executar_agente(p3)
                    status3.update(label="✅ Agente 3: Guia do protótipo finalizado!", state="complete")

                st.success("Dossiê Técnico Gerado com Sucesso!")
                
                with st.expander("🔬 Análise de Viabilidade (Pesquisador)", expanded=False):
                    st.markdown(r1)
                    
                with st.expander("⚙️ Projeto Técnico / Formulação (Engenheiro)", expanded=False):
                    st.markdown(r2)

                st.markdown("### 🛠️ Lista de Materiais e Guia de Montagem")
                st.markdown(r3)

                dossie = f"# DOSSIÊ DE INVENÇÃO\n\n## 1. Viabilidade\n{r1}\n\n## 2. Projeto Técnico\n{r2}\n\n## 3. Materiais & Protótipo\n{r3}"
                st.download_button("📄 Baixar Dossiê (.md)", data=dossie, file_name="Dossie_Invention.md", mime="text/markdown")

            except Exception as e:
                st.error(f"Erro na execução: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 2: GERADOR DE ORÇAMENTOS TÉCNICOS
# ------------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Gerador de Orçamentos Técnicos & Análise de Projetos")
    
    scale_info = st.text_area("Referência de medida para imagem/desenho (Ex: A porta tem 2.10m):", placeholder="Informe uma escala de referência...")
    uploaded_files = st.file_uploader("Carregue arquivos do projeto (PDF, Planilhas, Imagens):", type=["pdf", "xlsx", "xls", "csv", "png", "jpg", "jpeg"], accept_multiple_files=True)

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

        Gere um ORÇAMENTO TÉCNICO COMPLETO em Markdown contendo:
        1. Resumo Executivo
        2. Análise Dimensional Visual (Pixel Scaling)
        3. Tabela de Quantitativo de Materiais
        4. Plano de Aproveitamento e Otimização de Cortes
        5. Resumo Financeiro Final
        """

        if st.button("🚀 Gerar Orçamento Técnico", type="primary"):
            if not gemini_key:
                st.error("Por favor, insira a Chave de API do Gemini na barra lateral ou nos Secrets.")
            else:
                with st.spinner("Analisando documentos e gerando orçamento..."):
                    try:
                        client = genai.Client(api_key=gemini_key)
                        res = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[prompt_orcamento] + contents_payload
                        )
                        st.success("Orçamento Gerado!")
                        st.markdown(res.text)
                    except Exception as e:
                        st.error(f"Erro ao processar: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 3: TESTE DE PROVEDORES DE IA
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Testar Modelo de IA Individual")
    prompt_teste = st.text_input("Pergunta para o modelo de teste:")
    modelo_sel = st.selectbox("Escolha o modelo:", ["Gemini 2.5 Flash (Google)", "Llama 3.3 70B (Groq)", "DeepSeek R1 Free (OpenRouter)"])
    
    if st.button("Enviar Consulta"):
        if prompt_teste:
            try:
                if "Gemini" in modelo_sel:
                    res = call_gemini(prompt_teste, gemini_key)
                elif "Groq" in modelo_sel:
                    res = call_groq(prompt_teste, groq_key)
                elif "DeepSeek" in modelo_sel:
                    res = call_openrouter_free(prompt_teste, openrouter_key, "deepseek/deepseek-r1:free")
                
                st.markdown("**Resposta:**")
                st.write(res)
            except Exception as e:
                st.error(f"Erro: {str(e)}")