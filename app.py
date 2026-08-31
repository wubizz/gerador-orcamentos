import streamlit as st
import pandas as pd
from PIL import Image
import pypdf
from google import genai

# Configuração da página no Streamlit
st.set_page_config(
    page_title="Gerador de Orçamentos Técnicos IA",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Gerador de Orçamentos Técnicos & Análise de Projetos (Gemini IA)")
st.markdown("""
Esta ferramenta analisa **PDFs, planilhas (Excel/CSV) e projetos 3D/Imagens**, calculando medidas visuais
por proporção de pixels e gerando o **orçamento técnico completo com listagens, dimensões e plano de corte**.
""")

# Barra lateral para configuração da chave API e Parâmetros
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input("Chave de API do Google Gemini:", type="password")

    st.subheader("📏 Escala / Referência para Imagens")
    scale_info = st.text_area(
        "Referência de medida para o desenho 3D/Imagem (Recomendado):",
        placeholder="Ex: A porta visível na imagem tem 2.10m de altura; ou a régua/escala indica que 100px = 1 metro."
    )

    st.info("Obtenha sua chave de API em: https://aistudio.google.com/")

# Função para leitura de PDFs
def read_pdf(file):
    reader = pypdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Função para leitura de planilhas
def read_excel_or_csv(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return df.to_string()
    except Exception as e:
        return f"Erro ao ler planilha: {str(e)}"

# Upload de Arquivos
uploaded_files = st.file_uploader(
    "Carregue os arquivos do projeto (Imagens, PDFs, Planilhas Excel/CSV):",
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
                st.text_area(f"Conteúdo ({file.name})", pdf_text[:300] + "...", height=100, disabled=True)
                contents_payload.append(f"--- CONTEÚDO DO PDF '{file.name}' ---\n{pdf_text}")
            
            elif file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel", "text/csv"]:
                sheet_text = read_excel_or_csv(file)
                st.text_area(f"Dados ({file.name})", sheet_text[:300] + "...", height=100, disabled=True)
                contents_payload.append(f"--- DADOS DA PLANILHA '{file.name}' ---\n{sheet_text}")

    # Prompt técnico estruturado
    prompt_instrucoes = f"""
    Você é um Engenheiro Orçamentista e Especialista em Computação Gráfica/Análise Dimensional.
    Análise criteriosamente todos os arquivos anexados (documentos, planilhas e imagens de projetos 3D/desenhos).

    {f"INFORMAÇÃO DE ESCALA PARA ANÁLISE DE IMAGENS: {scale_info}" if scale_info else "Para imagens sem escala explícita, faça estimativas baseadas na proporção de pixels relativa a objetos padrão (portas, pé-direito, espessura de perfis, etc)."}

    Gere um ORÇAMENTO TÉCNICO COMPLETO E DETALHADO contendo as seguintes seções estruturadas em Markdown:

    ---
    ### 1. Resumo Executivo do Projeto
    - Breve descrição do escopo com base nos documentos e imagens.

    ### 2. Análise Dimensional Visual (Visão Computacional por Pixels)
    - Para cada imagem/desenho 3D enviado:
      - Objeto de referência utilizado para calibrar a escala de pixels.
      - Medidas identificadas/calculadas (Comprimento, Largura, Altura, Área e Espessura).
      - Proporções e elementos inferidos visualmente.

    ### 3. Listagem Quantitativa de Materiais e Componentes
    Crie uma tabela completa contendo:
    | Item | Descrição do Material / Peça | Quantidade | Dimensões (Comprimento x Largura x Espessura) | Unidade | Custo Unitário Estimado (R$) | Custo Total (R$) |

    ### 4. Plano de Aproveitamento e Otimização de Cortes (Nesting / Cutting Plan)
    - Especificação do tamanho padrão da chapa/perfil comercial utilizado.
    - **Esquema de Corte:** Como organizar as peças nas barras/chapas para minimizar desperdício.
    - Percentual de aproveitamento do material e cálculo de sobra/retalho (sucata).

    ### 5. Resumo Financeiro e Cronograma Estimado
    - Subtotal de Materiais.
    - Estimativa de Mão de Obra e Processamento.
    - Margem/Contingência recomendada (%).
    - **VALOR TOTAL ESTIMADO DO ORÇAMENTO**.
    ---
    """

    st.divider()
    
    if st.button("🚀 Gerar Orçamento Técnico Completo", type="primary"):
        if not api_key:
            st.error("Por favor, insira sua chave da API do Google Gemini na barra lateral.")
        else:
            client = genai.Client(api_key=api_key)
            
            with st.spinner("Analisando imagens (pixel scaling), lendo documentos e calculando orçamento..."):
                try:
                    # Chamada atualizada com a chave/modelo correto
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[prompt_instrucoes] + contents_payload
                    )
                    
                    st.success("Orçamento Técnico Gerado com Sucesso!")
                    st.markdown(response.text)

                    st.download_button(
                        label="📄 Baixar Relatório do Orçamento (.md)",
                        data=response.text,
                        file_name="Orcamento_Tecnico_Gemini.md",
                        mime="text/markdown"
                    )

                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar com a API do Gemini: {str(e)}")