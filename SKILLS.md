# Habilidades e Regras Técnicas para o Código

## Skill 1: Áudio Contínuo (Frontend)
- **Não use** `MediaRecorder` tradicional que só envia no `onstop`.
- **Use** Web Audio API (`AudioContext` e `ScriptProcessorNode` ou `AudioWorkletNode`) para capturar o áudio do microfone em amostras de 16-bit PCM, 16kHz, Mono, e enviar pelo WebSocket a cada 100ms.
- **Frontend Interrompível**: O front deve manter uma fila de reprodução (Buffer Source). Se o WebSocket receber `{"type": "interrupt"}`, o front deve executar `source.stop()` no áudio atual e limpar a fila.

## Skill 2: Silero VAD (Backend)
- Use a biblioteca `onnxruntime` para carregar o modelo Silero VAD.
- O backend acumula os bytes do WebSocket em um buffer de frames. O VAD avalia janelas de 30ms (512 amostras a 16kHz).
- Threshold sugerido: `0.5`. Silêncio necessário para `turn_end`: `700ms`.

## Skill 3: Barge-in (A Arte da Interrupção)
- A máquina de estados no backend deve ter uma flag `is_bot_speaking = True`.
- Se o VAD acusar `speech_start` enquanto `is_bot_speaking == True`:
  1. O backend seta um `cancellation_token` (variável global ou por conexão).
  2. Dispara o evento de interrupção pro frontend calar a boca.
  3. Aborta os loops assíncronos atuais do Ollama e do TTS.
  4. Limpa o buffer de áudio do usuário e começa a ouvir a nova fala a partir desse ponto.

## Skill 4: Contornando Limitações do Windows
- O Python 3.14 no Windows tem problemas para compilar bibliotecas C++ (`av`, `webrtcvad`).
- **NÃO instale** a biblioteca `av` se possível, ou crie um monkeypatch explícito para `av.open` caso o `faster-whisper` exija.
- Para salvar/ler áudio em memória, use a biblioteca nativa `wave` e `io.BytesIO`. Não use bibliotecas que requeiram binários externos complexos (exceto o Ollama que roda como serviço externo via HTTP).