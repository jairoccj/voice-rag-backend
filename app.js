const RATE = 16000;
const statusEl = document.querySelector('#status');
const button = document.querySelector('#toggle');
const orb = document.querySelector('#orb');
const log = document.querySelector('#log');
const labels = {
  idle: 'Pronto', listening: 'Ouvindo', transcribing: 'Transcrevendo',
  thinking: 'Pensando', speaking: 'Falando', interrupted: 'Interrompido',
};
let ws, ctx, stream, node, active = false, nextPlay = 0, currentBot;
let state = 'idle', botSpeaking = false;
const sources = new Set();

function line(kind, text) {
  const el = document.createElement('div');
  el.className = `line ${kind}`;
  el.textContent = text;
  log.append(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

function stopPlayback() {
  for (const source of sources) {
    try { source.stop(); } catch {}
  }
  sources.clear();
  nextPlay = ctx?.currentTime || 0;
}

function playPCM(buffer) {
  if (!active || !ctx) return;
  botSpeaking = true;
  const pcm = new Int16Array(buffer);
  if (!pcm.length) return;
  const audio = ctx.createBuffer(1, pcm.length, RATE);
  const channel = audio.getChannelData(0);
  for (let i = 0; i < pcm.length; i++) channel[i] = pcm[i] / 32768;
  const source = ctx.createBufferSource();
  source.buffer = audio;
  source.connect(ctx.destination);
  sources.add(source);
  nextPlay = Math.max(nextPlay, ctx.currentTime + 0.025);
  source.start(nextPlay);
  nextPlay += audio.duration;
  source.onended = () => {
    sources.delete(source);
    if (sources.size === 0 && botSpeaking && active && ws?.readyState === WebSocket.OPEN) {
      botSpeaking = false;
      ws.send(JSON.stringify({ type: 'playback_done' }));
    }
  };
}

function onServerMessage(event) {
  if (typeof event.data !== 'string') {
    playPCM(event.data);
    return;
  }
  const message = JSON.parse(event.data);
  if (message.type === 'status') {
    statusEl.textContent = message.message;
  } else if (message.type === 'state') {
    state = message.state;
    if (state === 'speaking') botSpeaking = true;
    if (state === 'interrupted' || state === 'listening') botSpeaking = false;
    statusEl.textContent = labels[state] || state;
    orb.classList.toggle('speaking', state === 'speaking');
  } else if (message.type === 'audio_level') {
    if (state === 'listening') {
      statusEl.textContent = `Ouvindo · microfone ${message.rms} · VAD ${message.vad}`;
    }
  } else if (message.type === 'transcript') {
    currentBot = null;
    line('user', message.text);
  } else if (message.type === 'text') {
    if (!currentBot) currentBot = line('bot', '');
    currentBot.textContent += message.text;
  } else if (message.type === 'interrupt') {
    botSpeaking = false;
    stopPlayback();
    statusEl.textContent = 'Interrompido';
  } else if (message.type === 'error') {
    statusEl.textContent = message.message;
    stop();
  }
}

const workletSource = `
class Capture extends AudioWorkletProcessor {
  constructor() {
    super();
    this.samples = [];
    this.squareSum = 0;
    this.count = 0;
  }
  process(inputs) {
    const input = inputs[0]?.[0];
    if (!input) return true;
    const ratio = sampleRate / 16000;
    for (let i = 0; i < input.length; i += ratio) {
      const value = Math.max(-1, Math.min(1, input[Math.floor(i)]));
      this.samples.push(value < 0 ? value * 32768 : value * 32767);
      this.squareSum += value * value;
      this.count++;
      if (this.count === 1600) {
        const pcm = new Int16Array(this.samples);
        this.port.postMessage({
          pcm: pcm.buffer,
          rms: Math.sqrt(this.squareSum / this.count),
        }, [pcm.buffer]);
        this.samples = [];
        this.squareSum = 0;
        this.count = 0;
      }
    }
    return true;
  }
}
registerProcessor('capture', Capture);
`;

async function start() {
  button.disabled = true;
  statusEl.textContent = 'Solicitando acesso ao microfone…';
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: false },
    });
    ctx = new AudioContext({ sampleRate: RATE });
    await ctx.audioWorklet.addModule(URL.createObjectURL(
      new Blob([workletSource], { type: 'text/javascript' }),
    ));
    ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/voice`);
    ws.binaryType = 'arraybuffer';
    ws.onmessage = onServerMessage;
    ws.onclose = () => { if (active) stop(); };
    ws.onerror = () => { statusEl.textContent = 'Erro na conexão WebSocket'; };
    statusEl.textContent = 'Conectando ao backend…';
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });
    const mic = ctx.createMediaStreamSource(stream);
    node = new AudioWorkletNode(ctx, 'capture');
    node.port.onmessage = (event) => {
      const { pcm, rms } = event.data;
      if (ws?.readyState === WebSocket.OPEN) ws.send(pcm);
      if (state === 'listening') {
        statusEl.textContent = `Ouvindo · microfone ${rms.toFixed(4)}`;
      }
    };
    mic.connect(node);
    node.connect(ctx.destination);
    active = true;
    orb.classList.add('live');
    button.textContent = 'Encerrar conversa';
    statusEl.textContent = 'Microfone conectado · aguardando o backend';
  } catch (error) {
    statusEl.textContent = `Não foi possível iniciar: ${error.message}`;
    stop();
  } finally {
    button.disabled = false;
  }
}

function stop() {
  active = false;
  botSpeaking = false;
  stopPlayback();
  node?.disconnect();
  stream?.getTracks().forEach(track => track.stop());
  ctx?.close();
  ws?.close();
  node = stream = ctx = ws = null;
  orb.classList.remove('live', 'speaking');
  button.textContent = 'Iniciar conversa';
  button.disabled = false;
  state = 'idle';
  statusEl.textContent = 'Conversa encerrada';
}

button.onclick = () => active ? stop() : start();
