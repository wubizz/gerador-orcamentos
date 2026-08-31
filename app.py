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
import tempfile
import os

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
# FUNÇÕES UTILITÁRIAS E DE PARSE BLINDADAS
# ==============================================================================
def limpar_codigo_python(texto_bruto):
    texto = texto_bruto.replace("```python", "").replace("```", "")
    return texto.strip()

def extrair_json_seguro(texto_bruto):
    padrao = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(padrao, texto_bruto, re.DOTALL)
    if match:
        return match.group(1).strip()
    return texto_bruto.strip()

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

def gerar_imagem_peca_temp(nome_peca):
    """Gera um gráfico Matplotlib de uma peça e salva em arquivo temporário para inserir no PDF."""
    try:
        plt.close('all')
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.set_facecolor('#0a192f')
        fig.patch.set_facecolor('#0a192f')
        
        # Desenho esquemático genérico baseado no nome
        rect = patches.Rectangle((0.1, 0.2), 0.8, 0.6, linewidth=2, edgecolor='#00d2ff', facecolor='#172a45')
        ax.add_patch(rect)
        ax.text(0.5, 0.5, f"PEÇA: {nome_peca[:25]}", color='white', fontsize=10, ha='center', va='center', weight='bold')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(tmp_file.name, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close('all')
        return tmp_file.name
    except Exception:
        plt.close('all')
        return None

# ==============================================================================
# FUNÇÃO BLINDADA PARA GERAR PDF (Com suporte a Inclusão de Imagens/Desenhos)
# ==============================================================================
def criar_pdf_com_desenhos(titulo, conteudo_texto, lista_pecas_desenho=None):
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
                
    # Se houver peças para desenhar, adiciona uma página com os esquemáticos
    if lista_pecas_desenho:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(pdf.epw, 10, text="ESQUEMÁTICO TÉCNICO DAS PEÇAS", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)
        
        for p in lista_pecas_desenho:
            nome = p.get('nome', 'Peça')
            img_path = gerar_imagem_peca_temp(nome)
            if img_path and os.path.exists(img_path):
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(pdf.epw, 6, text=f"Componente: {nome}", new_x="LMARGIN", new_y="NEXT")
                try:
                    pdf.image(img_path, w=100)
                    pdf.ln(5)
                except Exception:
                    pass
                finally:
                    try:
                        os.unlink(img_path)
                    except:
                        pass

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
                pdf_data = criar_pdf_com_desenhos(item['titulo'], item['conteudo'], item.get('pecas'))
                st.download_button(
                    "📄 Baixar PDF com Desenhos",
                    data=pdf_data,
                    file_name=f"{item['titulo'][:15].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"btn_pdf_{idx}"
                )
    else:
        st.info("Nenhum projeto salvo na sessão.")

# ==============================================================================
# FUNÇÕES DE CHAMADA ÀS APIS
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
# ABA 1: AGENTES DE INVENÇÃO (Com Inclusão de Peças e Desenhos no PDF)
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
                with st.status("🛠️ Agente 3 (Maker): Gerando Lista de Materiais e Peças...", expanded=True):
                    prompt_maker = f"""
                    Com base no projeto:\n{r2}\n
                    Crie a Lista de Materiais completa contendo componentes estruturais E ferragens/parafusos necessários.
                    Retorne obrigatoriamente um JSON puro no formato:
                    ```json
                    {{
                      "lista_materiais": [
                        {{"ITEM": "1", "DESCRIÇÃO": "Nome da Peça ou Ferragem", "COMP. (mm)": "100", "LARG. (mm)": "50", "QTD.": "4", "MATERIAL": "Aço/MDF/Plástico"}}
                      ],
                      "pecas_para_desenho": [
                        {{"nome": "Nome da Peça", "descricao": "Descrição geométrica"}}
                      ]
                    }}
                    ```
                    """
                    r3_bruto = exec_agente(prompt_maker)
                    json_str_inv = extrair_json_seguro(r3_bruto)
                    dados_inv = json.loads(json_str_inv)

                st.success("Dossiê e Peças Gerados com Sucesso!")
                dossie_completo = f"DOSSIÊ TÉCNICO: {ideia[:30]}\n\n--- 1. VIABILIDADE ---\n{r1}\n\n--- 2. PROJETO ---\n{r2}\n\n--- 3. MATERIAIS & FERRAGENS ---\n{json.dumps(dados_inv.get('lista_materiais', []), indent=2, ensure_ascii=False)}"
                
                st.session_state.historico_projetos.append({
                    "titulo": f"Invenção: {ideia[:20]}...",
                    "tipo": "Invenção",
                    "resumo": r1[:150],
                    "conteudo": dossie_completo,
                    "pecas": dados_inv.get('pecas_para_desenho', [])
                })

                st.markdown(dossie_completo)
                pdf_bytes = criar_pdf_com_desenhos("DOSSIE DE INVENCAO", dossie_completo, dados_inv.get('pecas_para_desenho', []))
                st.download_button("📄 Baixar Dossiê Completo + Desenhos em PDF", data=pdf_bytes, file_name="Dossie_Invention_Com_Desenhos.pdf", mime="application/pdf")
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
                    codigo_bruto = call_gemini(prompt_draw, gemini_key)
                    codigo_python = limpar_codigo_python(codigo_bruto)
                    
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
# ABA 3: ORÇAMENTOS TÉCNICOS & EXTRAÇÃO DE INSUMOS E FERRAGENS
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("📋 Leitor de Projetos, Imagens e Extração de Materiais/Ferragens")
    st.markdown("Faça upload de **Imagens (Plantas)**, **PDFs técnicos** ou **Planilhas** para converter na Lista Completa de Insumos (Peças + Ferragens).")
    
    scale_info = st.text_input("Referência de escala (Opcional):", placeholder="Ex: O vão principal tem 3.50m...")
    uploaded_files = st.file_uploader("Upload de Arquivos:", type=["pdf", "xlsx", "csv", "png", "jpg", "jpeg"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("🚀 Analisar Documentos e Gerar Orçamento Completo", type="primary"):
            if not gemini_key:
                st.error("Insira a chave Gemini na barra lateral.")
            else:
                with st.spinner("Analisando documentos, peças e ferragens..."):
                    try:
                        contents_payload = []
                        texto_extraido = ""
                        
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
                        Você é um Engenheiro de Processos e Orçamentista. Analise os documentos e imagens fornecidos.
                        {f"Escala de Referência Visual: {scale_info}" if scale_info else ""}
                        
                        Extraia e deduza TODAS as informações dos componentes, incluindo chapas/estruturas E TODAS AS FERRAGENS NECESSÁRIAS (parafusos, cavilhas, minifix, dobradiças, suportes, etc.).
                        Gere OBRIGATORIAMENTE APENAS UM BLOCO JSON com a seguinte estrutura exata:
                        
                        ```json
                        {{
                          "relatorio_texto": "Resumo executivo do projeto, recomendações técnicas e análise de insumos.",
                          "lista_materiais": [
                            {{"ITEM": "1", "DESCRIÇÃO": "BASE-FRONTAL", "COMP. (mm)": "1100", "LARG. (mm)": "90", "QTD.": "2", "MATERIAL": "MDF GRAFITE MATT 15MM"}},
                            {{"ITEM": "2", "DESCRIÇÃO": "PARAFUSO Minifix", "COMP. (mm)": "-", "LARG. (mm)": "-", "QTD.": "10", "MATERIAL": "AÇO ZINCADO"}}
                          ],
                          "pecas_para_desenho": [
                            {{"nome": "BASE-FRONTAL", "descricao": "Peça estrutural 1100x90mm"}}
                          ]
                        }}