.PHONY: dev db-up db-down db-logs ollama-setup local-assets seed help

help:
	@echo "Comandos disponíveis no projeto:"
	@echo "  make dev           - Inicia o servidor FastAPI em modo de desenvolvimento"
	@echo "  make db-up         - Sobe o PostgreSQL com pgvector no Docker (porta 5433)"
	@echo "  make db-down       - Para os containers do Docker"
	@echo "  make db-logs       - Exibe os logs do PostgreSQL"
	@echo "  make ollama-setup  - Baixa os modelos locais configurados"
	@echo "  make local-assets  - Baixa os modelos ONNX do Silero e Piper"
	@echo "  make seed          - Insere documentos fictícios do Tribunal de Contas"

dev:
	uv run uvicorn app.main:app --reload --env-file .env --port 8000

db-up:
	docker compose up -d

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres

ollama-setup:
	ollama pull nomic-embed-text
	ollama pull llama3.2:3b

local-assets:
	mkdir -p models
	curl -fL https://raw.githubusercontent.com/snakers4/silero-vad/master/src/silero_vad/data/silero_vad.onnx -o models/silero_vad.onnx
	uv run python -m piper.download_voices pt_BR-faber-medium --download-dir models

seed:
	uv run python scripts/seed_documents.py
