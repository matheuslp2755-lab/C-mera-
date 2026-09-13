"""
Assistente de vigilância do portão.

Monitora continuamente o stream RTSP da câmera, detecta movimento apenas
dentro da área do portão (definida em roi.json) e envia uma notificação
pelo WhatsApp com uma foto do momento, usando a API da Twilio.

Antes de rodar:
1. Preencha o arquivo .env com suas credenciais (veja .env.example).
2. Rode select_region.py uma vez para definir a área do portão (gera roi.json).
3. Instale as dependências: pip install -r requirements.txt
4. Rode: python motion_watch.py
"""

import os
import json
import time
import logging
from datetime import datetime

import cv2
import requests
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

# ---------- Configurações (vêm do arquivo .env) ----------
RTSP_URL = os.getenv("RTSP_URL")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")  # ex: whatsapp:+14155238886
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO")      # ex: whatsapp:+55XXXXXXXXXXX

MIN_AREA = int(os.getenv("MIN_AREA", "2000"))                 # área mínima do contorno para considerar movimento real
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "60"))   # tempo mínimo entre duas notificações seguidas
SNAPSHOT_DIR = "snapshots"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("gate-watch")


def load_roi():
    """Carrega a área do portão salva por select_region.py."""
    if not os.path.exists("roi.json"):
        log.error("Arquivo roi.json não encontrado. Rode 'python select_region.py' primeiro.")
        raise SystemExit(1)
    with open("roi.json") as f:
        return json.load(f)


def upload_image(path):
    """Sobe a imagem para o imgbb.com e devolve a URL pública (necessária para o Twilio)."""
    with open(path, "rb") as f:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY},
            files={"image": f},
            timeout=30,
        )
    response.raise_for_status()
    return response.json()["data"]["url"]


def send_whatsapp_notification(image_url):
    """Envia a notificação com a foto pelo WhatsApp usando a Twilio."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=TWILIO_WHATSAPP_TO,
        body="🔔 Alguém chegou no portão!",
        media_url=[image_url],
    )


def notify(frame):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    filename = os.path.join(
        SNAPSHOT_DIR, f"portao_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    )
    cv2.imwrite(filename, frame)
    log.info(f"Movimento detectado no portão. Snapshot salvo em {filename}")

    try:
        image_url = upload_image(filename)
        send_whatsapp_notification(image_url)
        log.info("Notificação enviada pelo WhatsApp com sucesso.")
    except Exception as e:
        log.error(f"Falha ao enviar notificação: {e}")


def main():
    if not RTSP_URL:
        log.error("Defina a variável RTSP_URL no arquivo .env antes de rodar.")
        return

    roi = load_roi()
    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]

    bg_subtractor = cv2.createBackgroundSubtractorMOG2(
        history=500, varThreshold=40, detectShadows=False
    )

    last_notification = 0.0

    while True:
        cap = cv2.VideoCapture(RTSP_URL)
        if not cap.isOpened():
            log.error("Não consegui conectar na câmera. Tentando de novo em 10s...")
            time.sleep(10)
            continue

        log.info("Conectado à câmera. Monitorando a área do portão...")

        while True:
            ret, frame = cap.read()
            if not ret:
                log.warning("Perdi o sinal da câmera. Reconectando...")
                break

            roi_frame = frame[y:y + h, x:x + w]
            mask = bg_subtractor.apply(roi_frame)
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            _, mask = cv2.threshold(mask, 250, 255, cv2.THRESH_BINARY)

            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            motion_detected = any(cv2.contourArea(c) > MIN_AREA for c in contours)

            now = time.time()
            if motion_detected and (now - last_notification) > COOLDOWN_SECONDS:
                last_notification = now
                notify(frame)

        cap.release()
        time.sleep(5)


if __name__ == "__main__":
    main()
