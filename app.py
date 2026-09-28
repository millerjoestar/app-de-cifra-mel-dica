import streamlit as st
from PIL import Image
import pypdfium2 as pdfium
import os
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Leitor de Partituras - Cifra Melódica",
    page_icon="🎵",
    layout="centered"
)

st.title("🎵 Leitor de Partituras & Cifra Melódica")
st.write("Anexe a imagem ou PDF da sua partitura para extrair o tom, notas e cifra melódica!")

# Barra lateral para configuração da chave de API
st.sidebar.header("⚙️ Configurações")
api_key = st.sidebar.text_input("Chave de API (Gemini/OpenAI):", type="password")

# Upload do arquivo
uploaded_file = st.file_uploader(
    "Envie a partitura (PNG, JPG, JPEG ou PDF):", 
    type=["png", "jpg", "jpeg", "pdf"]
)

image_to_process = None

if uploaded_file is not None:
    # Trata arquivo PDF (converte a primeira página para imagem)
    if uploaded_file.type == "application/pdf":
        st.info("📄 PDF detectado. Convertendo a primeira página para imagem...")
        pdf = pdfium.PdfDocument(uploaded_file.read())
        page = pdf[0]
        image_to_process = page.render(scale=2).to_pil()
    else:
        # Se for imagem direta
        image_to_process = Image.open(uploaded_file)

    # Exibe a partitura carregada
    st.image(image_to_process, caption="Partitura Carregada", use_column_width=True)

    # Botão para processar
    if st.button("🚀 Analisar Partitura e Gerar Cifra", type="primary"):
        if not api_key:
            st.error("Por favor, insira uma Chave de API na barra lateral para continuar.")
        else:
            with st.spinner("Analisando os símbolos musicais, clave e armadura de tom..."):
                try:
                    # Inicializa o cliente da API
                    client = genai.Client(api_key=api_key)
                    
                    # Prompt estruturado para a análise musical
                    prompt = """
                    Análise a imagem desta partitura musical fornecida e retorne um relatório organizado com as seguintes informações:

                    1. **Informações Gerais**:
                       - Título/Música (se visível)
                       - Clave utilizada (ex: Clave de Sol, Clave de Fá)
                       - Tom/Tonalidade identificada (ex: Dó Maior, Sol Menor)
                       - Armadura de Clave (acidentes)
                       - Fórmula de Compasso (ex: 4/4, 3/4)

                    2. **Cifra Melódica / Sequência de Notas**:
                       - Escreva a sequência exata de notas da melodia principal (use notação em português: Dó, Ré, Mi, Fá, Sol, Lá, Si ou cifras C, D, E, F, G, A, B).
                       - Organize a transcrição por compassos.
                       - Destaque o ritmo/duração básica (ex: seminimas, colcheias) se relevante.
                    """

                    # Executa a chamada do modelo multimodal
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[image_to_process, prompt]
                    )

                    st.success("Análise concluída!")
                    st.markdown("---")
                    st.subheader("🎼 Resultado da Análise Musical")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"Erro ao processar a imagem: {e}")
