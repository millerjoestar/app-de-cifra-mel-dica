import streamlit as st
from PIL import Image
import pypdfium2 as pdfium
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Leitor de Partituras - Cifra Melódica",
    page_icon="🎵",
    layout="centered"
)

st.title("🎵 Leitor de Partituras & Cifra Melódica")
st.write("Anexe a imagem ou PDF da sua partitura para extrair a cifra melódica e o tom!")

# Obtém a chave dos Secrets do Streamlit Cloud
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

# Upload do arquivo
uploaded_file = st.file_uploader(
    "Envie a partitura (PNG, JPG, JPEG ou PDF):", 
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        st.info("📄 PDF detectado. Convertendo a primeira página para imagem...")
        pdf = pdfium.PdfDocument(uploaded_file.read())
        page = pdf[0]
        image_to_process = page.render(scale=2).to_pil()
    else:
        image_to_process = Image.open(uploaded_file)

    st.image(image_to_process, caption="Partitura Carregada", use_container_width=True)

    if st.button("🚀 Extrair Cifra Melódica", type="primary"):
        if not api_key:
            st.error("Chave de API não configurada nos Secrets do Streamlit Cloud.")
        else:
            with st.spinner("Analisando pauta, clave e notas..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    prompt = """
                    Analise com precisão a imagem desta partitura musical e extraia a cifra melódica completa.

                    Formate a resposta assim:
                    1. **Informações Gerais**:
                       - Título da Música:
                       - Clave / Armadura de Clave / Tom:

                    2. **Cifra Melódica**:
                       - Transcreva a sequência exata das notas (ex: fa# sol la fa# RÉ...).
                       - Use letras maiúsculas para notas agudas (oitava superior).
                       - Organize separando os compassos por barra ' | '.
                    """

                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=[image_to_process, prompt]
                    )

                    st.success("Análise concluída!")
                    st.markdown("---")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
