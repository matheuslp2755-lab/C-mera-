# Gate Watch — Assistente de notificação do portão

Monitora a câmera do portão (via RTSP) e te avisa no WhatsApp, com foto,
sempre que alguém chega — sem depender de áudio.

## Como funciona

1. O script se conecta direto no stream RTSP da câmera.
2. Compara os quadros de vídeo apenas dentro da área do portão que você
   definir (pra não disparar com carros passando na rua, árvores balançando etc).
3. Quando detecta movimento real ali, tira um print e sobe pro imgbb.com
   (hospedagem gratuita e temporária de imagem).
4. Envia uma mensagem no WhatsApp com a foto, usando a Twilio.

## 1. Descobrir a URL RTSP da câmera

No app iCSee: abra a câmera → ícone de configurações → Informações do
dispositivo / Configurações avançadas → procure "RTSP" ou "ONVIF".
O formato costuma ser:

```
rtsp://usuario:senha@IP_DA_CAMERA:554/stream1
```

Se não aparecer no app, procure o manual do fabricante da câmera (o app
iCSee é usado por várias marcas de câmera diferentes, o menu pode variar).

## 2. Preparar o dispositivo que vai rodar o script

Precisa de algo ligado 24h na mesma rede da câmera: um Raspberry Pi, um
mini PC, um PC antigo ou um NAS que rode Python.

```bash
sudo apt update && sudo apt install python3 python3-pip -y
```

## 3. Instalar as dependências

Copie esta pasta para o dispositivo e rode:

```bash
pip install -r requirements.txt
```

## 4. Criar as contas necessárias

- **imgbb**: crie uma conta grátis em https://api.imgbb.com/ e pegue sua API key.
- **Twilio**: crie uma conta grátis em https://www.twilio.com/, ative o
  "WhatsApp Sandbox" (Console → Messaging → Try it out → Send a WhatsApp message)
  e siga as instruções pra liberar seu número de WhatsApp no sandbox
  (você manda uma mensagem com um código pro número deles).
  Anote o Account SID, o Auth Token e o número do sandbox.

  > Nota: o WhatsApp Sandbox da Twilio é gratuito, mas em algumas contas
  > o número liberado expira depois de alguns dias de inatividade —
  > se parar de funcionar, é só reenviar o código de ativação de novo.
  > Para um uso permanente e mais robusto, dá pra migrar depois para um
  > número de WhatsApp Business aprovado pela Twilio (pago, bem barato).

## 5. Configurar suas credenciais

```bash
cp .env.example .env
nano .env   # preencha com seus dados reais
```

## 6. Definir a área do portão

```bash
python select_region.py
```

Uma imagem da câmera vai abrir — desenhe um retângulo ao redor da área do
portão (só ela, não o quintal inteiro) e pressione ENTER. Isso evita
notificações falsas de movimento que não é na entrada.

## 7. Rodar o assistente

```bash
python motion_watch.py
```

Deixe rodando e teste chegando perto do portão — a notificação deve
chegar no WhatsApp em poucos segundos.

## 8. Deixar rodando sempre (systemd)

Para o assistente iniciar sozinho com o dispositivo e reiniciar se cair:

```bash
sudo cp gate-watch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gate-watch
sudo systemctl start gate-watch
```

Ajuste o `WorkingDirectory` e `ExecStart` dentro do arquivo
`gate-watch.service` para o caminho real onde você colocou os arquivos.

Para ver os logs:

```bash
sudo journalctl -u gate-watch -f
```

## Ajustes finos

No arquivo `.env`:

- `MIN_AREA`: quanto maior, menos sensível (evita disparar com folhas,
  sombras, insetos passando perto da lente).
- `COOLDOWN_SECONDS`: tempo mínimo entre duas notificações seguidas, pra
  não te encher de mensagens enquanto a pessoa ainda está parada ali.

## Publicando no GitHub

O `.gitignore` já está configurado pra nunca subir seu `.env` (suas senhas)
nem o `roi.json` (específico da sua câmera). O repositório já vem com o
`git init` e o primeiro commit feitos — falta só criar o repositório
vazio no GitHub e apontar pra ele:

```bash
git remote add origin https://github.com/SEU_USUARIO/gate-watch.git
git branch -M main
git push -u origin main
```

Crie o repositório vazio antes em https://github.com/new (sem README, sem
.gitignore, sem licença — pra não dar conflito com o que já existe aqui).
