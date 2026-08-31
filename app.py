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
    page_title="Multi-Engine IA: CAD & Engenharia Industrial Pro",
    page_icon="⚡",
    layout="wide"
)

# ==============================================================================
# INICIALIZAÇÃO DO HISTÓRICO DE SESSÃO
# ==============================================================================
if "historico_projetos" not in st.session_state:
    st.session_state.historico_projetos = []

# ==============================================================================
# FUNÇÕES UTILITÁRIAS E DE PARSE
# ==============================================================================
def limpar_codigo_python(texto_bruto):
    if not texto_bruto:
        return ""
    texto = str(texto_bruto)
    texto = re.sub(r"^```python\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"^```\s*", "", texto)
    texto = re.sub(r"\s*```$", "", texto)
    return texto.strip()


def extrair_json_seguro(texto_bruto):
    if not texto_bruto:
        raise ValueError("A IA retornou uma resposta vazia.")
    texto = str(texto_bruto).strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", texto, re.IGNORECASE | re.DOTALL)
    if match:
        texto = match.group(1).strip()
    inicio = texto.find("{")
    fim = texto.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        texto = texto[inicio:fim + 1]
    return texto.strip()


def ler_pdf(file):
    try:
        reader = pypdf.PdfReader(file)
        partes = [page.extract_text() for page in reader.pages if page.extract_text()]
        return "\n".join(partes)
    except Exception as e:
        return f"Erro ao ler PDF: {str(e)}"

read_pdf = ler_pdf


def read_excel_or_csv(file):
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
        return df
    except Exception as e:
        st.error(f"Erro ao ler planilha: {str(e)}")
        return pd.DataFrame()


# ==============================================================================
# MOTOR CAD DE ALTA PRECISÃO (VISTAS ORTOGONAIS, COTAS E MATRIZ DE FURAÇÃO)
# ==============================================================================
def gerar_desenho_cad_industrial(nome_peca, comp=1200, larg=600):
    """Gera um projeto CAD profissional com 3 painéis: Vista Frontal, Perfil Lateral e Matriz de Furação Técnica."""
    try:
        plt.close("all")
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5.5))
        fig.patch.set_facecolor("#0a192f")
        
        for ax in [ax1, ax2, ax3]:
            ax.set_facecolor("#0a192f")
            ax.grid(True, color="#1e3a8a", linestyle=":", alpha=0.4)

        # --- PAINEL 1: VISTA FRONTAL COM COTAS ---
        rect_front = patches.Rectangle((0.15, 0.2), 0.7, 0.6, linewidth=2, edgecolor="#38bdf8", facecolor="#1e293b", hatch="//")
        ax1.add_patch(rect_front)
        
        # Furações (Minifix / Cavilhas)
        ax1.add_patch(patches.Circle((0.25, 0.5), 0.035, facecolor="#ef4444", edgecolor="white", lw=1.2))
        ax1.add_patch(patches.Circle((0.75, 0.5), 0.035, facecolor="#ef4444", edgecolor="white", lw=1.2))
        ax1.text(0.25, 0.5, "Ø15", color="white", fontsize=6, ha="center", va="center", weight="bold")
        ax1.text(0.75, 0.5, "Ø15", color="white", fontsize=6, ha="center", va="center", weight="bold")

        # Linhas de Cota
        ax1.annotate('', xy=(0.15, 0.12), xytext=(0.85, 0.12), arrowprops=dict(arrowstyle="<->", color="#fbbf24", lw=1.5))
        ax1.text(0.5, 0.06, f"COMP: {comp} mm", color="#fbbf24", fontsize=9, ha="center", weight="bold")
        
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.set_title("VISTA FRONTAL & USINAGEM", color="white", fontsize=10, weight="bold")
        ax1.axis("off")

        # --- PAINEL 2: VISTA LATERAL / CORTE ---
        rect_side = patches.Rectangle((0.35, 0.2), 0.3, 0.6, linewidth=2, edgecolor="#38bdf8", facecolor="#334155")
        ax2.add_patch(rect_side)
        
        ax2.annotate('', xy=(0.25, 0.2), xytext=(0.25, 0.8), arrowprops=dict(arrowstyle="<->", color="#fbbf24", lw=1.5))
        ax2.text(0.12, 0.5, f"LARG:\n{larg} mm", color="#fbbf24", fontsize=9, ha="center", weight="bold")
        
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.set_title("PERFIL / ESPESSURA", color="white", fontsize=10, weight="bold")
        ax2.axis("off")

        # --- PAINEL 3: MATRIZ DE COORDENADAS DE FURAÇÃO ---
        ax3.text(0.05, 0.85, "TABELA DE FUROS (CNC)", color="#38bdf8", fontsize=10, weight="bold")
        tabela_dados = [
            ["Furo", "X (mm)", "Y (mm)", "Tipo", "Diâmetro"],
            ["H1", "50.0", f"{larg/2}", "Minifix", "Ø15mm"],
            ["H2", f"{comp-50}", f"{larg/2}", "Minifix", "Ø15mm"],
            ["C1", "32.0", "9.0", "Cavilha", "Ø8mm"],
            ["C2", f"{comp-32}", "9.0", "Cavilha", "Ø8mm"]
        ]
        
        y_pos = 0.65
        for row in tabela_dados:
            x_pos = 0.05
            for col in row:
                ax3.text(x_pos, y_pos, col, color="white" if y_pos == 0.65 else "#cbd5e1", fontsize=8, weight="bold" if y_pos == 0.65 else "normal")
                x_pos += 0.2
            y_pos -= 0.12
            
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)
        ax3.set_title("MATRIZ CNC", color="white", fontsize=10, weight="bold")
        ax3.axis("off")

        plt.suptitle(f"DETALHAMENTO TÉCNICO CAD • {str(nome_peca).upper()}", color="#38bdf8", fontsize=13, weight="bold", y=0.96)

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_file.close()
        plt.savefig(tmp_file.name, format="png", bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close("all")
        return tmp_file.name
    except Exception:
        plt.close("all")
        return None


# ==============================================================================
# MOTOR DE NESTING GRÁFICO (APROVEITAMENTO DE CORTE)
# ==============================================================================
def gerar_grafico_nesting_temp(chapa_c=2750, chapa_l=1850, lista_pecas=None):
    try:
        plt.close("all")
        fig, ax = plt.subplots(figsize=(9, 6))
        ax.set_facecolor("#0f172a")
        fig.patch.set_facecolor("#0f172a")

        chapa_rect = patches.Rectangle((0, 0), chapa_c, chapa_l, linewidth=2, edgecolor="#38bdf8", facecolor="#1e293b")
        ax.add_patch(chapa_rect)

        cores = ["#f43f5e", "#fbbf24", "#34d399", "#38bdf8", "#a855f7", "#ec4899", "#f97316"]
        if not lista_pecas:
            lista_pecas = [{"COMP": 1000, "LARG": 500, "QTD": 2, "NOME": "Exemplo"}]

        curr_x, curr_y = 60.0, 60.0
        max_row_h = 0.0
        idx_cor = 0

        for p in lista_pecas:
            c = float(p.get("COMP", 500))
            l = float(p.get("LARG", 300))
            qtd = int(p.get("QTD", 1))
            nome = str(p.get("NOME", "Peça"))

            for _ in range(min(qtd, 15)):
                if curr_x + c > chapa_c - 60:
                    curr_x = 60.0
                    curr_y += max_row_h + 60.0
                    max_row_h = 0.0
                if curr_y + l > chapa_l - 60:
                    break

                cor = cores[idx_cor % len(cores)]
                p_rect = patches.Rectangle((curr_x, curr_y), c, l, linewidth=1, edgecolor="white", facecolor=cor, alpha=0.9)
                ax.add_patch(p_rect)
                ax.text(curr_x + c/2, curr_y + l/2, f"{nome[:10]}\n{int(c)}x{int(l)}", color="#0f172a", fontsize=7, ha="center", va="center", weight="bold")

                max_row_h = max(max_row_h, l)
                curr_x += c + 30.0
                idx_cor += 1

        ax.set_xlim(-150, chapa_c + 150)
        ax.set_ylim(-150, chapa_l + 150)
        ax.set_aspect('equal')
        ax.axis("off")
        ax.set_title("MAPA DE DISTRIBUIÇÃO GRÁFICA DE CORTE (NESTING)", color="white", fontsize=12, weight="bold", pad=15)

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_file.close()
        plt.savefig(tmp_file.name, format="png", bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close("all")
        return tmp_file.name
    except Exception:
        plt.close("all")
        return None


# ==============================================================================
# GERAÇÃO DE PDF APOSTILA COMERCIAL COLORIDO
# ==============================================================================
class PDFComercialColorido(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 22, 'F')
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 6)
        self.cell(0, 10, "RELATÓRIO TÉCNICO COMERCIAL & ENGENHARIA", 0, 0, "L")
        self.set_xy(-60, 6)
        self.cell(50, 10, "DOCUMENTAÇÃO PRO", 0, 0, "R")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Página {self.page_no()} | Multi-Engine IA Industrial Suite", 0, 0, "C")


def criar_pdf_relatorio_comercial(titulo, conteudo_texto, lista_pecas_desenho=None, grafico_nesting_path=None):
    pdf = PDFComercialColorido()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, str(titulo).encode("latin-1", "replace").decode("latin-1"), 0, 1, "L")
    pdf.set_draw_color(56, 189, 248)
    pdf.set_line_width(1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(50, 50, 50)
    largura_util = pdf.epw

    for linha in str(conteudo_texto).split("\n"):
        linha_limpa = linha.encode("latin-1", "replace").decode("latin-1")
        try:
            if not linha_limpa.strip():
                pdf.ln(3)
            elif "---" in linha_limpa or "===" in linha_limpa:
                pdf.ln(4)
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(30, 58, 138)
                pdf.cell(largura_util, 7, linha_limpa, 0, 1, "L")
                pdf.set_font("Helvetica", size=10)
                pdf.set_text_color(50, 50, 50)
            else:
                pdf.multi_cell(largura_util, 5.5, linha_limpa, 0, "L")
        except Exception:
            pdf.multi_cell(largura_util, 5.5, "[Linha omitida]", 0, "L")

    if grafico_nesting_path and os.path.exists(grafico_nesting_path):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 10, "MAPA GRÁFICO DE CORTE (NESTING OTIMIZADO)", 0, 1, "C")
        pdf.ln(5)
        try:
            pdf.image(grafico_nesting_path, w=175)
            pdf.ln(5)
        except Exception:
            pass

    if lista_pecas_desenho:
        for peca in lista_pecas_desenho:
            if not isinstance(peca, dict):
                continue
            pdf.add_page()
            nome = peca.get("nome", "Peça")
            comp = peca.get("comp", 1200)
            larg = peca.get("larg", 600)

            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, f"DETALHAMENTO CAD: {str(nome).upper()}", 0, 1, "C")
            pdf.set_font("Helvetica", size=10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, f"Dimensões Principais: {comp} x {larg} mm", 0, 1, "C")
            pdf.ln(5)

            img_cad = gerar_desenho_cad_industrial(nome, comp, larg)
            if img_cad and os.path.exists(img_cad):
                try:
                    pdf.image(img_cad, w=185)
                    pdf.ln(5)
                except Exception:
                    pass
                finally:
                    try:
                        os.unlink(img_cad)
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
        response = client.models.generate_content(model=model, contents=contents_payload)
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "high demand" in error_msg.lower() or "404" in error_msg:
            fallback_model = "gemini-1.5-flash"
            try:
                response_fallback = client.models.generate_content(model=fallback_model, contents=contents_payload)
                return response_fallback.text
            except Exception as e2:
                raise Exception(f"Erro no modelo de reserva: {str(e2)}") from e2
        raise


def call_groq(prompt, api_key, model="llama-3.3-70b-versatile"):
    if not validar_chave(api_key, "Groq"):
        raise ValueError("Groq API Key não informada.")
    url = "[https://api.groq.com/openai/v1/chat/completions](https://api.groq.com/openai/v1/chat/completions)"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    res = requests.post(url, json=payload, headers=headers, timeout=120)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    raise Exception(f"Erro Groq ({res.status_code}): {res.text}")


def call_openrouter_free(prompt, api_key, model="meta-llama/llama-3.3-70b-instruct:free"):
    if not validar_chave(api_key, "OpenRouter"):
        raise ValueError("OpenRouter API Key não informada.")
    url = "[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    res = requests.post(url, json=payload, headers=headers, timeout=120)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    raise Exception(f"Erro OpenRouter ({res.status_code}): {res.text}")


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
        default_gemini = default_groq = default_openrouter = ""

    gemini_key = st.text_input("1. Gemini API Key:", value=default_gemini, type="password")
    groq_key = st.text_input("2. Groq API Key:", value=default_groq, type="password")
    openrouter_key = st.text_input("3. OpenRouter API Key:", value=default_openrouter, type="password")

    st.divider()
    st.header("📁 Projetos da Sessão")

    if st.session_state.historico_projetos:
        for idx, item in enumerate(st.session_state.historico_projetos):
            with st.expander(f"📌 {item['titulo']}"):
                st.caption(f"Tipo: {item['tipo']}")
                st.write(item["resumo"][:150] + "...")
                pdf_data = criar_pdf_relatorio_comercial(item["titulo"], item["conteudo"], item.get("pecas"), item.get("nesting_img"))
                st.download_button(
                    "📄 Baixar PDF Comercial Colorido",
                    data=pdf_data,
                    file_name=f"{item['titulo'][:30].replace(' ', '_')}.pdf",
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
    "📐 CAD Pro (Multivistas & CNC)",
    "📋 Orçamentos, Planilha Real & Nesting",
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
        provedor = st.selectbox("Provedor dos Agentes:", ["Google Gemini", "Groq (Llama 3.3)", "OpenRouter Free"])
    with col2:
        area_projeto = st.selectbox("Área:", ["Engenharia Química", "Mecânica/Robótica", "Eletrônica/IoT", "Biotecnologia"])

    ideia = st.text_area("Descreva a ideia:", placeholder="Ex: Válvula de retenção biomimética automatizada...")

    if st.button("🚀 Processar Invenção", type="primary"):
        if not ideia.strip():
            st.warning("Preencha a ideia primeiro.")
        else:
            try:
                def exec_agente(prompt):
                    if "Gemini" in provedor: return call_gemini(prompt, gemini_key)
                    if "Groq" in provedor: return call_groq(prompt, groq_key)
                    return call_openrouter_free(prompt, openrouter_key)

                with st.status("🕵️ Agente 1 (Pesquisador): Verificando viabilidade...", expanded=True):
                    r1 = exec_agente(f"Pesquisador Científico em {area_projeto}. Analise viabilidade de: {ideia}")

                with st.status("⚙️ Agente 2 (Engenheiro): Criando especificações...", expanded=True):
                    r2 = exec_agente(f"Engenheiro. Com base no parecer:\n{r1}\nElabore o projeto técnico detalhado.")

                with st.status("🛠️ Agente 3 (Maker): Gerando Lista de Materiais e Peças...", expanded=True):
                    prompt_maker = f"""
Com base no projeto abaixo:
{r2}

Crie a Lista de Materiais completa contendo componentes estruturais E ferragens/parafusos necessários.
Retorne obrigatoriamente APENAS JSON válido, sem Markdown, sem ```json.

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
      "comp": 100,
      "larg": 50,
      "descricao": "Detalhes geométricos com cotas e furações"
    }}
  ]
}}
""".strip()
                    r3_bruto = exec_agente(prompt_maker)
                    json_str_inv = extrair_json_seguro(r3_bruto)
                    dados_inv = json.loads(json_str_inv)

                st.success("Dossiê e Peças Gerados com Sucesso!")
                lista_materiais = dados_inv.get("lista_materiais", [])
                materiais_json = json.dumps(lista_materiais, indent=2, ensure_ascii=False)

                dossie_completo = (
                    f"DOSSIÊ TÉCNICO: {ideia[:80]}\n\n"
                    f"--- 1. VIABILIDADE ---\n{r1}\n\n"
                    f"--- 2. PROJETO ---\n{r2}\n\n"
                    f"--- 3. MATERIAIS & FERRAGENS ---\n{materiais_json}"
                )

                st.session_state.historico_projetos.append({
                    "titulo": f"Invenção: {ideia[:40]}...",
                    "tipo": "Invenção",
                    "resumo": r1[:150],
                    "conteudo": dossie_completo,
                    "pecas": dados_inv.get("pecas_para_desenho", [])
                })

                st.markdown(dossie_completo)
                pdf_bytes = criar_pdf_relatorio_comercial("DOSSIE DE INVENCAO", dossie_completo, dados_inv.get("pecas_para_desenho", []))
                st.download_button("📄 Baixar PDF Comercial Colorido", data=pdf_bytes, file_name="Dossie_Comercial.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"Erro: {str(e)}")


# ==============================================================================
# ABA 2 — CAD PRO (MULTIVISTAS & CNC)
# ==============================================================================
with tabs[1]:
    st.subheader("📐 CAD Pro: Gerador de Desenhos Técnicos Multivistas & Matriz CNC")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        peca_nome_input = st.text_input("Nome da Peça CAD:", value="Lateral de Gabinete")
    with col_d2:
        dim_comp = st.number_input("Comprimento (mm):", min_value=10.0, value=1200.0, step=50.0)
        dim_larg = st.number_input("Largura (mm):", min_value=10.0, value=600.0, step=50.0)

    if st.button("🎨 Renderizar Desenho CAD Industrial"):
        if not peca_nome_input.strip():
            st.warning("Informe o nome da peça.")
        else:
            with st.spinner("Gerando projeções ortogonais e tabela CNC..."):
                try:
                    img_path = gerar_desenho_cad_industrial(peca_nome_input, dim_comp, dim_larg)
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, caption=f"CAD Industrial Multivistas: {peca_nome_input}", use_container_width=True)
                        os.unlink(img_path)
                    st.success("Desenho CAD industrial gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao renderizar CAD: {e}")


# ==============================================================================
# ABA 3 — ORÇAMENTOS, PLANILHA REAL & NESTING
# ==============================================================================
with tabs[2]:
    st.subheader("📋 Orçamentos, Planilha Real Estilizada & Nesting Automático")
    st.markdown("Faça upload de **Imagens (Plantas/Projetos)**, **PDFs técnicos** ou **Planilhas** para extrair insumos, gerar planilha formatada e o mapa gráfico de corte.")

    col_mat_opt1, col_mat_opt2 = st.columns(2)
    with col_mat_opt1:
        chapa_padrao_comp = st.number_input("Comp. Chapa Base (mm):", min_value=100.0, value=2750.0, step=50.0)
    with col_mat_opt2:
        chapa_padrao_larg = st.number_input("Larg. Chapa Base (mm):", min_value=100.0, value=1850.0, step=50.0)

    scale_info = st.text_input("Referência de escala (Opcional):", placeholder="Ex: O vão principal tem 3.50m...")
    uploaded_files = st.file_uploader("Upload de Arquivos:", type=["pdf", "xlsx", "csv", "png", "jpg", "jpeg"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("🚀 Analisar Projeto, Gerar Planilha Real e Nesting", type="primary"):
            if not gemini_key:
                st.error("Insira a chave Gemini na barra lateral.")
            else:
                with st.spinner("Processando documentos, extraindo insumos e gerando planilha..."):
                    try:
                        contents_payload = []
                        texto_extraido = ""

                        for arquivo in uploaded_files:
                            if arquivo.type.startswith("image"):
                                img = Image.open(arquivo)
                                st.image(img, width=250, caption=arquivo.name)
                                contents_payload.append(img)
                            elif arquivo.type == "application/pdf":
                                texto = read_pdf(arquivo)
                                texto_extraido += f"\n--- Conteúdo do PDF ({arquivo.name}) ---\n{texto}"
                            elif arquivo.name.lower().endswith((".xlsx", ".xls", ".csv")):
                                df_upload = read_excel_or_csv(arquivo)
                                texto_extraido += f"\n--- Conteúdo da Planilha ({arquivo.name}) ---\n{df_upload.to_string(index=False)}"

                        if texto_extraido:
                            contents_payload.append(texto_extraido)

                        escala_texto = f"Escala de Referência Visual: {scale_info}" if scale_info else "Nenhuma escala adicional informada."

                        prompt_orcamento = f"""
Você é um Engenheiro de Processos e Orçamentista sênior. Analise TODOS os documentos e imagens fornecidos.
{escala_texto}

OBJETIVO:
Extrair e deduzir TODAS as informações dos componentes, incluindo chapas, estruturas, perfis, peças, acabamentos E FERRAGENS (parafusos, minifix, dobradiças, etc.).
Para peças lineares ou chapas, informe os valores numéricos exatos de comprimento e largura. Para ferragens unitárias, use "-".

Gere OBRIGATORIAMENTE APENAS JSON VÁLIDO, sem Markdown, sem ```json.

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
    }}
  ],
  "pecas_para_desenho": [
    {{
      "nome": "BASE-FRONTAL",
      "comp": 1100,
      "larg": 90,
      "descricao": "Peça estrutural 1100x90mm com furação"
    }}
  ]
}}
""".strip()

                        resposta_orcamento = call_gemini(contents_payload + [prompt_orcamento], gemini_key)
                        json_str = extrair_json_seguro(resposta_orcamento)
                        dados_orcamento = json.loads(json_str)

                        relatorio = dados_orcamento.get("relatorio_texto", "Relatório não informado.")
                        lista_materiais = dados_orcamento.get("lista_materiais", [])
                        pecas_desenho = dados_orcamento.get("pecas_para_desenho", [])

                        area_chapa_unit = chapa_padrao_comp * chapa_padrao_larg
                        area_pecas_total = 0.0
                        pecas_nesting = []

                        for item in lista_materiais:
                            c_str = str(item.get("COMP. (mm)", "-")).strip()
                            l_str = str(item.get("LARG. (mm)", "-")).strip()
                            q_str = str(item.get("QTD.", "1")).strip()
                            desc = str(item.get("DESCRIÇÃO", "Peça"))

                            if c_str not in ["-", "", "NÃO INFORMADO"] and l_str not in ["-", "", "NÃO INFORMADO"]:
                                try:
                                    c_val = float(c_str)
                                    l_val = float(l_str)
                                    q_val = float(q_str) if q_str.replace('.', '', 1).isdigit() else 1.0
                                    area_pecas_total += c_val * l_val * q_val
                                    pecas_nesting.append({"COMP": c_val, "LARG": l_val, "QTD": int(q_val), "NOME": desc})
                                except ValueError:
                                    pass

                        aproveitamento_pct = (area_pecas_total / area_chapa_unit * 100) if area_chapa_unit > 0 else 0
                        chapas_estimadas = (area_pecas_total / area_chapa_unit) if area_chapa_unit > 0 else 0

                        nesting_img_path = gerar_grafico_nesting_temp(chapa_padrao_comp, chapa_padrao_larg, pecas_nesting)

                        relatorio_aproveitamento = (
                            f"\n\n--- ANÁLISE DE APROVEITAMENTO E NESTING DE CORTE ---\n"
                            f"Dimensão Base da Matéria-Prima: {chapa_padrao_comp} x {chapa_padrao_larg} mm\n"
                            f"Área Útil por Chapa: {area_chapa_unit/1e6:.2f} m²\n"
                            f"Área Total Requerida pelas Peças: {area_pecas_total/1e6:.2f} m²\n"
                            f"Aproveitamento Teórico Estimado: {aproveitamento_pct:.2f}%\n"
                            f"Quantidade Estimada de Chapas Necessárias: {max(1.0, chapas_estimadas):.2f} unidades"
                        )

                        relatorio_completo_final = relatorio + relatorio_aproveitamento

                        st.success("✅ Análise, Planilha e Nesting gerados com sucesso!")

                        st.markdown("### 📊 Relatório Técnico Comercial")
                        st.write(relatorio_completo_final)

                        if nesting_img_path and os.path.exists(nesting_img_path):
                            st.markdown("### 🗺️ Mapa Gráfico de Corte (Nesting)")
                            st.image(nesting_img_path, use_container_width=True)

                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.metric("Aproveitamento Teórico", f"{aproveitamento_pct:.2f}%")
                        with col_m2:
                            st.metric("Chapas Estimadas", f"{max(1.0, chapas_estimadas):.2f}")

                        st.markdown("### 🧱 Planilha Real de Insumos (Formatada em Colunas)")
                        if lista_materiais:
                            df_materiais = pd.DataFrame(lista_materiais)
                            st.dataframe(df_materiais, use_container_width=True, hide_index=True)

                            excel_buffer = io.BytesIO()
                            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                                df_materiais.to_excel(writer, index=False, sheet_name='Lista_Insumos')
                                workbook = writer.book
                                worksheet = writer.sheets['Lista_Insumos']
                                
                                header_format = workbook.add_format({
                                    'bold': True,
                                    'font_color': 'white',
                                    'bg_color': '#0f172a',
                                    'border': 1,
                                    'align': 'center'
                                })
                                for col_num, value in enumerate(df_materiais.columns.values):
                                    worksheet.write(0, col_num, value, header_format)
                                    worksheet.set_column(col_num, col_num, 22)
                            excel_buffer.seek(0)

                            st.download_button(
                                label="📥 Baixar Planilha Real Formatada (.xlsx)",
                                data=excel_buffer,
                                file_name="Planilha_Insumos_Profissional.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                        else:
                            st.warning("A IA não retornou itens na lista de materiais.")

                        materiais_json_orcamento = json.dumps(lista_materiais, indent=2, ensure_ascii=False)
                        conteudo_orcamento = f"RELATÓRIO TÉCNICO DE ORÇAMENTO\n\n{relatorio_completo_final}\n\nLISTA DE MATERIAIS\n\n{materiais_json_orcamento}"

                        st.session_state.historico_projetos.append({
                            "titulo": "Orçamento Técnico Comercial",
                            "tipo": "Orçamento / Extração",
                            "resumo": str(relatorio)[:150],
                            "conteudo": conteudo_orcamento,
                            "pecas": pecas_desenho,
                            "nesting_img": nesting_img_path
                        })

                        pdf_orcamento = criar_pdf_relatorio_comercial("RELATÓRIO TÉCNICO E ORÇAMENTO", conteudo_orcamento, pecas_desenho, nesting_img_path)

                        st.download_button(
                            "📄 Baixar PDF Comercial Colorido (Apostila)",
                            data=pdf_orcamento,
                            file_name="Relatorio_Comercial_Colorido.pdf",
                            mime="application/pdf",
                            key="download_orcamento_pdf"
                        )

                    except Exception as e:
                        st.error(f"Erro ao processar documentos: {str(e)}")


# ==============================================================================
# ABA 4 — OTIMIZADOR DE CORTE (MANUAL)
# ==============================================================================
with tabs[3]:
    st.subheader("✂️ Otimizador de Corte (Manual / Linear)")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        chapa_comp = st.number_input("Comprimento da chapa / barra (mm)", min_value=1.0, value=2750.0, step=10.0)
    with col_b:
        chapa_larg = st.number_input("Largura da chapa (mm) [Defina 0 para perfil linear]", min_value=0.0, value=1850.0, step=10.0)
    with col_c:
        espessura = st.number_input("Espessura / Kerf (mm)", min_value=0.1, value=3.0, step=0.5)

    dados_corte = st.data_editor(
        pd.DataFrame([{"PEÇA": "Exemplo", "COMP. (mm)": 500, "LARG. (mm)": 300, "QTD.": 1}]),
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("📐 Calcular Aproveitamento Manual"):
        try:
            area_chapa = chapa_comp * (chapa_larg if chapa_larg > 0 else 1.0)
            area_total = 0.0
            for _, row in dados_corte.iterrows():
                l_val = float(row["LARG. (mm)"]) if chapa_larg > 0 else 1.0
                area_total += float(row["COMP. (mm)"]) * l_val * float(row["QTD."])

            aproveitamento = (area_total / area_chapa * 100) if area_chapa > 0 else 0
            unidades_teoricas = (area_total / area_chapa) if area_chapa > 0 else 0

            st.metric("Aproveitamento teórico", f"{aproveitamento:.2f}%")
            st.metric("Unidades/Chapas teóricas", f"{unidades_teoricas:.2f}")

            img_nest = gerar_grafico_nesting_temp(chapa_comp, max(chapa_larg, 100.0), [{"COMP": r["COMP. (mm)"], "LARG": r["LARG. (mm)"], "QTD": r["QTD."], "NOME": r["PEÇA"]} for _, r in dados_corte.iterrows()])
            if img_nest and os.path.exists(img_nest):
                st.image(img_nest, use_container_width=True)
                os.unlink(img_nest)
        except Exception as e:
            st.error(f"Erro no cálculo: {e}")


# ==============================================================================
# ABA 5 — VÍDEOS & NARRAÇÃO
# ==============================================================================
with tabs[4]:
    st.subheader("🎬 Vídeos & Narração Comercial")
    texto_narracao = st.text_area("Texto para narração do projeto:", placeholder="Digite aqui o resumo comercial...")
    idioma = st.selectbox("Idioma:", ["pt", "en", "es"])

    if st.button("🔊 Gerar Narração em Áudio"):
        if not texto_narracao.strip():
            st.warning("Digite um texto.")
        else:
            try:
                with st.spinner("Sintetizando áudio comercial..."):
                    audio_buffer = io.BytesIO()
                    tts = gTTS(text=texto_narracao, lang=idioma)
                    tts.write_to_fp(audio_buffer)
                    audio_buffer.seek(0)
                st.audio(audio_buffer, format="audio/mp3")
                st.download_button("⬇️ Baixar MP3", data=audio_buffer.getvalue(), file_name="narracao_comercial.mp3", mime="application/mpeg")
            except Exception as e:
                st.error(f"Erro: {str(e)}")

st.divider()
st.caption("Multi-Engine IA • Engenharia, Projetos, Extração e Orçamentos")