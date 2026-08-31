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

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
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
# FUNÇÕES UTILITÁRIAS
# ==============================================================================
def limpar_codigo_python(texto_bruto):
    """Remove cercas Markdown de um código Python retornado pela IA."""
    if not texto_bruto:
        return ""
    texto = str(texto_bruto)
    texto = re.sub(r"^```python\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"^```\s*", "", texto)
    texto = re.sub(r"\s*```$", "", texto)
    return texto.strip()


def extrair_json_seguro(texto_bruto):
    """
    Extrai JSON mesmo quando a IA devolve ```json ... ```.
    Também tenta localizar o primeiro objeto JSON balanceado.
    """
    if not texto_bruto:
        raise ValueError("A IA retornou uma resposta vazia.")

    texto = str(texto_bruto).strip()

    # Primeiro tenta bloco Markdown.
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", texto, re.IGNORECASE | re.DOTALL)
    if match:
        texto = match.group(1).strip()

    # Remove eventuais prefixos/sufixos fora do JSON.
    inicio = texto.find("{")
    fim = texto.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        texto = texto[inicio:fim + 1]

    return texto.strip()


def ler_pdf(file):
    """Lê texto de um PDF."""
    try:
        reader = pypdf.PdfReader(file)
        partes = []

        for page in reader.pages:
            extraido = page.extract_text()
            if extraido:
                partes.append(extraido)

        return "\n".join(partes)

    except Exception as e:
        return f"Erro ao ler PDF: {str(e)}"


# Mantém o nome usado no código original.
read_pdf = ler_pdf


def read_excel_or_csv(file):
    """Lê CSV/XLSX e devolve representação textual da tabela."""
    try:
        nome = getattr(file, "name", "").lower()

        if nome.endswith(".csv"):
            try:
                df = pd.read_csv(file)
            except UnicodeDecodeError:
                file.seek(0)
                df = pd.read_csv(file, encoding="latin-1")
        else:
            df = pd.read_excel(file)

        return df.to_string(index=False)

    except Exception as e:
        return f"Erro ao ler planilha: {str(e)}"


def gerar_imagem_peca_temp(nome_peca):
    """Gera um esquemático genérico de uma peça para o PDF."""
    try:
        plt.close("all")

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.set_facecolor("#0a192f")
        fig.patch.set_facecolor("#0a192f")

        rect = patches.Rectangle(
            (0.1, 0.2),
            0.8,
            0.6,
            linewidth=2,
            edgecolor="#00d2ff",
            facecolor="#172a45"
        )
        ax.add_patch(rect)

        ax.text(
            0.5,
            0.5,
            f"PEÇA: {str(nome_peca)[:25]}",
            color="white",
            fontsize=10,
            ha="center",
            va="center",
            weight="bold"
        )

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_file.close()

        plt.savefig(
            tmp_file.name,
            format="png",
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
            edgecolor="none"
        )
        plt.close("all")

        return tmp_file.name

    except Exception:
        plt.close("all")
        return None


def criar_pdf_com_desenhos(titulo, conteudo_texto, lista_pecas_desenho=None):
    """Cria PDF com relatório e esquemáticos das peças."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    titulo_limpo = str(titulo).encode("latin-1", "replace").decode("latin-1")
    pdf.cell(
        pdf.epw,
        10,
        text=titulo_limpo,
        new_x="LMARGIN",
        new_y="NEXT",
        align="C"
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", size=10)
    largura_util = pdf.epw

    for linha in str(conteudo_texto).split("\n"):
        texto_limpo = linha.encode("latin-1", "replace").decode("latin-1")

        try:
            if not texto_limpo.strip():
                pdf.ln(3)
            elif len(texto_limpo) > 90 and " " not in texto_limpo:
                for parte in textwrap.wrap(texto_limpo, 90):
                    pdf.multi_cell(
                        w=largura_util,
                        h=5.5,
                        text=parte,
                        new_x="LMARGIN",
                        new_y="NEXT"
                    )
            else:
                pdf.multi_cell(
                    w=largura_util,
                    h=5.5,
                    text=texto_limpo,
                    new_x="LMARGIN",
                    new_y="NEXT"
                )
        except Exception:
            pdf.multi_cell(
                w=largura_util,
                h=5.5,
                text="[Linha com formatação inválida omitida]",
                new_x="LMARGIN",
                new_y="NEXT"
            )

    if lista_pecas_desenho:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(
            pdf.epw,
            10,
            text="ESQUEMÁTICO TÉCNICO DAS PEÇAS",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C"
        )
        pdf.ln(5)

        for peca in lista_pecas_desenho:
            if not isinstance(peca, dict):
                continue

            nome = peca.get("nome", "Peça")
            descricao = peca.get("descricao", "")

            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(
                pdf.epw,
                6,
                text=f"Componente: {str(nome)}",
                new_x="LMARGIN",
                new_y="NEXT"
            )

            if descricao:
                pdf.set_font("Helvetica", size=9)
                desc_limpa = str(descricao).encode(
                    "latin-1", "replace"
                ).decode("latin-1")
                pdf.multi_cell(
                    pdf.epw,
                    5,
                    text=desc_limpa,
                    new_x="LMARGIN",
                    new_y="NEXT"
                )

            img_path = gerar_imagem_peca_temp(nome)

            if img_path and os.path.exists(img_path):
                try:
                    pdf.image(img_path, w=100)
                    pdf.ln(5)
                except Exception:
                    pass
                finally:
                    try:
                        os.unlink(img_path)
                    except OSError:
                        pass

    return bytes(pdf.output())


def validar_chave(chave, nome):
    if not chave or not chave.strip():
        st.error(f"Informe a API Key do {nome} na barra lateral.")
        return False
    return True


# ==============================================================================
# FUNÇÕES DE CHAMADA ÀS APIS
# ==============================================================================
def call_gemini(contents_payload, api_key, model="gemini-3.6-flash"):
    if not validar_chave(api_key, "Gemini"):
        raise ValueError("Gemini API Key não informada.")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents_payload
        )
        return response.text

    except Exception as e:
        error_msg = str(e)

        # Fallback somente quando há indicação de indisponibilidade/modelo inválido.
        if (
            "503" in error_msg
            or "high demand" in error_msg.lower()
            or "404" in error_msg
        ):
            fallback_model = "gemini-1.5-flash"
            st.warning(
                f"⚠️ O modelo {model} está indisponível/sobrecarregado. "
                f"Tentando o modelo reserva ({fallback_model})..."
            )

            try:
                response_fallback = client.models.generate_content(
                    model=fallback_model,
                    contents=contents_payload
                )
                return response_fallback.text
            except Exception as e2:
                raise Exception(
                    f"Erro no modelo de reserva: {str(e2)}"
                ) from e2

        raise


def call_groq(prompt, api_key, model="llama-3.3-70b-versatile"):
    if not validar_chave(api_key, "Groq"):
        raise ValueError("Groq API Key não informada.")

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

    res = requests.post(url, json=payload, headers=headers, timeout=120)

    if res.status_code == 200:
        data = res.json()
        return data["choices"][0]["message"]["content"]

    raise Exception(f"Erro Groq ({res.status_code}): {res.text}")


def call_openrouter_free(
    prompt,
    api_key,
    model="meta-llama/llama-3.3-70b-instruct:free"
):
    if not validar_chave(api_key, "OpenRouter"):
        raise ValueError("OpenRouter API Key não informada.")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    res = requests.post(url, json=payload, headers=headers, timeout=120)

    if res.status_code == 200:
        data = res.json()
        return data["choices"][0]["message"]["content"]

    raise Exception(
        f"Erro OpenRouter ({res.status_code}): {res.text}"
    )


# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.header("🔑 Configurações de APIs")

    try:
        default_gemini = st.secrets.get("GEMINI_API_KEY", "")
        default_groq = st.secrets.get("GROQ_API_KEY", "")
        default_openrouter = st.secrets.get("OPENROUTER_API_KEY", "")
    except Exception:
        default_gemini = ""
        default_groq = ""
        default_openrouter = ""

    gemini_key = st.text_input(
        "1. Gemini API Key:",
        value=default_gemini,
        type="password"
    )
    groq_key = st.text_input(
        "2. Groq API Key:",
        value=default_groq,
        type="password"
    )
    openrouter_key = st.text_input(
        "3. OpenRouter API Key:",
        value=default_openrouter,
        type="password"
    )

    st.divider()
    st.header("📁 Projetos da Sessão")

    if st.session_state.historico_projetos:
        for idx, item in enumerate(st.session_state.historico_projetos):
            with st.expander(f"📌 {item['titulo']}"):
                st.caption(f"Tipo: {item['tipo']}")
                st.write(item["resumo"][:150] + "...")

                pdf_data = criar_pdf_com_desenhos(
                    item["titulo"],
                    item["conteudo"],
                    item.get("pecas")
                )

                st.download_button(
                    "📄 Baixar PDF com Desenhos",
                    data=pdf_data,
                    file_name=(
                        f"{item['titulo'][:30].replace(' ', '_')}.pdf"
                    ),
                    mime="application/pdf",
                    key=f"btn_pdf_{idx}"
                )
    else:
        st.info("Nenhum projeto salvo na sessão.")


# ==============================================================================
# NAVEGAÇÃO PRINCIPAL
# ==============================================================================
st.title("⚡ Multi-Engine IA: Invenções & Engenharia Pro")

tabs = st.tabs([
    "🧪 Agentes de Invenção",
    "📐 Blueprint & Peças",
    "📋 Orçamentos e Extração",
    "✂️ Otimizador de Corte",
    "🎬 Vídeos & Narração"
])


# ==============================================================================
# ABA 1 — AGENTES DE INVENÇÃO
# ==============================================================================
with tabs[0]:
    st.subheader("Laboratório Multiagente de Prototipagem")

    col1, col2 = st.columns(2)

    with col1:
        provedor = st.selectbox(
            "Provedor dos Agentes:",
            [
                "Google Gemini",
                "Groq (Llama 3.3)",
                "OpenRouter Free"
            ]
        )

    with col2:
        area_projeto = st.selectbox(
            "Área:",
            [
                "Engenharia Química",
                "Mecânica/Robótica",
                "Eletrônica/IoT",
                "Biotecnologia"
            ]
        )

    ideia = st.text_area(
        "Descreva a ideia:",
        placeholder=(
            "Ex: Válvula de retenção biomimética automatizada..."
        )
    )

    if st.button("🚀 Processar Invenção", type="primary"):
        if not ideia.strip():
            st.warning("Preencha a ideia primeiro.")
        else:
            try:
                def exec_agente(prompt):
                    if "Gemini" in provedor:
                        return call_gemini(prompt, gemini_key)
                    if "Groq" in provedor:
                        return call_groq(prompt, groq_key)
                    return call_openrouter_free(
                        prompt,
                        openrouter_key
                    )

                with st.status(
                    "🕵️ Agente 1 (Pesquisador): "
                    "Verificando viabilidade...",
                    expanded=True
                ):
                    r1 = exec_agente(
                        f"Pesquisador Científico em {area_projeto}. "
                        f"Analise viabilidade de: {ideia}"
                    )

                with st.status(
                    "⚙️ Agente 2 (Engenheiro): "
                    "Criando especificações...",
                    expanded=True
                ):
                    r2 = exec_agente(
                        "Engenheiro. Com base no parecer abaixo, "
                        "elabore o projeto técnico detalhado.\n\n"
                        f"PARECER:\n{r1}"
                    )

                with st.status(
                    "🛠️ Agente 3 (Maker): "
                    "Gerando Lista de Materiais e Peças...",
                    expanded=True
                ):
                    prompt_maker = f"""
Com base no projeto abaixo:

{r2}

Crie a Lista de Materiais completa contendo componentes
estruturais E ferragens/parafusos necessários.

Retorne obrigatoriamente APENAS JSON válido, sem Markdown,
sem ```json e sem comentários.

Estrutura obrigatória:
{{
  "lista_materiais": [
    {{
      "ITEM": "1",
      "DESCRIÇÃO": "Nome da Peça ou Ferragem",
      "COMP. (mm)": "100",
      "LARG. (mm)": "50",
      "QTD.": "4",
      "MATERIAL": "Aço/MDF/Plástico"
    }}
  ],
  "pecas_para_desenho": [
    {{
      "nome": "Nome da Peça",
      "descricao": "Descrição geométrica"
    }}
  ]
}}
""".strip()

                    r3_bruto = exec_agente(prompt_maker)
                    json_str_inv = extrair_json_seguro(r3_bruto)
                    dados_inv = json.loads(json_str_inv)

                st.success("Dossiê e Peças Gerados com Sucesso!")

                lista_materiais = dados_inv.get(
                    "lista_materiais",
                    []
                )

                materiais_json = json.dumps(
                    lista_materiais,
                    indent=2,
                    ensure_ascii=False
                )

                dossie_completo = (
                    f"DOSSIÊ TÉCNICO: {ideia[:80]}\n\n"
                    f"--- 1. VIABILIDADE ---\n{r1}\n\n"
                    f"--- 2. PROJETO ---\n{r2}\n\n"
                    "--- 3. MATERIAIS & FERRAGENS ---\n"
                    f"{materiais_json}"
                )

                st.session_state.historico_projetos.append({
                    "titulo": f"Invenção: {ideia[:40]}...",
                    "tipo": "Invenção",
                    "resumo": r1[:150],
                    "conteudo": dossie_completo,
                    "pecas": dados_inv.get(
                        "pecas_para_desenho",
                        []
                    )
                })

                st.markdown(dossie_completo)

                pdf_bytes = criar_pdf_com_desenhos(
                    "DOSSIE DE INVENCAO",
                    dossie_completo,
                    dados_inv.get("pecas_para_desenho", [])
                )

                st.download_button(
                    "📄 Baixar Dossiê Completo + Desenhos em PDF",
                    data=pdf_bytes,
                    file_name="Dossie_Invention_Com_Desenhos.pdf",
                    mime="application/pdf"
                )

            except json.JSONDecodeError as e:
                st.error(
                    "A IA não retornou um JSON válido no Agente 3. "
                    f"Detalhe: {e}"
                )
            except Exception as e:
                st.error(f"Erro: {str(e)}")


# ==============================================================================
# ABA 2 — BLUEPRINT & DESENHO DE PEÇAS
# ==============================================================================
with tabs[1]:
    st.subheader("📐 Gerador de Desenhos Técnicos e Esquema de Peças")

    descricao_peca = st.text_input(
        "Descrição da peça:",
        placeholder=(
            "Ex: Engrenagem reta de 12 dentes com "
            "furo central de 8mm"
        )
    )

    if st.button("🎨 Gerar Desenho Técnico 2D"):
        if not descricao_peca.strip():
            st.warning("Descreva a peça primeiro.")
        elif not gemini_key:
            st.error("Insira a chave Gemini na barra lateral.")
        else:
            with st.spinner("Desenhando esquemático com cotas técnicas..."):
                prompt_draw = f"""
Atue como um gerador de gráficos Python (Matplotlib).

Crie APENAS um código Python funcional que use
matplotlib.pyplot para desenhar um esquema técnico 2D
cotado da peça:

'{descricao_peca}'

REGRAS OBRIGATÓRIAS:
- Defina: fig, ax = plt.subplots(figsize=(10, 6))
- Use fundo estilo blueprint (facecolor='#0a192f')
  no fig e ax.
- Use linhas e textos em branco ou azul claro ('#00d2ff').
- NUNCA use plt.tight_layout().
- O código deve ser autocontido.
- Responda APENAS com código Python puro.
""".strip()

                try:
                    codigo_bruto = call_gemini(
                        prompt_draw,
                        gemini_key
                    )
                    codigo_python = limpar_codigo_python(
                        codigo_bruto
                    )

                    plt.close("all")

                    fig, ax = plt.subplots(figsize=(10, 6))
                    exec_globals = {
                        "plt": plt,
                        "fig": fig,
                        "ax": ax,
                        "patches": patches
                    }

                    exec(codigo_python, exec_globals)

                    st.pyplot(
                        plt.gcf(),
                        use_container_width=True
                    )
                    plt.close("all")
                    st.success(
                        "Desenho Técnico Gerado com Sucesso!"
                    )

                except Exception as e:
                    plt.close("all")
                    st.error(
                        f"Erro ao desenhar: {str(e)}"
                    )


# ==============================================================================
# ABA 3 — ORÇAMENTOS TÉCNICOS & EXTRAÇÃO
# ==============================================================================
with tabs[2]:
    st.subheader(
        "📋 Leitor de Projetos, Imagens e "
        "Extração de Materiais/Ferragens"
    )

    st.markdown(
        "Faça upload de **Imagens (Plantas)**, **PDFs técnicos** "
        "ou **Planilhas** para converter na Lista Completa de "
        "Insumos (Peças + Ferragens)."
    )

    scale_info = st.text_input(
        "Referência de escala (Opcional):",
        placeholder="Ex: O vão principal tem 3.50m..."
    )

    uploaded_files = st.file_uploader(
        "Upload de Arquivos:",
        type=[
            "pdf",
            "xlsx",
            "csv",
            "png",
            "jpg",
            "jpeg"
        ],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button(
            "🚀 Analisar Documentos e Gerar Orçamento Completo",
            type="primary"
        ):
            if not gemini_key:
                st.error(
                    "Insira a chave Gemini na barra lateral."
                )
            else:
                with st.spinner(
                    "Analisando documentos, peças e ferragens..."
                ):
                    try:
                        contents_payload = []
                        texto_extraido = ""

                        for arquivo in uploaded_files:
                            if arquivo.type.startswith("image"):
                                img = Image.open(arquivo)
                                st.image(
                                    img,
                                    width=250,
                                    caption=arquivo.name
                                )
                                contents_payload.append(img)

                            elif arquivo.type == "application/pdf":
                                texto = read_pdf(arquivo)
                                texto_extraido += (
                                    f"\n--- Conteúdo do PDF "
                                    f"({arquivo.name}) ---\n{texto}"
                                )

                            elif arquivo.name.lower().endswith(
                                (".xlsx", ".xls", ".csv")
                            ):
                                texto = read_excel_or_csv(
                                    arquivo
                                )
                                texto_extraido += (
                                    f"\n--- Conteúdo da Planilha "
                                    f"({arquivo.name}) ---\n{texto}"
                                )

                        if texto_extraido:
                            contents_payload.append(texto_extraido)

                        escala_texto = (
                            f"Escala de Referência Visual: "
                            f"{scale_info}"
                            if scale_info
                            else "Nenhuma escala adicional foi informada."
                        )

                        # ------------------------------------------------------------------
                        # CORREÇÃO PRINCIPAL DO ERRO ORIGINAL:
                        # o f-string agora possui abertura e fechamento corretos.
                        # As chaves do JSON são duplicadas porque estão dentro de f-string.
                        # ------------------------------------------------------------------
                        prompt_orcamento = f"""
Você é um Engenheiro de Processos e Orçamentista.

Analise TODOS os documentos e imagens fornecidos.

{escala_texto}

OBJETIVO:
Extrair e deduzir TODAS as informações dos componentes,
incluindo chapas, estruturas, perfis, peças, acabamentos,
fixadores E TODAS AS FERRAGENS NECESSÁRIAS
(parafusos, cavilhas, minifix, dobradiças, suportes,
porcas, arruelas, rebites, ímãs, etc.).

REGRAS:
1. Não invente medidas que possam ser lidas nos documentos.
2. Quando uma medida não estiver disponível, use "NÃO INFORMADO".
3. Preserve unidades e materiais identificados.
4. Separe peças estruturais de ferragens quando possível.
5. Informe quantidade estimada quando puder ser deduzida.
6. Considere as imagens e o texto extraído em conjunto.
7. Gere OBRIGATORIAMENTE APENAS JSON VÁLIDO.
8. NÃO use Markdown.
9. NÃO coloque ```json.
10. Não inclua nenhum texto antes ou depois do JSON.

ESTRUTURA EXATA:

{{
  "relatorio_texto": "Resumo executivo do projeto, recomendações técnicas e análise de insumos.",
  "lista_materiais": [
    {{
      "ITEM": "1",
      "DESCRIÇÃO": "BASE-FRONTAL",
      "COMP. (mm)": "1100",
      "LARG. (mm)": "90",
      "QTD.": "2",
      "MATERIAL": "MDF GRAFITE MATT 15MM"
    }},
    {{
      "ITEM": "2",
      "DESCRIÇÃO": "PARAFUSO MINIFIX",
      "COMP. (mm)": "-",
      "LARG. (mm)": "-",
      "QTD.": "10",
      "MATERIAL": "AÇO ZINCADO"
    }}
  ],
  "pecas_para_desenho": [
    {{
      "nome": "BASE-FRONTAL",
      "descricao": "Peça estrutural 1100x90mm"
    }}
  ]
}}
""".strip()

                        resposta_orcamento = call_gemini(
                            contents_payload + [prompt_orcamento],
                            gemini_key
                        )

                        json_str = extrair_json_seguro(
                            resposta_orcamento
                        )
                        dados_orcamento = json.loads(json_str)

                        relatorio = dados_orcamento.get(
                            "relatorio_texto",
                            "Relatório não informado."
                        )

                        lista_materiais = dados_orcamento.get(
                            "lista_materiais",
                            []
                        )

                        pecas_desenho = dados_orcamento.get(
                            "pecas_para_desenho",
                            []
                        )

                        st.success(
                            "✅ Análise e orçamento gerados com sucesso!"
                        )

                        st.markdown("### 📊 Relatório Técnico")
                        st.write(relatorio)

                        st.markdown("### 🧱 Lista de Materiais")

                        if lista_materiais:
                            df_materiais = pd.DataFrame(
                                lista_materiais
                            )
                            st.dataframe(
                                df_materiais,
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.warning(
                                "A IA não retornou itens na "
                                "lista de materiais."
                            )

                        materiais_json_orcamento = json.dumps(
                            lista_materiais,
                            indent=2,
                            ensure_ascii=False
                        )

                        conteudo_orcamento = (
                            "RELATÓRIO TÉCNICO DE ORÇAMENTO\n\n"
                            f"{relatorio}\n\n"
                            "LISTA DE MATERIAIS\n\n"
                            f"{materiais_json_orcamento}"
                        )

                        st.session_state.historico_projetos.append({
                            "titulo": "Orçamento Técnico",
                            "tipo": "Orçamento / Extração",
                            "resumo": str(relatorio)[:150],
                            "conteudo": conteudo_orcamento,
                            "pecas": pecas_desenho
                        })

                        pdf_orcamento = criar_pdf_com_desenhos(
                            "ORCAMENTO TECNICO",
                            conteudo_orcamento,
                            pecas_desenho
                        )

                        st.download_button(
                            "📄 Baixar Orçamento Técnico em PDF",
                            data=pdf_orcamento,
                            file_name="Orcamento_Tecnico.pdf",
                            mime="application/pdf",
                            key="download_orcamento_pdf"
                        )

                        st.download_button(
                            "🧾 Baixar JSON do Orçamento",
                            data=json.dumps(
                                dados_orcamento,
                                indent=2,
                                ensure_ascii=False
                            ).encode("utf-8"),
                            file_name="orcamento_tecnico.json",
                            mime="application/json",
                            key="download_orcamento_json"
                        )

                    except json.JSONDecodeError as e:
                        st.error(
                            "A resposta da IA não pôde ser convertida "
                            f"em JSON válido: {e}"
                        )
                        with st.expander(
                            "Ver resposta bruta da IA"
                        ):
                            st.code(
                                resposta_orcamento
                                if "resposta_orcamento" in locals()
                                else "Sem resposta."
                            )

                    except Exception as e:
                        st.error(
                            f"Erro ao analisar documentos: {str(e)}"
                        )


# ==============================================================================
# ABA 4 — OTIMIZADOR DE CORTE
# ==============================================================================
with tabs[3]:
    st.subheader("✂️ Otimizador de Corte")

    st.info(
        "Informe as dimensões das chapas e das peças para obter "
        "uma estimativa de aproveitamento."
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        chapa_comp = st.number_input(
            "Comprimento da chapa (mm)",
            min_value=1.0,
            value=2750.0,
            step=10.0
        )

    with col_b:
        chapa_larg = st.number_input(
            "Largura da chapa (mm)",
            min_value=1.0,
            value=1850.0,
            step=10.0
        )

    with col_c:
        espessura = st.number_input(
            "Espessura (mm)",
            min_value=0.1,
            value=15.0,
            step=0.5
        )

    st.caption(
        "Para um plano de corte industrial otimizado, considere "
        "também sentido do veio, espessura do corte, margem e "
        "restrições da seccionadora."
    )

    dados_corte = st.data_editor(
        pd.DataFrame(
            [
                {
                    "PEÇA": "Exemplo",
                    "COMP. (mm)": 500,
                    "LARG. (mm)": 300,
                    "QTD.": 1
                }
            ]
        ),
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("📐 Calcular Aproveitamento"):
        try:
            area_chapa = chapa_comp * chapa_larg
            area_total = 0.0

            for _, row in dados_corte.iterrows():
                comp = float(row["COMP. (mm)"])
                larg = float(row["LARG. (mm)"])
                qtd = float(row["QTD."])
                area_total += comp * larg * qtd

            aproveitamento = (
                area_total / area_chapa * 100
                if area_chapa > 0
                else 0
            )

            chapas_teoricas = (
                area_total / area_chapa
                if area_chapa > 0
                else 0
            )

            st.metric(
                "Aproveitamento teórico",
                f"{aproveitamento:.2f}%"
            )
            st.metric(
                "Chapas teóricas",
                f"{chapas_teoricas:.2f}"
            )

            if aproveitamento <= 100:
                st.success(
                    "A área total das peças cabe teoricamente "
                    "na área de uma chapa, mas isso NÃO substitui "
                    "um plano geométrico de corte."
                )
            else:
                st.warning(
                    "A área total das peças supera a área de uma chapa."
                )

        except Exception as e:
            st.error(f"Erro no cálculo: {e}")


# ==============================================================================
# ABA 5 — VÍDEOS & NARRAÇÃO
# ==============================================================================
with tabs[4]:
    st.subheader("🎬 Vídeos & Narração")

    texto_narracao = st.text_area(
        "Texto para narração:",
        placeholder=(
            "Digite aqui o texto que deseja transformar "
            "em áudio..."
        )
    )

    idioma = st.selectbox(
        "Idioma:",
        ["pt", "en", "es"]
    )

    if st.button("🔊 Gerar Narração"):
        if not texto_narracao.strip():
            st.warning("Digite um texto para a narração.")
        else:
            try:
                with st.spinner("Gerando áudio..."):
                    audio_buffer = io.BytesIO()

                    tts = gTTS(
                        text=texto_narracao,
                        lang=idioma
                    )

                    tts.write_to_fp(audio_buffer)
                    audio_buffer.seek(0)

                st.audio(
                    audio_buffer,
                    format="audio/mp3"
                )

                st.download_button(
                    "⬇️ Baixar MP3",
                    data=audio_buffer.getvalue(),
                    file_name="narracao.mp3",
                    mime="audio/mpeg"
                )

            except Exception as e:
                st.error(
                    "Não foi possível gerar a narração. "
                    f"Erro: {str(e)}"
                )


# ==============================================================================
# RODAPÉ
# ==============================================================================
st.divider()
st.caption(
    "Multi-Engine IA • Engenharia, Projetos, Extração e Orçamentos"
)
