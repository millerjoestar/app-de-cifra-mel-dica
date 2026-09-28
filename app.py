import streamlit as st
from PIL import Image
import pypdfium2 as pdfium
import cv2
import numpy as np

st.set_page_config(
    page_title="Leitor de Partituras - Cifra Nativa Real",
    page_icon="🎵",
    layout="centered"
)

st.title("🎵 Leitor de Partituras & Cifra Melódica (Visão Computacional)")
st.write("Análise local via OpenCV: detecta dinamicamente a posição das notas no pentagrama sem usar APIs.")

def processar_notas_reais(img_pil):
    # Converte PIL para OpenCV
    img_array = np.array(img_pil.convert('RGB'))
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Binarização de Otsu para separar tinta preta do fundo branco
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 1. Detectar linhas horizontais (Pentagrama)
    kernel_linha = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    linhas = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_linha)
    
    # Encontrar as coordenadas Y das linhas
    posicoes_y_linhas = np.where(linhas.sum(axis=1) > 0)[0]
    
    if len(posicoes_y_linhas) < 5:
        return "Não foi possível identificar as 5 linhas do pentagrama com clareza na imagem."

    # Agrupar linhas próximas para definir o topo e a base do pentagrama
    y_min = posicoes_y_linhas[0]
    y_max = posicoes_y_linhas[-1]
    espacamento_medio = (y_max - y_min) / 4.0  # Espaço entre 2 linhas (1 grau da pauta)

    # 2. Detectar as cabeças das notas (círculos/elipses)
    kernel_nota = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    notas_img = cv2.morphologyEx(binary - linhas, cv2.MORPH_OPEN, kernel_nota)
    
    contornos, _ = cv2.findContours(notas_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrar e ordenar contornos da esquerda para a direita (X)
    notas_detectadas = []
    for c in contornos:
        x, y, w, h = cv2.boundingRect(c)
        # Filtro de tamanho para ignorar ruídos ou hastes isoladas
        if 6 <= w <= 30 and 6 <= h <= 30:
            notas_detectadas.append((x, y + h // 2))  # Guarda (X, Y centro da nota)
            
    notas_detectadas.sort(key=lambda item: item[0])  # Ordena pela sequência horizontal (tempo)

    # 3. Mapear coordenada Y para a nota musical (Clave de Sol como base)
    # Posições de referência em relação à 1ª linha de baixo (E4)
    escala = ["mi", "fa", "sol", "la", "si", "do", "re", "MI", "FA", "SOL", "LA", "SI", "RÉ"]
    
    cifra_resultado = []
    
    for x, y_nota in notas_detectadas:
        # Posição relativa em graus da pauta a partir da linha inferior
        distancia = (y_max - y_nota) / (espacamento_medio / 2.0)
        indice = int(round(distancia))
        
        if 0 <= indice < len(escala):
            cifra_resultado.append(escala[indice])

    if not cifra_resultado:
        return "Nenhuma nota identificada com clareza. Tente melhorar o contraste/resolução da imagem."

    # Organiza a exibição
    return " ".join(cifra_resultado)

uploaded_file = st.file_uploader(
    "Envie a partitura (PNG, JPG, JPEG ou PDF):", 
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        pdf = pdfium.PdfDocument(uploaded_file.read())
        page = pdf[0]
        image_to_process = page.render(scale=2).to_pil()
    else:
        image_to_process = Image.open(uploaded_file)

    st.image(image_to_process, caption="Partitura Carregada", use_container_width=True)

    if st.button("🚀 Processar Partitura (Nativo Real)", type="primary"):
        with st.spinner("Analisando pixels, linhas e cabeças de notas..."):
            resultado = processar_notas_reais(image_to_process)
            
            st.success("Análise concluída!")
            st.markdown("---")
            st.subheader("🎵 Cifra Melódica Extraída")
            st.code(resultado, language="text")
