'use strict';
// ═══════════════════════════════════════════
//  El — AI Examiner  |  app.js
//  ✅ Always-on voice input (SpeechRecognition)
//  ✅ Mic auto-starts on boot, pauses when El speaks
//  ✅ Transcribed text auto-sends after speech ends
//  ✅ Camera + mic media handled in browser
//  ✅ AI calls go to /api/chat (backend — no key here)
// ═══════════════════════════════════════════

const BACKEND_URL = 'http://localhost:3333/api/chat';

// ── DOM ──────────────────────────────────────────────────────────────
const gate          = document.getElementById('gate');
const gateBtn       = document.getElementById('gate-btn');
const gateLoading   = document.getElementById('gate-loading');
const gateErr       = document.getElementById('gate-err');

const app           = document.getElementById('app');
const camVideo      = document.getElementById('cam-video');
const camAvatar     = document.getElementById('cam-avatar');
const camSpeakRing  = document.getElementById('cam-speak-ring');
const mmBars        = document.querySelectorAll('.mm-bars i');
const mmMuted       = document.getElementById('mm-muted');
const speakerBtn    = document.getElementById('speaker-btn');
const spkOn         = document.getElementById('spk-on');
const spkOff        = document.getElementById('spk-off');

const elsOrb        = document.getElementById('els-orb');
const elsState      = document.getElementById('els-state');
const elsWaves      = document.getElementById('els-waves');

const heroOrb       = document.getElementById('hero-orb');
const heroText      = document.getElementById('hero-text');
const heroSub       = document.getElementById('hero-sub');
const quickChips    = document.getElementById('quick-chips');
const hero          = document.getElementById('hero');
const msgs          = document.getElementById('msgs');
const chatScroll    = document.getElementById('chat-scroll');

const chatInput     = document.getElementById('chat-input');
const plusBtn       = document.getElementById('plus-btn');
const fileInput     = document.getElementById('file-input');
const fileChips     = document.getElementById('file-chips');
const sendBtn       = document.getElementById('send-btn');
const deniedOverlay = document.getElementById('denied-overlay');
const listenRing    = document.getElementById('listen-ring');
const listenLabel   = document.getElementById('listen-label');

// ── STATE ────────────────────────────────────────────────────────────
let stream          = null;
let audioCtx        = null;
let analyser        = null;
let vizRAF          = null;
let voiceEnabled    = true;
let isSpeaking      = false;
let pendingFiles    = [];
let conversation    = [];

// Speech Recognition
const SR            = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition     = null;
let isListening     = false;
let autoSendTimer   = null;
let srEnabled       = !!SR;   // false if browser doesn't support it

// ── UTILS ────────────────────────────────────────────────────────────
const show  = el => el && el.classList.remove('hidden');
const hide  = el => el && el.classList.add('hidden');
const sleep = ms  => new Promise(r => setTimeout(r, ms));
const now   = ()  => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

// ── GATE ─────────────────────────────────────────────────────────────
async function requestPermissionsAndBoot(launchExam = false) {
  hide(gateErr);
  document.getElementById('gate-btn').style.display = 'none';
  show(gateLoading);

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
      audio: { echoCancellation: true, noiseSuppression: true }
    });

    gate.classList.add('out');
    await sleep(450);
    gate.style.display = 'none';
    show(app);
    bootApp(launchExam);
  } catch (err) {
    document.getElementById('gate-btn').style.display = '';
    hide(gateLoading);
    handlePermErr(err);
  }
}

gateBtn.addEventListener('click', () => requestPermissionsAndBoot(true));

// ── BOOT ─────────────────────────────────────────────────────────────
function bootApp(launchExam = false) {
  camVideo.srcObject = stream;
  camVideo.play().catch(() => {});
  if (stream.getAudioTracks().length > 0) startAnalyser();
  startSession(launchExam);
}

// ── SESSION START ────────────────────────────────────────────────────
function startSession(launchExam = false) {
  if (heroText) heroText.style.display = 'none';

  if (launchExam) {
    const examMsg = "Let's start the exam. Please begin!";
    addElMsg(examMsg, true);
    elSpeak(examMsg);
    conversation.push({ role: 'model', parts: [{ text: examMsg }] });
    chatInput.value = "Let's start the exam.";
    sendMessage();
  } else {
    const h = new Date().getHours();
    const greet = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
    const opening = `${greet}! I'm El, your AI Examiner. How can I help you today?`;
    addElMsg(opening, true);
    elSpeak(opening);
    conversation.push({ role: 'model', parts: [{ text: opening }] });
  }
  setTimeout(startListening, 800);
}

// ══════════════════════════════════════════════
//  SPEECH RECOGNITION — always-on voice input
// ══════════════════════════════════════════════
function initSR() {
  if (!srEnabled) return;

  recognition = new SR();
  recognition.lang            = 'en-US';
  recognition.continuous      = false;   // restart loop gives more reliability
  recognition.interimResults  = true;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isListening = true;
    setListenUI(true);
  };

  recognition.onresult = (e) => {
    let interim = '';
    let final   = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final   += e.results[i][0].transcript;
      else                       interim += e.results[i][0].transcript;
    }

    const spoken = (final || interim).trim();
    if (spoken) {
      chatInput.value = spoken;
      autoResize();
    }

    if (final.trim()) {
      // Small pause to let user finish sentence, then auto-send
      clearTimeout(autoSendTimer);
      autoSendTimer = setTimeout(() => {
        if (chatInput.value.trim()) sendMessage();
      }, 900);
    }
  };

  recognition.onend = () => {
    isListening = false;
    setListenUI(false);
    // Restart loop unless El is speaking
    if (!isSpeaking && srEnabled) {
      setTimeout(startListening, 250);
    }
  };

  recognition.onerror = (e) => {
    isListening = false;
    setListenUI(false);
    // 'aborted' and 'no-speech' are normal — just restart
    if (e.error !== 'aborted' && e.error !== 'no-speech') {
      console.warn('[SR]', e.error);
    }
    if (!isSpeaking && srEnabled) {
      setTimeout(startListening, 400);
    }
  };
}

function startListening() {
  if (!srEnabled || isSpeaking || isListening) return;
  try {
    if (!recognition) initSR();
    recognition.start();
  } catch (_) {
    // Already started — ignore
  }
}

function stopListening() {
  if (recognition && isListening) {
    try { recognition.stop(); } catch (_) {}
    isListening = false;
    setListenUI(false);
  }
}

function setListenUI(active) {
  if (listenRing)  listenRing.classList.toggle('active', active);
  const listenDot = document.getElementById('listen-dot');
  if (listenDot)   listenDot.classList.toggle('on', active);
  if (listenLabel) listenLabel.textContent = active ? '🎙️ Listening — speak now…' : 'Speak your answer';
  chatInput.placeholder = active
    ? '🎙️ Listening — speak now…'
    : 'Write your answer…';
}

// ── MIC ANALYSER ─────────────────────────────────────────────────────
function startAnalyser() {
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const src = audioCtx.createMediaStreamSource(stream);
    analyser  = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    analyser.smoothingTimeConstant = 0.75;
    src.connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);
    function draw() {
      vizRAF = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(data);
      const avg = data.reduce((a, b) => a + b, 0) / data.length / 255;
      mmBars.forEach((bar, i) => {
        const idx = Math.floor((i / mmBars.length) * data.length);
        bar.style.height  = Math.max(4, (data[idx] / 255) * 24) + 'px';
        bar.style.opacity = 0.3 + (data[idx] / 255) * 0.7;
      });
      camSpeakRing.classList.toggle('active', avg > 0.05);
    }
    draw();
  } catch (e) { console.warn('AudioCtx', e); }
}

// ── EL SPEAKS ────────────────────────────────────────────────────────
function elSpeak(text) {
  if (!voiceEnabled) {
    // No TTS — start listening immediately
    setTimeout(startListening, 300);
    return;
  }
  window.speechSynthesis.cancel();

  const utter   = new SpeechSynthesisUtterance(text);
  utter.rate    = 0.95;
  utter.pitch   = 1.0;
  utter.volume  = 1.0;

  const voices  = window.speechSynthesis.getVoices();
  const prefs   = ['Google UK English Female','Microsoft Zira Desktop','Samantha','Karen','Moira'];
  for (const name of prefs) {
    const v = voices.find(v => v.name === name);
    if (v) { utter.voice = v; break; }
  }
  if (!utter.voice) utter.voice = voices.find(v => v.lang.startsWith('en')) || null;

  utter.onstart = () => {
    isSpeaking = true;
    stopListening();        // pause mic while El talks
    heroOrb.classList.add('speaking');
    elsOrb.classList.add('pulse');
    elsState.textContent = 'Speaking…';
    show(elsWaves);
  };

  utter.onend = utter.onerror = () => {
    isSpeaking = false;
    heroOrb.classList.remove('speaking');
    elsOrb.classList.remove('pulse');
    elsState.textContent = 'Listening for you…';
    hide(elsWaves);
    // Auto-start mic after El finishes
    setTimeout(startListening, 400);
  };

  window.speechSynthesis.speak(utter);
}

if (speechSynthesis.onvoiceschanged !== undefined)
  speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();

speakerBtn.addEventListener('click', () => {
  voiceEnabled = !voiceEnabled;
  if (!voiceEnabled) window.speechSynthesis.cancel();
  voiceEnabled ? (show(spkOn), hide(spkOff)) : (hide(spkOn), show(spkOff));
});

// ── TOGGLE CAMERA — removed, camera is always-on ────────────────────

// ── FILE UPLOAD ──────────────────────────────────────────────────────
plusBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
  Array.from(fileInput.files).forEach(f => {
    pendingFiles.push(f);
    const chip = document.createElement('div');
    chip.className = 'fc';
    chip.innerHTML = `📎 ${trunc(f.name, 10)} <button>✕</button>`;
    chip.querySelector('button').addEventListener('click', () => {
      pendingFiles = pendingFiles.filter(x => x.name !== f.name);
      chip.remove();
    });
    fileChips.appendChild(chip);
  });
  fileInput.value = '';
});
const trunc = (s, n) => s.length <= n ? s : s.slice(0, n) + '…';

// ── SEND MESSAGE ─────────────────────────────────────────────────────
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text && pendingFiles.length === 0) return;

  clearTimeout(autoSendTimer);
  stopListening();                    // pause while processing

  if (isSpeaking) window.speechSynthesis.cancel();

  // Collapse hero on first message
  if (hero && !hero.classList.contains('gone')) {
    hero.style.display = 'none';
    hero.classList.add('gone');
  }

  // User bubble
  const userEl = document.createElement('div');
  userEl.className = 'msg-user';
  if (text) userEl.textContent = text;
  pendingFiles.forEach(f => {
    const t = document.createElement('div');
    t.className = 'file-tag';
    t.textContent = `📎 ${f.name}`;
    userEl.appendChild(t);
  });
  msgs.appendChild(userEl);
  scrollBot();

  const userText = text || `[User uploaded: ${pendingFiles.map(f => f.name).join(', ')}]`;
  pendingFiles = [];
  fileChips.innerHTML = '';
  chatInput.value = '';
  autoResize();

  conversation.push({ role: 'user', parts: [{ text: userText }] });

  sendBtn.disabled = true;
  elsState.textContent = 'Thinking…';
  const typingWrap = showTyping();

  let reply = '';
  try {
    reply = await callBackend(conversation);
  } catch (e) {
    reply = "I had a little trouble connecting. Could you try again?";
    console.error('[chat]', e.message);
  }

  typingWrap.remove();
  sendBtn.disabled = false;

  addElMsg(reply, true);
  elSpeak(reply);                     // mic auto-restarts after El finishes
  conversation.push({ role: 'model', parts: [{ text: reply }] });
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ── CALL BACKEND ─────────────────────────────────────────────────────
async function callBackend(messages) {
  const res = await fetch(BACKEND_URL, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ messages })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data.reply;
}

// ── ADD EL BUBBLE ────────────────────────────────────────────────────
function addElMsg(text, animate = false) {
  const wrap  = document.createElement('div');
  wrap.className = 'msg-el';
  const av    = document.createElement('div');
  av.className = 'el-av';
  const right = document.createElement('div');
  const bbl   = document.createElement('div');
  bbl.className = 'el-bbl';
  const timeEl = document.createElement('div');
  timeEl.className = 'el-time';
  timeEl.innerHTML = `${now()} <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
  right.append(bbl, timeEl);
  wrap.append(av, right);
  msgs.appendChild(wrap);
  scrollBot();

  if (!animate) { bbl.textContent = text; return; }
  let i = 0;
  const iv = setInterval(() => {
    bbl.textContent = text.slice(0, i++);
    if (i > text.length) clearInterval(iv);
    scrollBot();
  }, 16);
}

// ── TYPING INDICATOR ─────────────────────────────────────────────────
function showTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'msg-el';
  const av  = document.createElement('div');
  av.className = 'el-av';
  const bbl = document.createElement('div');
  bbl.className = 'el-bbl';
  bbl.innerHTML = '<div class="tdots"><span></span><span></span><span></span></div>';
  wrap.append(av, bbl);
  msgs.appendChild(wrap);
  scrollBot();
  return wrap;
}

function useChip(btn) {
  chatInput.value = btn.textContent.replace(/^[^\w]+/, '').trim();
  chatInput.focus();
}

function autoResize() {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 130) + 'px';
}
chatInput.addEventListener('input', autoResize);
function scrollBot() { chatScroll.scrollTop = chatScroll.scrollHeight; }

// ── PERMISSION ERROR ─────────────────────────────────────────────────
function handlePermErr(err) {
  if (['NotAllowedError', 'PermissionDeniedError'].includes(err.name)) {
    show(deniedOverlay); return;
  }
  gateErr.textContent = `Could not access media: ${err.message}`;
  show(gateErr);
}

// ── BROWSER CHECK ────────────────────────────────────────────────────
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
  gateBtn.disabled = true;
  gateErr.textContent = 'Use Chrome, Firefox, Edge, or Safari over localhost / HTTPS.';
  show(gateErr);
}

if (!SR) {
  console.warn('SpeechRecognition not supported in this browser. Use Chrome for voice input.');
}

// ── CLEANUP ──────────────────────────────────────────────────────────
window.addEventListener('beforeunload', () => {
  window.speechSynthesis.cancel();
  stopListening();
  if (vizRAF) cancelAnimationFrame(vizRAF);
  if (audioCtx) audioCtx.close();
  if (stream) stream.getTracks().forEach(t => t.stop());
});

// ── REMOVE SPLINE LOGO ───────────────────────────────────────────────
setInterval(() => {
  document.querySelectorAll('spline-viewer').forEach(viewer => {
    if (viewer.shadowRoot) {
      const logo = viewer.shadowRoot.querySelector('#logo');
      if (logo) logo.remove();
    }
  });
}, 1000);
