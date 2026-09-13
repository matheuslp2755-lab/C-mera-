"""
Ferramenta para selecionar visualmente a área do portão na imagem da câmera.

Rode este script UMA VEZ (ou sempre que a câmera mudar de posição) para gerar
o arquivo roi.json, usado pelo motion_watch.py para saber onde procurar movimento.
"""

import os
import json
import cv2
from dotenv import load_dotenv

load_dotenv()

RTSP_URL = os.getenv("RTSP_URL")


def main():
    if not RTSP_URL:
        print("Defina a variável RTSP_URL no arquivo .env antes de rodar este script.")
        return

    print(f"Conectando na câmera: {RTSP_URL}")
    cap = cv2.VideoCapture(RTSP_URL)

    if not cap.isOpened():
        print("Não consegui abrir o stream RTSP. Confira a URL, usuário e senha.")
        return

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Não consegui capturar um quadro da câmera.")
        return

    print("Desenhe um retângulo ao redor da área do portão e pressione ENTER ou ESPAÇO.")
    print("Pressione 'c' para cancelar sem salvar.")

    roi = cv2.selectROI("Selecione a área do portão", frame, showCrosshair=True)
    cv2.destroyAllWindows()

    x, y, w, h = roi
    if w == 0 or h == 0:
        print("Nenhuma área selecionada. Nada foi salvo.")
        return

    with open("roi.json", "w") as f:
        json.dump({"x": int(x), "y": int(y), "w": int(w), "h": int(h)}, f)

    print(f"Área salva em roi.json: x={x}, y={y}, w={w}, h={h}")


if __name__ == "__main__":
    main()
