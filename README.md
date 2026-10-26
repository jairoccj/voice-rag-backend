# Voice RAG

Assistente de voz local em português. O navegador envia áudio contínuo por WebSocket; o backend detecta fala com Silero, transcreve com faster-whisper, busca documentos no PostgreSQL/pgvector, gera resposta com Ollama e sintetiza áudio com Piper. Os modelos e dados são processados localmente depois de baixados.

## Requisitos e instalação

Windows 11 e PowerShell. Instale Git, `uv`, Docker Desktop e Ollama. O Python 3.13 será instalado pelo `uv`.

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
winget install --id Docker.DockerDesktop -e
irm https://ollama.com/install.ps1 | iex
```

Abra o Docker Desktop e um novo PowerShell. É necessária conexão à internet na primeira instalação para baixar dependências e modelos.

## Instalação

Abra o PowerShell na pasta onde deseja instalar o projeto:

```powershell
git clone https://github.com/jairoccj/voice-rag-backend.git
cd voice-rag-backend

Copy-Item .env.example .env
uv python install 3.13
uv sync --python 3.13
```

Com Docker Desktop aberto e Ollama em execução, baixe os modelos Ollama:

```powershell
ollama pull llama3.2:3b
ollama pull nomic-embed-text
docker compose up -d
```

Baixe os modelos Silero e Piper:

```powershell
New-Item -ItemType Directory -Force models | Out-Null
Invoke-WebRequest `
  "https://raw.githubusercontent.com/snakers4/silero-vad/master/src/silero_vad/data/silero_vad.onnx" `
  -OutFile "models/silero_vad.onnx"
uv run python -m piper.download_voices pt_BR-faber-medium --download-dir models
```

O modelo faster-whisper `base` é baixado automaticamente na primeira conexão de voz. Para pré-carregá-lo, basta iniciar o servidor e abrir a conversa uma vez.

## Base de conhecimento de demonstração

O seed adiciona documentos fictícios sobre o Tribunal de Contas. Para adicionar documentos, edite `documentos_teste` em `scripts/seed_documents.py` e rode:

```powershell
uv run python scripts/seed_documents.py
```

O script pode ser executado novamente sem duplicar textos que já existem.

## Executar

```powershell
uv run uvicorn app.main:app --reload --env-file .env --port 8000
```

Abra <http://localhost:8000>, permita o acesso ao microfone e inicie a conversa. O endpoint de verificação é <http://localhost:8000/health>.

## Configuração

Os valores padrão estão em `.env.example`. O PostgreSQL do Compose usa a porta `5433`; os nomes do banco, usuário e senha devem corresponder entre `DATABASE_URL` e as variáveis `POSTGRES_*`.

## Comandos úteis

```powershell
docker compose up -d       # iniciar PostgreSQL/pgvector
docker compose down        # parar PostgreSQL/pgvector
ollama list                # conferir modelos Ollama instalados
```

O Makefile também oferece `make dev`, `make db-up`, `make db-down`, `make ollama-setup`, `make local-assets` e `make seed` em ambientes com Make e shell compatíveis.
