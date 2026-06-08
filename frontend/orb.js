"use strict";

const API_BASE = 'http://localhost:8000';
const stageLabels = ['DRAFT', 'CONFIGURED', 'READY', 'LIVE', 'ACTIVE_VIVA', 'COMPLETED', 'ARCHIVED'];

const state = {
  sessions: [],
  selectedSessionId: null,
  latestDecision: null,
  latestOracle: null,
  latestEvents: [],
};

const $ = (id) => document.getElementById(id);

const els = {
  backendStatus: $('backend-status'),
  backendNote: $('backend-note'),
  stageStrip: $('stage-strip'),
  sessionSelect: $('session-select'),
  sessionState: $('session-state'),
  sessionCount: $('session-count'),
  admissionCount: $('admission-count'),
  gatekeeperOutput: $('gatekeeper-output'),
  oracleOutput: $('oracle-output'),
  eventFeed: $('event-feed'),
  artifactList: $('artifact-list'),
  sessionList: $('session-list'),
};

function toDateTimeLocal(value) {
  if (!value) return '';
  const date = new Date(value);
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function parseDateTimeLocal(value) {
  return value ? new Date(value).toISOString() : null;
}

function parseRubric() {
  const lines = $('rubric-criteria').value.split('\n').map((line) => line.trim()).filter(Boolean);
  const criteria = lines.map((line, index) => {
    const [name = `Criterion ${index + 1}`, score = '10', description = ''] = line.split('|').map((part) => part.trim());
    return { name, max_score: Number(score) || 10, description: description || null };
  });
  return {
    title: $('rubric-title').value.trim() || 'Default Viva Rubric',
    criteria,
  };
}

function parseTimingWindow() {
  return {
    opens_at: parseDateTimeLocal($('opens-at').value),
    closes_at: parseDateTimeLocal($('closes-at').value),
    viva_duration_minutes: Number($('duration').value) || 15,
    check_in_grace_minutes: Number($('grace').value) || 5,
  };
}

function parseConfig() {
  return {
    subject: $('subject').value.trim(),
    course: $('course').value.trim(),
    semester: $('semester').value.trim(),
    subject_code: $('subject-code').value.trim() || null,
    instructor_name: $('instructor').value.trim() || null,
    exam_coordinator: $('coordinator').value.trim() || null,
    timing_window: parseTimingWindow(),
    rubric: parseRubric(),
  };
}

function parseSubmissions() {
  return $('student-submissions').value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [roll_number = '', repository_url = '', documents = '', batch_label = ''] = line.split('|').map((part) => part.trim());
      return {
        roll_number,
        repository_url: repository_url || null,
        document_paths: documents ? documents.split(',').map((item) => item.trim()).filter(Boolean) : [],
        batch_label: batch_label || null,
      };
    });
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || data?.error || `Request failed: ${response.status}`);
  }
  return data;
}

function setBackendStatus(ok, note) {
  els.backendStatus.textContent = ok ? 'Online' : 'Offline';
  els.backendStatus.classList.toggle('ok', ok);
  els.backendNote.textContent = note;
}

function renderStageStrip(session) {
  const current = session?.state || 'DRAFT';
  const currentIndex = stageLabels.indexOf(current);
  els.stageStrip.innerHTML = stageLabels.map((label) => `
    <div class="stage ${label === current ? 'active' : ''} ${stageLabels.indexOf(label) <= currentIndex ? 'done' : ''}">
      <span>${label.replaceAll('_', ' ')}</span>
    </div>
  `).join('');
}

function renderSessions() {
  const sessions = state.sessions;
  els.sessionSelect.innerHTML = sessions.length
    ? sessions.map((session) => `<option value="${session.session_id}">${session.title} · ${session.state}</option>`).join('')
    : '<option value="">No sessions yet</option>';
  els.sessionList.innerHTML = sessions.length
    ? sessions.map((session) => `
        <button class="session-pill ${session.session_id === state.selectedSessionId ? 'selected' : ''}" data-session="${session.session_id}">
          <strong>${session.title}</strong>
          <span>${session.session_id}</span>
          <small>${session.state}</small>
        </button>
      `).join('')
    : '<p class="muted">Create a draft session to begin the lifecycle.</p>';
  document.querySelectorAll('[data-session]').forEach((button) => {
    button.addEventListener('click', () => selectSession(button.dataset.session));
  });
}

function renderCurrentSession(session) {
  renderStageStrip(session);
  els.sessionState.textContent = session?.state || '—';
  els.sessionCount.textContent = session?.assigned_students?.length ?? 0;
  els.admissionCount.textContent = session?.gatekeeper_decisions?.length ?? 0;
  if (session?.gatekeeper_decisions?.length) {
    state.latestDecision = session.gatekeeper_decisions[session.gatekeeper_decisions.length - 1];
  }
  if (session?.analysis_artifacts?.length) {
    state.latestOracle = session.analysis_artifacts[session.analysis_artifacts.length - 1];
  }
  els.gatekeeperOutput.textContent = state.latestDecision
    ? JSON.stringify(state.latestDecision, null, 2)
    : 'No admission decision recorded for this session.';
  els.oracleOutput.textContent = state.latestOracle
    ? JSON.stringify(state.latestOracle, null, 2)
    : 'ORACLE has not started yet.';
  els.artifactList.innerHTML = session?.analysis_artifacts?.length
    ? session.analysis_artifacts.slice().reverse().map((artifact) => `
        <article class="artifact-card">
          <strong>${artifact.artifact_type}</strong>
          <pre>${escapeHtml(JSON.stringify(artifact.payload, null, 2))}</pre>
        </article>
      `).join('')
    : '<p class="muted">Artifacts will appear here after ORACLE analysis starts.</p>';

  const auditEvents = session?.audit_events || [];
  state.latestEvents = auditEvents.slice().reverse();
  els.eventFeed.innerHTML = auditEvents.length
    ? auditEvents.slice().reverse().map((event) => `
        <article class="feed-item">
          <div>
            <strong>${event.event_type}</strong>
            <span>${new Date(event.timestamp).toLocaleString()}</span>
          </div>
          <small>${event.actor}</small>
        </article>
      `).join('')
    : '<p class="muted">Audit-safe events will be recorded here.</p>';
}

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

async function loadSessions(preselect = null) {
  try {
    const data = await request('/exam-sessions');
    state.sessions = data.items || [];
    const nextSelection = preselect || state.selectedSessionId || state.sessions[0]?.session_id || null;
    state.selectedSessionId = nextSelection;
    renderSessions();
    if (nextSelection) {
      await selectSession(nextSelection, { silent: true });
    } else {
      renderCurrentSession(null);
    }
    setBackendStatus(true, `${state.sessions.length} session(s) available from the exam-session API.`);
  } catch (error) {
    setBackendStatus(false, error.message);
    renderCurrentSession(null);
  }
}

async function selectSession(sessionId, options = {}) {
  if (!sessionId) return;
  state.selectedSessionId = sessionId;
  $('session-select').value = sessionId;
  const payload = await request(`/exam-sessions/${sessionId}`);
  const session = payload.session;
  renderSessions();
  renderCurrentSession(session);
  if (!options.silent) {
    setBackendStatus(true, `Loaded ${session.title} (${session.state}).`);
  }
}

async function createSession() {
  const payload = {
    admin_id: $('admin-id').value.trim(),
    title: $('session-title').value.trim(),
  };
  const data = await request('/exam-sessions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  await loadSessions(data.session.session_id);
}

async function configureSession() {
  const sessionId = state.selectedSessionId;
  if (!sessionId) throw new Error('Create or select a session first.');
  await request(`/exam-sessions/${sessionId}/configure`, {
    method: 'POST',
    body: JSON.stringify({ config: parseConfig() }),
  });
  await loadSessions(sessionId);
}

async function assignStudents() {
  const sessionId = state.selectedSessionId;
  if (!sessionId) throw new Error('Create or select a session first.');
  await request(`/exam-sessions/${sessionId}/students`, {
    method: 'POST',
    body: JSON.stringify({ submissions: parseSubmissions() }),
  });
  await loadSessions(sessionId);
}

async function markReady() {
  const sessionId = state.selectedSessionId;
  if (!sessionId) throw new Error('Create or select a session first.');
  await request(`/exam-sessions/${sessionId}/ready`, { method: 'POST', body: '{}' });
  await loadSessions(sessionId);
}

async function activateSession() {
  const sessionId = state.selectedSessionId;
  if (!sessionId) throw new Error('Create or select a session first.');
  await request(`/exam-sessions/${sessionId}/activate`, { method: 'POST', body: '{}' });
  await loadSessions(sessionId);
}

async function runGatekeeper() {
  const sessionId = state.selectedSessionId;
  if (!sessionId) throw new Error('Create or select a session first.');
  const roll_number = $('roll-number').value.trim();
  const data = await request(`/exam-sessions/${sessionId}/gatekeeper/precheck`, {
    method: 'POST',
    body: JSON.stringify({ roll_number }),
  });
  state.latestDecision = data.decision;
  renderCurrentSession(data.session);
  setBackendStatus(true, data.decision.admitted ? `Admission granted for ${data.decision.student_roll_number}.` : `Admission rejected: ${data.decision.reason}`);
}

async function startOracle() {
  const sessionId = state.selectedSessionId;
  if (!sessionId) throw new Error('Create or select a session first.');
  const roll_number = $('roll-number').value.trim();
  const data = await request(`/exam-sessions/${sessionId}/oracle/start`, {
    method: 'POST',
    body: JSON.stringify({ roll_number }),
  });
  await loadSessions(sessionId);
  setBackendStatus(true, `ORACLE analysis attached to ${data.session.title}.`);
}

function bindEvents() {
  $('refresh-sessions').addEventListener('click', () => loadSessions());
  $('create-session').addEventListener('click', async () => handleAction(createSession));
  $('configure-session').addEventListener('click', async () => handleAction(configureSession));
  $('assign-students').addEventListener('click', async () => handleAction(assignStudents));
  $('set-ready').addEventListener('click', async () => handleAction(markReady));
  $('activate-session').addEventListener('click', async () => handleAction(activateSession));
  $('gatekeeper-check').addEventListener('click', async () => handleAction(runGatekeeper));
  $('start-oracle').addEventListener('click', async () => handleAction(startOracle));
  $('session-select').addEventListener('change', (event) => selectSession(event.target.value));
}

async function handleAction(action) {
  try {
    await action();
  } catch (error) {
    setBackendStatus(false, error.message);
  }
}

function seedTimeline() {
  els.stageStrip.innerHTML = stageLabels.map((label) => `
    <div class="stage ${label === 'DRAFT' ? 'active' : ''}"><span>${label.replaceAll('_', ' ')}</span></div>
  `).join('');
}

async function boot() {
  seedTimeline();
  bindEvents();
  $('opens-at').value = toDateTimeLocal(new Date(Date.now() + 60 * 60 * 1000).toISOString());
  $('closes-at').value = toDateTimeLocal(new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString());
  await loadSessions();
}

boot();
/**
 * El Orb — Vanilla WebGL (ported from OGL React component)
 * Non-interactive: hover = 0 always, no mouse events.
 * Call: initOrb(containerElement, { hue, backgroundColor })
 * Returns: destroy() function to clean up.
 */
(function () {
  'use strict';

  // ── GLSL ──────────────────────────────────────────────────────────────
  const VERT = `
    precision highp float;
    attribute vec2 position;
    varying vec2 vUv;
    void main() {
      vUv = position * 0.5 + 0.5;
      gl_Position = vec4(position, 0.0, 1.0);
    }
  `;

  const FRAG = `
    precision highp float;

    uniform float iTime;
    uniform vec3  iResolution;
    uniform float hue;
    uniform float hover;
    uniform float rot;
    uniform float hoverIntensity;
    uniform vec3  backgroundColor;
    varying vec2  vUv;

    vec3 rgb2yiq(vec3 c){
      return vec3(
        dot(c,vec3(0.299,0.587,0.114)),
        dot(c,vec3(0.596,-0.274,-0.322)),
        dot(c,vec3(0.211,-0.523,0.312))
      );
    }
    vec3 yiq2rgb(vec3 c){
      return vec3(
        c.x+0.956*c.y+0.621*c.z,
        c.x-0.272*c.y-0.647*c.z,
        c.x-1.106*c.y+1.703*c.z
      );
    }
    vec3 adjustHue(vec3 color,float hueDeg){
      float rad=hueDeg*3.14159265/180.0;
      float ca=cos(rad),sa=sin(rad);
      vec3 yiq=rgb2yiq(color);
      yiq=vec3(yiq.x,yiq.y*ca-yiq.z*sa,yiq.y*sa+yiq.z*ca);
      return yiq2rgb(yiq);
    }

    vec3 hash33(vec3 p3){
      p3=fract(p3*vec3(0.1031,0.11369,0.13787));
      p3+=dot(p3,p3.yxz+19.19);
      return -1.0+2.0*fract(vec3(p3.x+p3.y,p3.x+p3.z,p3.y+p3.z)*p3.zyx);
    }
    float snoise3(vec3 p){
      const float K1=0.333333333,K2=0.166666667;
      vec3 i=floor(p+(p.x+p.y+p.z)*K1);
      vec3 d0=p-(i-(i.x+i.y+i.z)*K2);
      vec3 e=step(vec3(0.0),d0-d0.yzx);
      vec3 i1=e*(1.0-e.zxy);
      vec3 i2=1.0-e.zxy*(1.0-e);
      vec3 d1=d0-(i1-K2);
      vec3 d2=d0-(i2-K1);
      vec3 d3=d0-0.5;
      vec4 h=max(0.6-vec4(dot(d0,d0),dot(d1,d1),dot(d2,d2),dot(d3,d3)),0.0);
      vec4 n=h*h*h*h*vec4(
        dot(d0,hash33(i)),
        dot(d1,hash33(i+i1)),
        dot(d2,hash33(i+i2)),
        dot(d3,hash33(i+1.0))
      );
      return dot(vec4(31.316),n);
    }
    vec4 extractAlpha(vec3 c){
      float a=max(max(c.r,c.g),c.b);
      return vec4(c/max(a,1e-5),a);
    }

    const vec3 baseColor1=vec3(0.72,0.28,1.0);      /* brighter purple  */
    const vec3 baseColor2=vec3(0.32,0.82,0.98);      /* vivid cyan-blue  */
    const vec3 baseColor3=vec3(0.08,0.06,0.72);      /* deep indigo core */
    const float innerRadius=0.52;
    const float noiseScale=0.65;

    float light1(float i,float a,float d){return i/(1.0+d*a);}
    float light2(float i,float a,float d){return i/(1.0+d*d*a);}

    vec4 draw(vec2 uv){
      vec3 c1=adjustHue(baseColor1,hue);
      vec3 c2=adjustHue(baseColor2,hue);
      vec3 c3=adjustHue(baseColor3,hue);

      float ang=atan(uv.y,uv.x);
      float len=length(uv);
      float invLen=len>0.0?1.0/len:0.0;
      float bgLum=dot(backgroundColor,vec3(0.299,0.587,0.114));

      float n0=snoise3(vec3(uv*noiseScale,iTime*0.5))*0.5+0.5;
      float r0=mix(mix(innerRadius,1.0,0.4),mix(innerRadius,1.0,0.6),n0);
      float d0=distance(uv,(r0*invLen)*uv);
      float v0=light1(2.0,10.0,d0);            /* boosted from 1.0 */
      v0*=smoothstep(r0*1.05,r0,len);
      v0*=mix(smoothstep(r0*0.8,r0*0.95,len),1.0,bgLum*0.7);

      float cl=cos(ang+iTime*2.0)*0.5+0.5;
      float a2=iTime*-1.0;
      vec2 pos=vec2(cos(a2),sin(a2))*r0;
      float d=distance(uv,pos);
      float v1=light2(2.8,5.0,d)*light1(1.6,50.0,d0);  /* boosted */

      float v2=smoothstep(1.0,mix(innerRadius,1.0,n0*0.5),len);
      float v3=smoothstep(innerRadius,mix(innerRadius,1.0,0.5),len);

      vec3 colBase=mix(c1,c2,cl);
      float fade=mix(1.0,0.1,bgLum);

      vec3 dark=mix(c3,colBase,v0);
      dark=clamp((dark+v1)*v2*v3*1.5,0.0,1.0);  /* 1.5× brightness boost */

      vec3 light=clamp(mix(backgroundColor,(colBase+v1)*mix(1.0,v2*v3,fade),v0),0.0,1.0);
      return extractAlpha(mix(dark,light,bgLum));
    }

    vec4 mainImage(vec2 fragCoord){
      vec2 center=iResolution.xy*0.5;
      float size=min(iResolution.x,iResolution.y);
      vec2 uv=(fragCoord-center)/size*2.0;
      float s=sin(rot),c=cos(rot);
      uv=vec2(c*uv.x-s*uv.y,s*uv.x+c*uv.y);
      uv.x+=hover*hoverIntensity*0.1*sin(uv.y*10.0+iTime);
      uv.y+=hover*hoverIntensity*0.1*sin(uv.x*10.0+iTime);
      return draw(uv);
    }

    void main(){
      vec4 col=mainImage(vUv*iResolution.xy);
      gl_FragColor=vec4(col.rgb*col.a,col.a);
    }
  `;

  // ── HELPERS ───────────────────────────────────────────────────────────
  function hexToRgb(hex) {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    return [r, g, b];
  }

  function compileShader(gl, type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
      console.error('Shader error:', gl.getShaderInfoLog(s));
    return s;
  }

  function createProgram(gl, vert, frag) {
    const p = gl.createProgram();
    gl.attachShader(p, compileShader(gl, gl.VERTEX_SHADER, vert));
    gl.attachShader(p, compileShader(gl, gl.FRAGMENT_SHADER, frag));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS))
      console.error('Program error:', gl.getProgramInfoLog(p));
    return p;
  }

  // ── PUBLIC API ────────────────────────────────────────────────────────
  window.initOrb = function initOrb(container, opts = {}) {
    const hue   = opts.hue ?? 0;
    // Always use black background so the shader renders clean transparent edges
    const bgRgb = [0, 0, 0];

    const canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none;z-index:1;';
    container.style.position = 'relative';
    container.appendChild(canvas);

    const gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: false });
    if (!gl) { console.warn('WebGL not available'); return { destroy: () => {} }; }
    gl.clearColor(0, 0, 0, 0);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

    const prog = createProgram(gl, VERT, FRAG);
    gl.useProgram(prog);

    // Full-screen triangle
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const posLoc = gl.getAttribLocation(prog, 'position');
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    // Uniform locations
    const uTime    = gl.getUniformLocation(prog, 'iTime');
    const uRes     = gl.getUniformLocation(prog, 'iResolution');
    const uHue     = gl.getUniformLocation(prog, 'hue');
    const uHover   = gl.getUniformLocation(prog, 'hover');
    const uRot     = gl.getUniformLocation(prog, 'rot');
    const uHoverI  = gl.getUniformLocation(prog, 'hoverIntensity');
    const uBg      = gl.getUniformLocation(prog, 'backgroundColor');

    gl.uniform1f(uHue, hue);
    gl.uniform1f(uHover, 0);
    gl.uniform1f(uRot, 0);
    gl.uniform1f(uHoverI, 0);        // non-interactive: intensity = 0
    gl.uniform3fv(uBg, bgRgb);

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      const w   = container.clientWidth;
      const h   = container.clientHeight;
      canvas.width  = w * dpr;
      canvas.height = h * dpr;
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.uniform3f(uRes, canvas.width, canvas.height, canvas.width / canvas.height);
    }
    window.addEventListener('resize', resize);
    resize();

    let rafId;
    function render(t) {
      rafId = requestAnimationFrame(render);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(prog);
      gl.uniform1f(uTime, t * 0.001);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
    rafId = requestAnimationFrame(render);

    return {
      destroy() {
        cancelAnimationFrame(rafId);
        window.removeEventListener('resize', resize);
        gl.getExtension('WEBGL_lose_context')?.loseContext();
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
      }
    };
  };
})();
