O erro **`FPDFException: Not enough horizontal space to render a single character`** ocorre na biblioteca `fpdf2` quando `pdf.multi_cell(0, ...)` tenta calcular a largura automática com o cursor posicionado próximo à margem direita ou ao processar linhas longas sem espaço. Além disso, a sintaxe legada `pdf.output(dest='S')` foi substituída pelo método nativo `bytes(pdf.output())`.

Abaixo está o código integral do arquivo `app.py` com a função `criar_pdf` corrigida (utilizando `pdf.epw` - *Effective Page Width*), tratamento seguro de quebras de texto e todas as 5 abas operacionais.

---

### Código Completo e Corrigido (`app.py`)

```python
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
# FUNÇÃO CORRIGIDA PARA GERAR PDF (FPDF2)
# ==============================================================================
def criar_pdf(titulo, conteudo_texto):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Define fonte e cabeçalho
    pdf.set_font("Helvetica", "B", 16)
    titulo_limpo = titulo.encode("latin-1", "replace").decode("latin-1")
    pdf.cell(pdf.epw, 10, text=titulo_limpo, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    # Conteúdo do relatório
    pdf.set_font("Helvetica", size=10)
    largura_util = pdf.epw  # Largura efetiva da página evitando estouro de margem
    
    for linha in conteudo_texto.split("\n"):
        texto_limpo = linha.encode("latin-1", "replace").decode("latin-1")
        if not texto_limpo.strip():
            pdf.ln(3)
        else:
            pdf.multi_cell(w=largura_util, h=5.5, text=texto_limpo, new_x="LMARGIN", new_y="NEXT")
            
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
# FUNÇÕES DE CHAMADA ÀS APIS
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
            st.warning(f"⚠️ O modelo principal ({model}) está com alta demanda. Utilizando reserva ({fallback_model})...")
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
                    if "Gemini" in provedor:
                        return call_gemini(p, gemini_key)
                    elif "Groq" in provedor:
                        return call_groq(p, groq_key)
                    else:
                        return call_openrouter_free(p, openrouter_key)

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
                - Defina o tamanho da figura como: fig, ax = plt.subplots(figsize=(10, 6))
                - Use fundo escuro estilo blueprint (facecolor='#0a192f') no fig e ax.
                - Use linhas e textos em branco ou azul claro ('#00d2ff').
                - Inclua dimensões e cotas indicativas no desenho.
                - NUNCA use plt.tight_layout().
                - Responda APENAS com código Python puro, sem explicações ou markdown.
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
                    st.error(f"Não foi possível desenhar a peça automaticamente: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 3: ORÇAMENTOS TÉCNICOS (INTEGRADA COM DESENHOS DE PEÇAS)
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("📋 Gerador de Orçamentos Técnicos & Análise Visual")
    
    scale_info = st.text_input("Referência de medida/escala (Ex: O vão principal tem 3.50m):", placeholder="Informe a referência se houver...")
    uploaded_files = st.file_uploader("Upload de PDFs/Planilhas/Imagens:", type=["pdf", "xlsx", "csv", "png", "jpg", "jpeg"], accept_multiple_files=True, key="orc_files")

    if uploaded_files:
        prompt_orcamento = (
            "Você é um Engenheiro Orçamentista.\n"
            "Examine os arquivos anexados e especificações do projeto.\n"
            + (f"ESCALA DE REFERÊNCIA: {scale_info}\n" if scale_info else "")
            + "\nGere um ORÇAMENTO TÉCNICO COMPLETO contendo:\n"
            "1. Resumo Executivo\n"
            "2. Tabela de Quantitativo de Materiais e Peças\n"
            "3. Resumo Financeiro Final\n\n"
            "IMPORTANTE: Ao final da resposta, inclua um bloco JSON estrito no seguinte formato listando as principais peças para desenho técnico:\n"
            "```json\n"
            "{\n"
            '  "pecas_para_desenho": [\n'
            '    {"nome": "Nome da Peça 1", "descricao": "Descrição técnica com dimensões"}\n'
            "  ]\n"
            "}\n"
            "```"
        )

        if st.button("🚀 Processar Orçamento Integrado", type="primary"):
            if not gemini_key:
                st.error("Insira a chave Gemini na barra lateral.")
            else:
                with st.spinner("Analisando documentos e estruturando orçamento..."):
                    try:
                        res_orc = call_gemini(prompt_orcamento, gemini_key)
                        
                        partes = res_orc.split("```json")
                        texto_orcamento = partes[0]
                        st.session_state["ultimo_orcamento_texto"] = texto_orcamento
                        
                        pecas_extraidas = []
                        if len(partes) > 1:
                            try:
                                json_str = partes[1].split("```")[0].strip()
                                json_data = json.loads(json_str)
                                pecas_extraidas = json_data.get("pecas_para_desenho", [])
                            except Exception:
                                pass
                        
                        st.session_state["pecas_orcamento"] = pecas_extraidas
                        
                        st.session_state.historico_projetos.append({
                            "titulo": f"Orçamento: {uploaded_files[0].name}",
                            "tipo": "Orçamento",
                            "resumo": texto_orcamento[:150],
                            "conteudo": texto_orcamento
                        })

                    except Exception as e:
                        st.error(f"Erro ao processar orçamento: {str(e)}")

    if "ultimo_orcamento_texto" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["ultimo_orcamento_texto"])
        
        pdf_orc = criar_pdf("ORCAMENTO TECNICO", st.session_state["ultimo_orcamento_texto"])
        st.download_button("📄 Baixar Orçamento em PDF", data=pdf_orc, file_name="Orcamento_Tecnico.pdf", mime="application/pdf")

        if st.session_state.get("pecas_orcamento"):
            st.divider()
            st.subheader("📐 Desenho Técnico das Peças do Orçamento")
            
            opcoes_pecas = [f"{p['nome']} - {p['descricao']}" for p in st.session_state["pecas_orcamento"]]
            peca_selecionada = st.selectbox("Escolha a peça para gerar o Blueprint:", opcoes_pecas)
            
            if st.button("🎨 Gerar Blueprint da Peça Selecionada"):
                with st.spinner(f"Gerando esquemático para: {peca_selecionada}..."):
                    prompt_draw = f"""
                    Atue como um gerador de gráficos Python (Matplotlib).
                    Crie APENAS um código Python funcional que use matplotlib.pyplot para desenhar um esquema técnico 2D cotado do componente: '{peca_selecionada}'.
                    
                    REGRAS OBRIGATÓRIAS:
                    - Defina o tamanho da figura como: fig, ax = plt.subplots(figsize=(10, 6))
                    - Use fundo escuro estilo blueprint (facecolor='#0a192f') no fig e ax.
                    - Use linhas e textos em branco ou azul claro ('#00d2ff').
                    - Inclua dimensões e cotas indicativas no desenho.
                    - NUNCA use plt.tight_layout().
                    - Responda APENAS com o código puro.
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
                        st.error(f"Erro ao desenhar a peça: {str(e)}")

# ------------------------------------------------------------------------------
# ABA 4: OTIMIZADOR DE PLANO DE CORTE (NESTING)
# ------------------------------------------------------------------------------
with tabs[3]:
    st.subheader("✂️ Otimizador de Plano de Corte & Nesting de Materiais")
    st.markdown("Calcule a quantidade exata de chapas/barras necessárias com diagrama visual.")

    col_mat, col_esp = st.columns(2)
    with col_mat:
        tipo_material = st.selectbox(
            "Tipo de Matéria-Prima:",
            ["MDF / Madeira (Chapa Padrão 2750 x 1850 mm)", 
             "Tubos / Cantoneiras / Perfis (Barra de 6000 mm)", 
             "Chapas Metálicas em Geral (Dimensão Personalizada)"]
        )

    if "MDF" in tipo_material:
        largura_bruta = 2750
        comprimento_bruto = 1850
        st.info(f"📏 Dimensão da Chapa Padrão de MDF: **{largura_bruta} x {comprimento_bruto} mm**")
    elif "Tubos" in tipo_material:
        largura_bruta = 6000
        comprimento_bruto = 0 
        st.info(f"📏 Comprimento Padrão da Barra: **{largura_bruta} mm (6 metros)**")
    else:
        with col_esp:
            largura_bruta = st.number_input("Largura da Chapa do Fornecedor (mm):", min_value=100, value=3000, step=50)
            comprimento_bruto = st.number_input("Comprimento da Chapa do Fornecedor (mm):", min_value=100, value=1500, step=50)
            st.caption(f"📏 Dimensão Personalizada da Chapa: **{largura_bruta} x {comprimento_bruto} mm**")

    st.divider()
    st.markdown("### 📋 Lista de Peças a Cortar")
    
    lista_pecas_input = st.text_area(
        "Formato (Peça, Largura_mm, Comprimento_mm, Quantidade):",
        height=120,
        placeholder="Exemplo para Chapas:\nLateral, 500, 1800, 2\nTampa, 600, 800, 1\nFundo, 500, 750, 2\n\nExemplo para Tubos:\nTubo_Base, 1200, 0, 4\nTubo_Coluna, 850, 0, 8"
    )

    espessura_disco = st.number_input("Espessura da serra/corte (Kerf em mm):", min_value=0.0, value=3.0, step=0.5)

    if st.button("✂️ Calcular Plano de Corte e Gerar Diagrama", type="primary"):
        if not lista_pecas_input.strip():
            st.warning("Preencha a lista de peças antes de prosseguir.")
        else:
            with st.spinner("Calculando aproveitamento e gerando plano de corte..."):
                prompt_corte = f"""
                Atue como Engenheiro de Processos especialista em Nesting de Corte.
                
                DADOS DA MATÉRIA-PRIMA:
                - Tipo: {tipo_material}
                - Largura Bruta: {largura_bruta} mm
                - Comprimento Bruto: {comprimento_bruto} mm (Se for 0, considerar perfil linear de {largura_bruta} mm)
                - Perda na Serra (Kerf): {espessura_disco} mm
                
                LISTA DE PEÇAS REQUISITADAS:
                {lista_pecas_input}
                
                Gere um relatório detalhado contendo:
                1. Quantidade total de Chapas/Barras inteiras necessárias.
                2. Percentual de Aproveitamento (%) e Retalho/Sobra.
                3. Instruções passo a passo da sequência dos cortes.
                """
                
                try:
                    res_corte = call_gemini(prompt_corte, gemini_key)
                    st.markdown("### 📊 Relatório de Otimização de Corte")
                    st.markdown(res_corte)
                    
                    prompt_draw_nesting = f"""
                    Crie APENAS um código Python (Matplotlib) funcional para desenhar a disposição gráfica das peças na chapa:
                    Matéria-Prima: {largura_bruta}x{comprimento_bruto}mm. Peças: {lista_pecas_input}.
                    
                    REGRAS OBRIGATÓRIAS:
                    - Desenhe os retângulos da chapa ({largura_bruta}x{comprimento_bruto}) com fundo cinza escuro.
                    - Desenhe as peças posicionadas com cores vivas e rótulos do nome e dimensão.
                    - Use fig, ax = plt.subplots(figsize=(10, 6))
                    - NUNCA use plt.tight_layout().
                    - Responda APENAS com código puro, sem markdown.
                    """
                    codigo_nesting = call_gemini(prompt_draw_nesting, gemini_key).replace("```python", "").replace("```", "").strip()
                    
                    plt.close('all')
                    fig, ax = plt.subplots(figsize=(10, 6))
                    exec_globals = {"plt": plt, "fig": fig, "ax": ax, "patches": patches}
                    exec(codigo_nesting, exec_globals)
                    
                    st.markdown("### 📐 Diagrama de Disposição do Corte (Nesting)")
                    st.pyplot(plt.gcf(), use_container_width=True)
                    plt.close('all')

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
                try:
                    roteiro = call_gemini(f"Crie um roteiro de vídeo curto (1 min) para: '{topico_video}'. Divida em [CENA], [VISUAL] e [LOCUÇÃO].", gemini_key)
                    st.markdown("### 📜 Roteiro Cinematográfico")
                    st.markdown(roteiro)
                    
                    tts = gTTS(text=roteiro, lang=idioma, slow=False)
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    
                    st.markdown("### 🎙️ Narração Gerada")
                    st.audio(fp, format="audio/mp3")
                    st.download_button("🎵 Baixar Áudio MP3", data=fp, file_name="locucao.mp3", mime="audio/mp3")
                except Exception as e:
                    st.error(f"Erro ao gerar multimídia: {str(e)}")

```