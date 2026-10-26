# Voice RAG - Arquitetura de Agentes (Módulos)

O sistema deve ser estruturado nos seguintes agentes (módulos) independentes, orquestrados por um gerenciador central de WebSocket.

## 1. GatewayAgent (`app/core/connection_manager.py`)
- **Papel**: Mantém o WebSocket aberto.
- **Responsabilidade**: Roteia os bytes de áudio de entrada para o `VADAgent`. Gerencia o estado da conversa (Idle, Listening, Processing, Speaking). Envia eventos de interrupção (Barge-in) para o frontend se o estado mudar abruptamente.

## 2. VADAgent (`app/services/vad.py`)
- **Papel**: Os "Ouvidos".
- **Responsabilidade**: Carrega o `silero_vad.onnx`. Recebe os chunks PCM de 16kHz em tempo real. Identifica `speech_start` e `speech_end`. Mantém um buffer do áudio falado. Ao identificar `speech_end`, passa o buffer completo para o `STTAgent`.

## 3. STTAgent (`app/services/stt.py`)
- **Papel**: O "Tradutor".
- **Responsabilidade**: Usa `faster-whisper` local para transcrever o buffer de áudio em texto em poucos milissegundos. Usa `initial_prompt` para priorizar o vocabulário do contexto.

## 4. BrainAgent (`app/services/rag.py`)
- **Papel**: O "Cérebro".
- **Responsabilidade**: Recebe a transcrição. Busca contexto no PostgreSQL (`pgvector`). Consulta o Ollama (`llama3.2:3b`) enviando a pergunta e o contexto. Retorna a resposta da LLM em streaming (token por token).
- **Tratamento de Cancelamento**: Deve aceitar um `threading.Event` ou mecanismo similar para abortar a geração se o usuário interromper.

## 5. TTSAgent (`app/services/tts.py`)
- **Papel**: A "Boca".
- **Responsabilidade**: Recebe os tokens em streaming, acumula em frases curtas e gera áudio offline. Deve ser capaz de parar a geração/síntese instantaneamente se receber um sinal de aborto do `GatewayAgent`.