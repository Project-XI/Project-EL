import { useMemo, useRef, useState, useEffect } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  Position,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';

const BACKEND_WS_URL = import.meta.env.VITE_ORACLE_WS_URL ?? 'ws://localhost:8000/ws/analyze';
// derive HTTP API base from websocket URL (fallback)
const API_BASE = import.meta.env.VITE_API_BASE ?? BACKEND_WS_URL.replace(/^ws/, 'http').replace('/ws/analyze', '');
const DEFAULT_REPO_URL = 'https://github.com/Project-XI/Project-EL';

const STATUS_CLASS = {
  idle: 'status-idle',
  running: 'status-running',
  done: 'status-done',
  error: 'status-error',
};

const EVENT_CLASS = {
  HANDOFF: 'event-handoff',
  STATUS: 'event-status',
  RESULT: 'event-result',
  FLAG: 'event-flag',
  ERROR: 'event-error',
};

const AGENT_META = {
  gatekeeper: {
    id: 'gatekeeper',
    name: 'GATEKEEPER',
    status: 'idle',
    progress: 0,
    lastEvent: 'Awaiting validation start',
    durationMs: 0,
    position: { x: 120, y: 380 },
  },
  oracle: {
    id: 'oracle',
    name: 'ORACLE',
    status: 'idle',
    progress: 0,
    lastEvent: 'Awaiting repository analysis',
    durationMs: 0,
    position: { x: 300, y: 40 },
  },
  main: {
    id: 'main',
    name: 'MAIN VIVA',
    status: 'idle',
    progress: 0,
    lastEvent: 'Awaiting viva handoff',
    durationMs: 0,
    position: { x: 300, y: 220 },
  },
  sentinel: {
    id: 'sentinel',
    name: 'SENTINEL',
    status: 'idle',
    progress: 0,
    lastEvent: 'Awaiting oversight stream',
    durationMs: 0,
    position: { x: 520, y: 400 },
  },
};

const DEFAULT_ALERTS = [
  {
    id: 'alt-1',
    owner: 'SENTINEL',
    type: 'tone shift',
    severity: 'high',
    summary: 'Rapid tone instability during follow-up Q2.',
  },
  {
    id: 'alt-2',
    owner: 'SENTINEL',
    type: 'gaze anomaly',
    severity: 'medium',
    summary: 'Repeated gaze divergence during answer window.',
  },
  {
    id: 'alt-3',
    owner: 'GATEKEEPER',
    type: 'identity mismatch',
    severity: 'critical',
    summary: 'Voice-print variance exceeded allowed tolerance.',
  },
  {
    id: 'alt-4',
    owner: 'GATEKEEPER',
    type: 'session breach',
    severity: 'low',
    summary: 'Unexpected short disconnect recovered automatically.',
  },
];

const AGENT_SEQUENCE = ['GATEKEEPER', 'ORACLE', 'MAIN VIVA', 'SENTINEL'];
const EDGE_BY_SOURCE = {
  GATEKEEPER: 'e-gatekeeper-oracle',
  ORACLE: 'e-oracle-main',
  'MAIN VIVA': 'e-main-sentinel',
  SENTINEL: 'e-main-sentinel',
};

function normalizeKey(value) {
  return String(value ?? '')
    .toUpperCase()
    .replace(/\s+/g, '_')
    .replace(/[^A-Z0-9_]/g, '');
}

function createInitialAgentState() {
  return Object.fromEntries(
    Object.values(AGENT_META).map((agent) => [
      agent.id,
      {
        name: agent.name,
        status: agent.status,
        progress: agent.progress,
        lastEvent: agent.lastEvent,
        durationMs: agent.durationMs,
      },
    ])
  );
}

function AgentNode({ data }) {
  return (
    <div className={`agent-node ${STATUS_CLASS[data.status]}`}>
      <div className="agent-node-name">{data.name}</div>
      <div className="agent-node-status">{data.status.toUpperCase()}</div>
      <div className="agent-node-progress">
        <span>Progress</span>
        <span>{data.progress}%</span>
      </div>
      <div className="agent-node-bar">
        <div className="agent-node-bar-fill" style={{ width: `${data.progress}%` }} />
      </div>
      <div className="agent-node-last">{data.lastEvent}</div>
      <div className="agent-node-time">Last op: {data.durationMs}ms</div>
    </div>
  );
}

function buildNodes(agentState) {
  return Object.values(AGENT_META).map((agent) => ({
    id: agent.id,
    type: 'agentNode',
    position: agent.position,
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
    data: {
      name: agent.name,
      status: agentState[agent.id]?.status ?? agent.status,
      progress: agentState[agent.id]?.progress ?? 0,
      lastEvent: agentState[agent.id]?.lastEvent ?? agent.lastEvent,
      durationMs: agentState[agent.id]?.durationMs ?? agent.durationMs,
    },
  }));
}

function buildEdges(activeEdgeIds) {
  return [
    {
      id: 'e-gatekeeper-oracle',
      source: 'gatekeeper',
      target: 'oracle',
      label: 'HANDOFF',
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
      animated: activeEdgeIds.includes('e-gatekeeper-oracle'),
    },
    {
      id: 'e-oracle-main',
      source: 'oracle',
      target: 'main',
      label: 'RESULT',
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
      animated: activeEdgeIds.includes('e-oracle-main'),
    },
    {
      id: 'e-main-sentinel',
      source: 'main',
      target: 'sentinel',
      label: 'STATUS/FLAG',
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
      animated: activeEdgeIds.includes('e-main-sentinel'),
    },
  ];
}

function inferSourceAgent(message = '') {
  if (message.includes('[Gatekeeper]')) return 'GATEKEEPER';
  if (message.includes('[Oracle]')) return 'ORACLE';
  if (message.includes('[MainAgent]')) return 'MAIN VIVA';
  if (message.includes('[Sentinel]')) return 'SENTINEL';
  return 'MAIN VIVA';
}

function inferEventType(logType = 'info', message = '') {
  const text = `${logType} ${message}`.toLowerCase();
  if (text.includes('error') || text.includes('failed') || text.includes('rejected') || text.includes('timeout')) {
    return 'ERROR';
  }
  if (text.includes('flag') || text.includes('mismatch') || text.includes('contradiction') || text.includes('breach') || text.includes('risk')) {
    return 'FLAG';
  }
  if (text.includes('complete') || text.includes('verified') || text.includes('success') || text.includes('result')) {
    return 'RESULT';
  }
  if (text.includes('started') || text.includes('parsing') || text.includes('cloning') || text.includes('building') || text.includes('analyzing') || text.includes('detecting')) {
    return 'HANDOFF';
  }
  return 'STATUS';
}

function inferTargetAgent(sourceAgent, eventType, message = '') {
  if (sourceAgent === 'GATEKEEPER') return eventType === 'ERROR' || message.toLowerCase().includes('rejected') ? 'GATEKEEPER' : 'ORACLE';
  if (sourceAgent === 'ORACLE') return 'MAIN VIVA';
  if (sourceAgent === 'MAIN VIVA') return 'SENTINEL';
  if (sourceAgent === 'SENTINEL') return 'MAIN VIVA';
  return 'MAIN VIVA';
}

function inferProgress(sourceAgent, message = '', eventType = 'STATUS') {
  const text = message.toLowerCase();

  if (sourceAgent === 'GATEKEEPER') {
    if (text.includes('verified')) return { status: 'done', progress: 100 };
    if (text.includes('rejected') || eventType === 'ERROR') return { status: 'error', progress: 100 };
    if (text.includes('started')) return { status: 'running', progress: 20 };
    return { status: 'running', progress: 60 };
  }

  if (sourceAgent === 'ORACLE') {
    if (text.includes('submission intelligence complete') || text.includes('complete')) return { status: 'done', progress: 100 };
    if (text.includes('parsing')) return { status: 'running', progress: 15 };
    if (text.includes('cloning')) return { status: 'running', progress: 30 };
    if (text.includes('detecting')) return { status: 'running', progress: 45 };
    if (text.includes('building execution graph')) return { status: 'running', progress: 60 };
    if (text.includes('extracting observable')) return { status: 'running', progress: 70 };
    if (text.includes('analyzing failure')) return { status: 'running', progress: 82 };
    if (text.includes('generating viva')) return { status: 'running', progress: 92 };
    return { status: 'running', progress: 50 };
  }

  if (sourceAgent === 'MAIN VIVA') {
    if (text.includes('analysis complete') || text.includes('voice_viva.completed')) return { status: 'done', progress: 100 };
    if (text.includes('voice_viva.started')) return { status: 'running', progress: 10 };
    if (text.includes('question.playback.started')) return { status: 'running', progress: 25 };
    if (text.includes('turn.finalized')) return { status: 'running', progress: 50 };
    if (text.includes('turn.evaluated')) return { status: 'running', progress: 70 };
    if (text.includes('topic.coverage.updated')) return { status: 'running', progress: 85 };
    if (eventType === 'ERROR') return { status: 'error', progress: 100 };
    return { status: 'running', progress: 40 };
  }

  if (sourceAgent === 'SENTINEL') {
    if (eventType === 'ERROR') return { status: 'error', progress: 100 };
    if (text.includes('complete')) return { status: 'done', progress: 100 };
    if (text.includes('placeholder')) return { status: 'running', progress: 15 };
    if (text.includes('flag')) return { status: 'running', progress: 60 };
    return { status: 'running', progress: 35 };
  }

  return { status: 'running', progress: 50 };
}

function mapAgentNameToId(name) {
  const key = String(name || '').toUpperCase();
  if (key.includes('GATEKEEPER')) return 'gatekeeper';
  if (key.includes('ORACLE')) return 'oracle';
  if (key.includes('MAIN') || key.includes('VIVA')) return 'main';
  if (key.includes('SENTINEL')) return 'sentinel';
  return 'main';
}

function buildTimelineBlocks(events) {
  if (events.length === 0) {
    return AGENT_SEQUENCE.map((agent, index) => ({
      agent,
      startMs: 0,
      endMs: 0,
      label: 'Waiting',
      widthPct: 12,
      leftPct: index * 18,
    }));
  }

  const start = Math.min(...events.map((event) => event.duration_ms));
  const end = Math.max(...events.map((event) => event.duration_ms));
  const span = Math.max(end - start, 1);

  return AGENT_SEQUENCE.map((agent, index) => {
    const agentEvents = events.filter((event) => event.source_agent === agent || event.target_agent === agent);
    if (agentEvents.length === 0) {
      return {
        agent,
        startMs: start,
        endMs: start,
        label: 'Pending',
        widthPct: 12,
        leftPct: index * 18,
      };
    }

    const agentStart = Math.min(...agentEvents.map((event) => event.duration_ms));
    const agentEnd = Math.max(...agentEvents.map((event) => event.duration_ms));
    return {
      agent,
      startMs: agentStart,
      endMs: agentEnd,
      label: `${agentEvents[0].event_type} window`,
      leftPct: ((agentStart - start) / span) * 100,
      widthPct: Math.max(((agentEnd - agentStart) / span) * 100, 10),
    };
  });
}

function Timeline({ blocks, onSelectWindow }) {
  return (
    <div className="timeline-grid">
      {blocks.map((block) => (
        <div className="timeline-row" key={block.agent}>
          <div className="timeline-agent">{block.agent}</div>
          <div className="timeline-track">
            <button
              type="button"
              className="timeline-block"
              style={{ left: `${block.leftPct}%`, width: `${block.widthPct}%` }}
              onClick={() => onSelectWindow(block.agent, block.startMs, block.endMs)}
            >
              {block.label}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString([], { hour12: false });
}

function payloadPreview(payload) {
  if (!payload) return '{}';
  if (typeof payload === 'string') return payload;
  try {
    return JSON.stringify(payload, null, 2);
  } catch {
    return String(payload);
  }
}

function createAlertId(alert) {
  return `${normalizeKey(alert.owner)}_${normalizeKey(alert.type)}_${normalizeKey(alert.severity)}`;
}

function App() {
  const [repoUrl, setRepoUrl] = useState(DEFAULT_REPO_URL);
  const [backendUrl] = useState(BACKEND_WS_URL);
  const [rollNumber, setRollNumber] = useState('');
  const [connectionState, setConnectionState] = useState('idle');
  const connectionStateRef = useRef('idle');
  const [sessionId, setSessionId] = useState('idle');
  const sessionIdRef = useRef('idle');
  const [analysisData, setAnalysisData] = useState(null);
  const [pendingAlerts, setPendingAlerts] = useState([]);
  const [agentState, setAgentState] = useState(createInitialAgentState());
  const [liveEvents, setLiveEvents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('ALL');
  const [selectedSession, setSelectedSession] = useState('ALL');
  const [selectedRange, setSelectedRange] = useState(null);
  const [dismissedAlerts, setDismissedAlerts] = useState([]);
  const [highlightEdgeId, setHighlightEdgeId] = useState('e-gatekeeper-oracle');
  const [statusMessage, setStatusMessage] = useState('Connect to the backend to stream live agent data.');
  const [activeSection, setActiveSection] = useState('node-graph');
  const wsRef = useRef(null);
  const startTimeRef = useRef(0);
  const eventCounterRef = useRef(0);

  const nodes = useMemo(() => buildNodes(agentState), [agentState]);
  const edges = useMemo(() => buildEdges([highlightEdgeId]), [highlightEdgeId]);
  const sessionOptions = useMemo(() => ['ALL', ...new Set(liveEvents.map((event) => event.session_id))], [liveEvents]);
  const timelineBlocks = useMemo(() => buildTimelineBlocks(liveEvents), [liveEvents]);

  const filteredEvents = useMemo(() => {
    return liveEvents.filter((event) => {
      const byAgent =
        selectedAgent === 'ALL' ||
        event.source_agent === selectedAgent ||
        event.target_agent === selectedAgent;
      const bySession = selectedSession === 'ALL' || event.session_id === selectedSession;
      const byRange =
        !selectedRange ||
        (event.duration_ms >= selectedRange.startMs && event.duration_ms <= selectedRange.endMs);
      return byAgent && bySession && byRange;
    });
  }, [liveEvents, selectedAgent, selectedSession, selectedRange]);

  const visibleAlerts = useMemo(() => {
    const runtimeAlerts = [];

    if (analysisData?.runtime_risks?.length) {
      analysisData.runtime_risks.forEach((risk, index) => {
        runtimeAlerts.push({
          id: `risk-${index}-${normalizeKey(risk.value)}`,
          owner: 'SENTINEL',
          type: risk.value,
          severity: String(risk.severity || 'medium').toLowerCase(),
          summary: risk.evidence?.[0] || 'Runtime risk detected from analysis result.',
        });
      });
    }

    if (analysisData?.inconsistencies?.length) {
      analysisData.inconsistencies.forEach((flag, index) => {
        runtimeAlerts.push({
          id: `flag-${index}-${normalizeKey(flag.issue)}`,
          owner: 'SENTINEL',
          type: flag.issue,
          severity: String(flag.severity || 'medium').toLowerCase(),
          summary: flag.evidence?.[0] || 'Analysis inconsistency detected.',
        });
      });
    }

    if (analysisData?.gatekeeper_status === 'rejected') {
      runtimeAlerts.push({
        id: 'gatekeeper-rejected',
        owner: 'GATEKEEPER',
        type: 'identity mismatch',
        severity: 'critical',
        summary: analysisData.gatekeeper_reason || 'Submission rejected by Gatekeeper.',
      });
    }

    const merged = [...DEFAULT_ALERTS, ...pendingAlerts, ...runtimeAlerts];
    const unique = merged.filter((alert, index, array) => index === array.findIndex((candidate) => candidate.id === alert.id));
    return unique.filter((alert) => !dismissedAlerts.includes(alert.id));
  }, [analysisData, dismissedAlerts, pendingAlerts]);

  async function fetchPendingAlerts() {
    try {
      const res = await fetch(`${API_BASE}/face/pending-alerts`);
      if (!res.ok) return;
      const payload = await res.json();
      // normalize to array of alerts
      const items = Array.isArray(payload) ? payload : payload.results || [];
      const normalized = items.map((a, i) => ({
        id: a.conflict_id || a.id || `pending-${i}`,
        owner: a.owner || 'SENTINEL',
        type: a.type || a.issue || 'unknown',
        severity: (a.severity || 'medium').toLowerCase(),
        summary: a.summary || a.evidence || JSON.stringify(a).slice(0, 120),
      }));
      setPendingAlerts(normalized);
    } catch (err) {
      // ignore
    }
  }

  // fetch pending alerts when session starts
  useEffect(() => {
    if (sessionId && sessionId !== 'idle') {
      fetchPendingAlerts();
    }
  }, [sessionId]);

  function setConnection(nextState) {
    connectionStateRef.current = nextState;
    setConnectionState(nextState);
  }

  function setSession(nextSession) {
    sessionIdRef.current = nextSession;
    setSessionId(nextSession);
  }

  function closeWebSocket() {
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {
        // noop
      }
      wsRef.current = null;
    }
  }

  function resetRunState(nextSessionId) {
    setSession(nextSessionId);
    setConnection('connecting');
    setAnalysisData(null);
    setLiveEvents([]);
    setAgentState(createInitialAgentState());
    setDismissedAlerts([]);
    setSelectedAgent('ALL');
    setSelectedSession('ALL');
    setSelectedRange(null);
    setHighlightEdgeId('e-gatekeeper-oracle');
    setStatusMessage('Connecting to backend websocket...');
    startTimeRef.current = Date.now();
    eventCounterRef.current = 0;
  }

  function appendEvent(message, logType, payload, explicitSource = null) {
    const timestamp = new Date().toISOString();
    const elapsedMs = Math.max(Date.now() - startTimeRef.current, 0);
    const sourceAgent = explicitSource || inferSourceAgent(message);
    const eventType = inferEventType(logType, message);
    const targetAgent = inferTargetAgent(sourceAgent, eventType, message);

    const event = {
      event_id: `evt-${String(++eventCounterRef.current).padStart(3, '0')}`,
      timestamp,
      source_agent: sourceAgent,
      target_agent: targetAgent,
      event_type: eventType,
      session_id: sessionIdRef.current,
      payload,
      duration_ms: elapsedMs,
    };

    setLiveEvents((prev) => [...prev, event]);
    setHighlightEdgeId(EDGE_BY_SOURCE[sourceAgent] || 'e-main-sentinel');
    setStatusMessage(message);

    setAgentState((prev) => {
      const next = { ...prev };
      const progress = inferProgress(sourceAgent, message, eventType);

      const updateSource = (key) => {
        next[key] = {
          ...next[key],
          ...progress,
          lastEvent: message,
          durationMs: elapsedMs,
        };
      };

      if (sourceAgent === 'GATEKEEPER') {
        updateSource('gatekeeper');
        if (progress.status === 'done' && next.oracle.status === 'idle') {
          next.oracle = {
            ...next.oracle,
            status: 'running',
            progress: 10,
            lastEvent: 'Waiting for ORACLE analysis to begin',
            durationMs: elapsedMs,
          };
        }
      }

      if (sourceAgent === 'ORACLE') {
        updateSource('oracle');
        if (progress.status === 'done' && next.main.status === 'idle') {
          next.main = {
            ...next.main,
            status: 'running',
            progress: 10,
            lastEvent: 'Waiting for MAIN VIVA handoff',
            durationMs: elapsedMs,
          };
        }
      }

      if (sourceAgent === 'MAIN VIVA') {
        updateSource('main');
        if (progress.status === 'done' && next.sentinel.status === 'idle') {
          next.sentinel = {
            ...next.sentinel,
            status: 'running',
            progress: 15,
            lastEvent: 'Waiting for SENTINEL oversight',
            durationMs: elapsedMs,
          };
        }
      }

      if (sourceAgent === 'SENTINEL') {
        updateSource('sentinel');
      }

      return next;
    });

    return event;
  }

  function startAnalysis() {
    if (!repoUrl) {
      setStatusMessage('Enter a repository URL first.');
      return;
    }

    closeWebSocket();
    const nextSessionId = `session-${Date.now()}`;
    resetRunState(nextSessionId);

    const socket = new WebSocket(backendUrl);
    wsRef.current = socket;

    socket.onopen = () => {
      setConnection('running');
      setStatusMessage('Backend connected. Starting GATEKEEPER → ORACLE → MAIN VIVA → SENTINEL pipeline.');
      socket.send(
        JSON.stringify({
          repo_url: repoUrl,
          report_path: null,
          enable_viva: true,
          enable_debug: true,
          generate_report: false,
          // optional roll_number for Gatekeeper
          roll_number: rollNumber || undefined,
        })
      );

      appendEvent(
        '[MainAgent] Live analysis session opened.',
        'info',
        {
          repo_url: repoUrl,
          backend_url: backendUrl,
        },
        'MAIN VIVA'
      );
    };

    socket.onmessage = (rawEvent) => {
      let data;
      try {
        data = JSON.parse(rawEvent.data);
      } catch {
        return;
      }

      // If backend sends structured PlatformEvent or 'event' messages
      if (data.event_type || data.type === 'event' || data.agent_name || data.source_agent) {
        const sourceName = data.agent_name || data.source_agent || data.agent || (data.payload && data.payload.source) || null;
        const sourceAgent = sourceName ? sourceName : inferSourceAgent(String(data.message || ''));
        const eventType = data.event_type || data.type || 'event';
        const session = data.session_id || data.session || sessionIdRef.current;
        const timestamp = data.timestamp || new Date().toISOString();
        const duration_ms = data.duration_ms || data.durationMs || Math.max(Date.now() - startTimeRef.current, 0);
        const payload = data.payload || data.data || data.message || {};

        const evt = {
          event_id: data.event_id || `evt-${Date.now()}`,
          timestamp,
          source_agent: sourceAgent,
          target_agent: data.target_agent || data.to_agent || inferTargetAgent(sourceAgent, eventType, String(payload?.message || '')),
          event_type: eventType,
          session_id: session,
          payload,
          duration_ms,
        };

        setLiveEvents((prev) => [...prev, evt]);

        // update agent progress if provided in payload or if event_type suggests progress
        if ((String(eventType).toLowerCase().includes('progress')) || payload?.progress !== undefined || payload?.status) {
          const agentKey = mapAgentNameToId(evt.source_agent);
          const p = typeof payload.progress === 'number' ? payload.progress : undefined;
          const status = payload.status || undefined;
          setAgentState((prev) => {
            const next = { ...prev };
            if (agentKey && next[agentKey]) {
              next[agentKey] = {
                ...next[agentKey],
                progress: p !== undefined ? p : next[agentKey].progress,
                status: status || next[agentKey].status,
                lastEvent: typeof payload === 'string' ? payload : (payload.summary || JSON.stringify(payload).slice(0, 120)),
                durationMs: duration_ms,
              };
            }
            return next;
          });
        }

        // highlight handoff edges
        if (String(eventType).toLowerCase().includes('handoff')) {
          setHighlightEdgeId(EDGE_BY_SOURCE[evt.source_agent] || 'e-main-sentinel');
        }

        return;
      }

      // legacy log messages
      if (data.type === 'log') {
        const message = String(data.message || '');
        const logType = String(data.log_type || data.type || 'info');
        const source = inferSourceAgent(message);
        const event = appendEvent(message, logType, { message, log_type: logType }, source);

        if (event.event_type === 'ERROR') {
          setConnection('error');
        }
        if (message.toLowerCase().includes('analysis complete')) {
          setConnection('done');
        }
        return;
      }

      if (data.type === 'result') {
        const payload = data.data || {};
        setAnalysisData(payload);

        appendEvent(
          '[Oracle] Structured result received from backend.',
          'success',
          {
            project_name: payload.project_name?.value,
            backend_framework: payload.backend_framework?.value,
            architecture_pattern: payload.architecture_pattern?.value,
            viva_targets: Array.isArray(payload.implementation_viva_targets)
              ? payload.implementation_viva_targets.length
              : Array.isArray(payload.viva_intelligence_targets)
                ? payload.viva_intelligence_targets.length
                : 0,
          },
          'ORACLE'
        );

        setAgentState((prev) => ({
          gatekeeper: {
            ...prev.gatekeeper,
            status: prev.gatekeeper.status === 'error' ? 'error' : 'done',
            progress: 100,
            lastEvent: prev.gatekeeper.lastEvent,
            durationMs: prev.gatekeeper.durationMs,
          },
          oracle: {
            ...prev.oracle,
            status: 'done',
            progress: 100,
            lastEvent: payload.backend_framework?.value
              ? `Backend: ${payload.backend_framework.value}`
              : 'Submission intelligence complete',
            durationMs: prev.oracle.durationMs,
          },
          main: {
            ...prev.main,
            status: 'done',
            progress: 100,
            lastEvent: payload.viva_intelligence_targets?.length
              ? `${payload.viva_intelligence_targets.length} viva targets prepared`
              : 'Main viva completed',
            durationMs: prev.main.durationMs,
          },
          sentinel: {
            ...prev.sentinel,
            status: prev.sentinel.status === 'error' ? 'error' : 'done',
            progress: 100,
            lastEvent: payload.runtime_risks?.length
              ? `${payload.runtime_risks.length} runtime risks under review`
              : 'Oversight complete',
            durationMs: prev.sentinel.durationMs,
          },
        }));

        setHighlightEdgeId('e-main-sentinel');
        setConnection('done');
      }
    };

    socket.onerror = () => {
      setConnection('error');
      setStatusMessage('WebSocket connection failed. Make sure the backend is running on port 8000.');
      setAgentState((prev) => ({
        ...prev,
        oracle: { ...prev.oracle, status: 'error' },
      }));
    };

    socket.onclose = () => {
      wsRef.current = null;
      if (connectionStateRef.current !== 'done' && connectionStateRef.current !== 'error') {
        setConnection('idle');
      }
    };
  }

  function onTimelineSelect(agent, startMs, endMs) {
    setSelectedAgent(agent);
    setSelectedRange({ startMs, endMs });
    setHighlightEdgeId(EDGE_BY_SOURCE[agent] || 'e-main-sentinel');
    setStatusMessage(`Timeline window filtered for ${agent} (${startMs}ms → ${endMs}ms).`);
  }

  function dismissAlert(id) {
    // attempt to resolve on backend, then mark dismissed locally
    (async () => {
      try {
        await fetch(`${API_BASE}/face/resolve-alert`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ conflict_id: id, approved: false }),
        });
      } catch (err) {
        // ignore network errors; still dismiss locally
      }
      setDismissedAlerts((prev) => [...prev, id]);
    })();
  }

  function scrollToSection(id) {
    const target = document.getElementById(id);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setActiveSection(id);
    }
  }

  return (
    <div className="dashboard-shell">
      <header className="topbar">
        <div className="brand">ORACLE Backend Testing UI</div>
        <nav className="menu">
          <button type="button" className={activeSection === 'node-graph' ? 'menu-item active' : 'menu-item'} onClick={() => scrollToSection('node-graph')}>
            NODE GRAPH
          </button>
          <span className="menu-separator" />
          <button type="button" className={activeSection === 'timeline' ? 'menu-item active' : 'menu-item'} onClick={() => scrollToSection('timeline')}>
            SESSION TIMELINE
          </button>
          <span className="menu-separator" />
          <button type="button" className={activeSection === 'events' ? 'menu-item active' : 'menu-item'} onClick={() => scrollToSection('events')}>
            LIVE EVENT FEED
          </button>
          <span className="menu-separator" />
          <button type="button" className={activeSection === 'agent-progress' ? 'menu-item active' : 'menu-item'} onClick={() => scrollToSection('agent-progress')}>
            AGENT PROGRESS
          </button>
        </nav>
      </header>

      <main className="dashboard-stack">
        <section className="control-strip">
          <label className="control-field">
            <span>Repository URL</span>
            <input value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} />
          </label>
          <label className="control-field">
            <span>Roll number</span>
            <input value={rollNumber} onChange={(e) => setRollNumber(e.target.value)} placeholder="e.g. A12345" />
          </label>
          <div className="control-summary">
            <span>Backend: {backendUrl}</span>
            <span>Session: {sessionId}</span>
            <span>Status: {connectionState.toUpperCase()}</span>
          </div>
          <button type="button" className="control-button" onClick={startAnalysis}>
            Run Live Analysis
          </button>
        </section>

        <section className="panel panel-graph" id="node-graph">
          <div className="panel-header">
            <h2>1. Agent Topology Graph</h2>
            <div className="panel-meta">React Flow</div>
          </div>
          <div className="panel-body graph-body">
            <ReactFlowProvider>
              <ReactFlow nodes={nodes} edges={edges} nodeTypes={{ agentNode: AgentNode }} fitView>
                <Background color="#D4D0CA" gap={20} />
                <MiniMap zoomable pannable nodeColor="#E8E3DC" />
                <Controls />
              </ReactFlow>
            </ReactFlowProvider>
          </div>
        </section>

        <section className="panel panel-progress" id="agent-progress">
          <div className="panel-header">
            <h2>2. Agent Progress Overview</h2>
            <div className="panel-meta">Four-agent completion cards</div>
          </div>
          <div className="panel-body progress-grid">
            {Object.values(agentState).map((agent) => (
              <article key={agent.name} className={`progress-card ${STATUS_CLASS[agent.status]}`}>
                <div className="progress-card-head">
                  <strong>{agent.name}</strong>
                  <span>{agent.progress}%</span>
                </div>
                <div className="progress-card-status">{agent.status.toUpperCase()}</div>
                <div className="progress-bar-shell">
                  <div className="progress-bar-fill" style={{ width: `${agent.progress}%` }} />
                </div>
                <p>{agent.lastEvent}</p>
                <div className="progress-card-meta">Last operation: {agent.durationMs}ms</div>
              </article>
            ))}
          </div>
        </section>

        <section className="split-panels">
          <section className="panel panel-timeline" id="timeline">
            <div className="panel-header">
              <h2>3. Session Timeline Panel</h2>
              <div className="panel-meta">Gantt Style</div>
            </div>
            <div className="panel-body">
              <Timeline blocks={timelineBlocks} onSelectWindow={onTimelineSelect} />
              <p className="window-message">{statusMessage}</p>
            </div>
          </section>

          <section className="panel panel-events" id="events">
            <div className="panel-header">
              <h2>4. Live Event Feed</h2>
              <div className="panel-meta">Chronological Event Stream</div>
            </div>
            <div className="panel-body">
              <div className="filters-row">
                <label>
                  Agent
                  <select value={selectedAgent} onChange={(event) => setSelectedAgent(event.target.value)}>
                    <option value="ALL">ALL</option>
                    <option value="GATEKEEPER">GATEKEEPER</option>
                    <option value="ORACLE">ORACLE</option>
                    <option value="MAIN VIVA">MAIN VIVA</option>
                    <option value="SENTINEL">SENTINEL</option>
                  </select>
                </label>
                <label>
                  Session
                  <select value={selectedSession} onChange={(event) => setSelectedSession(event.target.value)}>
                    {sessionOptions.map((id) => (
                      <option key={id} value={id}>
                        {id}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="event-feed">
                {filteredEvents.map((event) => (
                  <article key={event.event_id} className={`event-card ${EVENT_CLASS[event.event_type] || 'event-status'}`}>
                    <div className="event-head">
                      <span>{formatTime(event.timestamp)}</span>
                      <span className="event-type">{event.event_type}</span>
                      <span className="event-session">{event.session_id}</span>
                    </div>
                    <div className="event-route">
                      {event.source_agent} → {event.target_agent}
                    </div>
                    <div className="event-schema">
                      <span>event_id: {event.event_id}</span>
                      <span>duration_ms: {event.duration_ms}</span>
                    </div>
                    <pre className="event-payload">{payloadPreview(event.payload)}</pre>
                  </article>
                ))}
                {filteredEvents.length === 0 && <p className="window-message">No events match the current filter.</p>}
              </div>
            </div>
          </section>
        </section>

        <section className="panel panel-alerts" id="alerts">
          <div className="panel-header">
            <h2>5. Alert Cards Panel</h2>
            <div className="panel-meta">SENTINEL + GATEKEEPER</div>
          </div>
          <div className="panel-body alert-grid">
            {visibleAlerts.length === 0 && <p className="window-message">No active alerts.</p>}
            {visibleAlerts.map((alert) => (
              <article key={createAlertId(alert)} className={`alert-card severity-${alert.severity}`}>
                <div className="alert-head">
                  <strong>{alert.owner}</strong>
                  <span>{alert.severity.toUpperCase()}</span>
                </div>
                <div className="alert-type">{alert.type}</div>
                <p>{alert.summary}</p>
                <button type="button" onClick={() => dismissAlert(createAlertId(alert))}>
                  Dismiss
                </button>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
