import streamlit as st
from PIL import Image
import pypdfium2 as pdfium
import time
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Leitor de Partituras - Cifra Melódica",
    page_icon="🎵",
    layout="centered"
)

st.title("🎵 Leitor de Partituras & Cifra Melódica")
st.write("Anexe a imagem ou PDF da sua partitura para extrair a cifra melódica exata e o tom!")

# Carrega a chave via Secrets do Streamlit Cloud
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

# Upload do arquivo
uploaded_file = st.file_uploader(
    "Envie a partitura (PNG, JPG, JPEG ou PDF):", 
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file is not None:
    # Trata arquivo PDF
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
            with st.spinner("Lendo a partitura, claves e acidentes..."):
                client = genai.Client(api_key=api_key)
                
                prompt = """
                Analise com precisão a imagem/PDF desta partitura musical e extraia a cifra melódica completa.

                Formate a resposta rigorosamente assim:
                1. **Informações Gerais**:
                   - Título da Música:
                   - Clave e Instrumento:
                   - Tonalidade Identificada (ex: Ré Maior / Dó# e Fá# na armadura):

                2. **Cifra Melódica (Texto/Bloco de Código)**:
                   - Transcreva todas as notas da melodia principal na sequência exata em que aparecem.
                   - Use notas em português (do, re, mi, fa, sol, la, si) ou cifras (C, D, E, F, G, A, B).
                   - Marque acidentes claramente (ex: fa#, do#, sib).
                   - Destaque notas mais agudas com letras MAIÚSCULAS ou notação de oitava (ex: RÉ, MI).
                   - Organize a transcrição dividindo as frases por compasso usando a barra vertical ' | '.
                """

                # Loop de retentativa para contornar instabilidades temporárias (503)
                max_tentativas = 3
                sucesso = False

                for tentativa in range(1, max_tentativas + 1):
                    try:
                        response = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=[image_to_process, prompt]
                        )
                        st.success("Análise concluída com sucesso!")
                        st.markdown("---")
                        st.markdown(response.text)
                        sucesso = True
                        break
                    except Exception as err:
                        if ("503" in str(err) or "UNAVAILABLE" in str(err)) and tentativa < max_tentativas:
                            st.warning(f"Servidor ocupado. Tentativa {tentativa} de {max_tentativas}... Aguardando 3 segundos.")
                            time.sleep(3)
                        else:
                            st.error(f"Erro ao processar: {err}")
                            break

                if not sucesso and "response" not in locals():
                    st.error("Servidores indisponíveis no momento. Tente novamente em alguns instantes.")
