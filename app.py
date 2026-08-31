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
import textwrap
import re

# Configuração da página
st.set_page_config(
    page_title="Multi-Engine IA: Engenharia, Projetos & Orçamentos",
    page_icon="⚡",
    layout="wide"
)

# ==============================================================================
# INICIALIZAÇÃO DO HISTÓRICO DE SESSÃO
# ==============================================================================
if "historico_projetos" not in st.session_state:
    st.session_state.historico_projetos = []

# ==============================================================================
# FUNÇÕES DE LEITURA DE ARQUIVOS
# ==============================================================================
def read_pdf(file):
    try:
        reader = pypdf.PdfReader(file)
        text = ""
        for page in reader.pages:
            extraido = page.extract_text()
            if extraido:
                text += extraido + "\n"
        return text
    except Exception as e:
        return f"Erro ao ler PDF: {str(e)}"

def read_excel_or_csv(file):
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file).to_string()
        return pd.read_excel(file).to_string()
    except Exception as e:
        return f"Erro ao ler planilha: {str(e)}"

# ==============================================================================
# FUNÇÃO BLINDADA PARA GERAR PDF (Evita Erro de Largura / FPDFException)
# ==============================================================================
def criar_pdf(titulo, conteudo_texto):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 14)
    titulo_limpo = titulo.encode("latin-1", "replace").decode("latin-1")
    pdf.cell(pdf.epw, 10, text=titulo_limpo, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", size=10)
    largura_util = pdf.epw
    
    for linha in conteudo_texto.split("\n"):
        texto_limpo = linha.encode("latin-1", "replace").decode("latin-1")
        
        # Quebra linhas longas sem espaço para evitar travamento da margem do PDF
        if len(texto_limpo) > 90 and " " not in texto_limpo:
            partes = textwrap.wrap(texto_limpo, 90)
            for p in partes:
                pdf.multi_cell(w=largura_util, h=5.5, text=p, new_x="LMARGIN", new_y="NEXT")
        else:
            try:
                if not texto_limpo.strip():
                    pdf.ln(3)
                else:
                    pdf.multi_cell(w=largura_util, h=5.5, text=texto_limpo, new_x="LMARGIN", new_y="NEXT")
            except Exception:
                pdf.multi_cell(w=largura_util, h=5.5, text="[Linha com formatação inválida omitida]", new_x="LMARGIN", new_y="NEXT")
                
    return bytes(pdf.output())

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
                    file_name=f"{item['titulo'][:15].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"btn_pdf_{idx}"
                )
    else:
        st.info("Nenhum projeto salvo na sessão.")

# ==============================================================================
# FUNÇÕES DE CHAMADA ÀS APIS (COM SUPORTE A IMAGENS NO GEMINI)
# ==============================================================================
def call_gemini(contents_payload, api_key, model="gemini-3.6-flash"):
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(model=model, contents=contents_payload)
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "high demand" in error_msg.lower() or "404" in error_msg:
            fallback_model = "gemini-1.5-flash"
            st.warning(f"⚠️ O modelo {model} está indisponível/sobrecarregado. Usando reserva ({fallback_model})...")
            try:
                response_fallback = client.models.generate_content(model=fallback_model, contents=contents_payload)
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
    "📋 Orçamentos e Extração", 
    "✂️ Otimizador de Corte",
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

                st.success("Dossiê Gerado com Sucesso!")
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
                - Defina: fig, ax = plt.subplots(figsize=(10, 6))
                - Use fundo estilo blueprint (facecolor='#0a192f') no fig e ax.
                - Use linhas e textos em branco ou azul claro ('#00d2ff').
                - NUNCA use plt.tight_layout().
                - Responda APENAS com código Python puro.
                """
                try:
                    codigo_python = call_gemini(prompt_draw, gemini_key).replace("```python", "").replace("```", "").strip()
                    plt.close('all')
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    exec_globals = {"plt": plt, "fig": fig, "ax": ax, "patches": patches}
                    exec(codigo_python, exec_globals)
                    
                    st.pyplot(plt.gcf(), use_container_width=True)
                    plt.close('all')
                    st.success("Desenho Técnico Gerado com Sucesso!")
                except Exception as e:
                    plt.close('all')
                    st.error(f"Erro ao desenhar: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 3: ORÇAMENTOS TÉCNICOS & EXTRAÇÃO ESTRUTURADA (IMAGENS E PDFS)
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("📋 Leitor de Projetos, Imagens e Extração de Planilhas")
    st.markdown("Faça upload de **Imagens (Plantas)**, **PDFs técnicos** ou **Planilhas** para converter em Lista de Materiais e Desenhos de Peças.")
    
    scale_info = st.text_input("Referência de escala (Opcional):", placeholder="Ex: O vão principal tem 3.50m...")
    uploaded_files = st.file_uploader("Upload de Arquivos:", type=["pdf", "xlsx", "csv", "png", "jpg", "jpeg"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("🚀 Analisar Documentos e Gerar Planilha", type="primary"):
            if not gemini_key:
                st.error("Insira a chave Gemini na barra lateral.")
            else:
                with st.spinner("Analisando imagens/textos e estruturando dados..."):
                    try:
                        contents_payload = []
                        texto_extraido = ""
                        
                        # Processando imagens e extraindo texto dos PDFs
                        for f in uploaded_files:
                            if f.type.startswith("image"):
                                img = Image.open(f)
                                st.image(img, width=250, caption=f.name)
                                contents_payload.append(img)
                            elif f.type == "application/pdf":
                                texto = read_pdf(f)
                                texto_extraido += f"\n--- Conteúdo do PDF ({f.name}) ---\n{texto}"
                            elif f.name.endswith((".xlsx", ".xls", ".csv")):
                                texto = read_excel_or_csv(f)
                                texto_extraido += f"\n--- Conteúdo da Planilha ({f.name}) ---\n{texto}"

                        if texto_extraido:
                            contents_payload.append(texto_extraido)

                        prompt_orcamento = f"""
                        Você é um Engenheiro de Processos. Analise os documentos e imagens fornecidos.
                        {f"Escala de Referência Visual: {scale_info}" if scale_info else ""}
                        
                        Extraia e deduza as informações das peças e gere OBRIGATORIAMENTE APENAS UM BLOCO JSON.
                        O JSON deve ter EXATAMENTE esta estrutura de chaves para que eu possa gerar o Excel:
                        
                        ```json
                        {{
                          "relatorio_texto": "Resumo executivo do projeto, recomendações técnicas e análise visual.",
                          "lista_materiais": [
                            {{"ITEM": "1", "DESCRIÇÃO": "Nome da Peça", "COMP. (mm)": "1000", "LARG. (mm)": "500", "QTD.": "2", "MATERIAL": "MDF/Metal etc."}}
                          ],
                          "pecas_para_desenho": [
                            {{"nome": "Nome da Peça", "descricao": "Descrição geométrica com cotas em mm"}}
                          ]
                        }}
                        ```
                        Sem formatações externas ou introduções verbais. Apenas o código JSON puro.
                        """
                        
                        contents_payload.insert(0, prompt_orcamento)
                        res_orc = call_gemini(contents_payload, gemini_key)
                        
                        # Extração segura do JSON
                        match = re.search(r'```(?:json)?\n?(.*?)\n?```', res_orc, re.DOTALL)
                        json_str = match.group(1).strip() if match else res_orc.strip()
                        dados_estruturados = json.loads(json_str)
                        
                        st.session_state["relatorio_texto"] = dados_estruturados.get("relatorio_texto", "Relatório Indisponível.")
                        st.session_state["lista_materiais"] = dados_estruturados.get("lista_materiais", [])
                        st.session_state["pecas_orcamento"] = dados_estruturados.get("pecas_para_desenho", [])
                        
                        # Salva histórico
                        st.session_state.historico_projetos.append({
                            "titulo": f"Análise: {uploaded_files[0].name}",
                            "tipo": "Orçamento/Extração",
                            "resumo": st.session_state["relatorio_texto"][:150],
                            "conteudo": st.session_state["relatorio_texto"]
                        })

                        st.success("Dados extraídos e estruturados com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao estruturar os dados. A IA pode não ter encontrado o formato correto. Detalhe: {str(e)}")

    # ========================== EXIBIÇÃO DA EXTRAÇÃO E GERADOR DE DESENHO ==========================
    if "lista_materiais" in st.session_state and st.session_state["lista_materiais"]:
        st.markdown("---")
        st.markdown("### 📊 Relatório Técnico do Projeto")
        st.write(st.session_state["relatorio_texto"])
        
        st.markdown("### 📋 Tabela de Materiais Extraída")
        df_materiais = pd.DataFrame(st.session_state["lista_materiais"])
        st.dataframe(df_materiais, use_container_width=True)
        
        # Gerar Excel em memória
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='xlsxwriter') as writer:
            df_materiais.to_excel(writer, index=False, sheet_name='Lista_Materiais')
        buffer_excel.seek(0)
        
        col_excel, col_pdf = st.columns(2)
        with col_excel:
            st.download_button(
                label="📥 Baixar Planilha (.xlsx)",
                data=buffer_excel,
                file_name="Lista_Materiais.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        with col_pdf:
            pdf_bytes = criar_pdf("RELATÓRIO TÉCNICO", st.session_state["relatorio_texto"])
            st.download_button(
                label="📄 Baixar Resumo em PDF", 
                data=pdf_bytes, 
                file_name="Resumo_Projeto.pdf", 
                mime="application/pdf"
            )

        # Seção de geração do desenho das peças que vieram da tabela/projeto
        if st.session_state.get("pecas_orcamento"):
            st.divider()
            st.subheader("📐 Modelagem 2D Automática das Peças da Tabela")
            st.markdown("Gere um *Blueprint* para os componentes encontrados na análise acima:")
            
            opcoes_desenho = [f"{p.get('nome', '')} - {p.get('descricao', '')}" for p in st.session_state["pecas_orcamento"]]
            peca_selecionada = st.selectbox("Escolha o componente extraído:", opcoes_desenho)
            
            if st.button("🎨 Desenhar Componente Selecionado"):
                with st.spinner(f"Gerando esquemático para: {peca_selecionada}..."):
                    prompt_draw = f"""
                    Atue APENAS como um gerador de código Python (Matplotlib).
                    Crie o código para desenhar um esquema técnico 2D cotado da peça: '{peca_selecionada}'.
                    
                    REGRAS OBRIGATÓRIAS:
                    - Defina o tamanho da figura como: fig, ax = plt.subplots(figsize=(10, 6))
                    - Use fundo escuro estilo blueprint (facecolor='#0a192f') no fig e ax.
                    - Use linhas e textos em branco ou azul claro ('#00d2ff').
                    - NUNCA use plt.tight_layout().
                    - Responda APENAS com o código puro. Nenhuma palavra a mais.
                    """
                    try:
                        codigo_python = call_gemini(prompt_draw, gemini_key).replace("```python", "").replace("