/**
 * Vyom, the analysis assistant. Typed or spoken, both drive the same path.
 *
 * Three things differ from the previous version.
 *
 * 1. The current run's real metrics are sent as context, so answers describe
 *    what is on screen. The old prompt asserted a fixed "RMSE = 0.196 px"
 *    regardless of what had been computed.
 *
 * 2. Commands match whole words against an explicit list, and only for short
 *    utterances. Previously any message containing "match" switched the view, so
 *    "how does matching work?" silently changed the display instead of answering.
 *
 * 3. Speech is opt-in and stays off until asked for. Voice replies fire only for
 *    input that arrived by voice, or when the speaker is switched on, so typing
 *    does not make the machine talk during a presentation.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { Sparkles, X, Send, Mic, MicOff, Volume2, VolumeX, Square } from 'lucide-react';

import { api } from '../lib/api';
import { useStore, STAGES } from '../state/useStore';

const GREETING = {
  role: 'assistant',
  content:
    'Ask about the current run — accuracy, inlier ratio, why a scenario is hard, ' +
    'what a setting changes.\n\nVoice or typed commands: `run`, `next`, `back`, ' +
    '`play`, `stop`.',
};

/** Whole-word commands only. A question that merely mentions a word is a question. */
const COMMANDS = [
  { words: ['run', 'execute', 'go'], reply: 'Running the pipeline.', act: (s) => s.run() },
  { words: ['next', 'forward'], reply: 'Next stage.', act: (s) => s.next() },
  { words: ['back', 'previous'], reply: 'Previous stage.', act: (s) => s.prev() },
  { words: ['play'], reply: 'Playing through the stages.', act: (s) => { if (!s.playing) s.togglePlay(); } },
  { words: ['stop', 'pause', 'halt'], reply: 'Paused.', act: (s) => { if (s.playing) s.togglePlay(); } },
];

function asCommand(text) {
  const t = text.trim().toLowerCase().replace(/[.!?]+$/, '');
  if (t.split(/\s+/).length > 3) return null;
  return COMMANDS.find((c) => c.words.some((w) => new RegExp(`\\b${w}\\b`).test(t))) || null;
}

/** Strip markdown so the speech output does not read out asterisks and backticks. */
function forSpeech(text) {
  return text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/[*_`#>]/g, '')
    .replace(/\[(.*?)\]\(.*?\)/g, '$1')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 600);
}

export default function Assistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [speechOn, setSpeechOn] = useState(false);
  const [voiceError, setVoiceError] = useState('');

  const endRef = useRef(null);
  const audioRef = useRef(null);
  const recogRef = useRef(null);

  const result = useStore((s) => s.result);
  const stageIndex = useStore((s) => s.stageIndex);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open]);

  /* -- speech out -------------------------------------------------------- */
  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      if (audioRef.current.src?.startsWith('blob:')) URL.revokeObjectURL(audioRef.current.src);
      audioRef.current = null;
    }
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }, []);

  // Never leave audio playing after the panel unmounts.
  useEffect(() => stopSpeaking, [stopSpeaking]);

  const speak = useCallback(async (text) => {
    const clean = forSpeech(text);
    if (!clean) return;
    stopSpeaking();
    setSpeaking(true);
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: clean }),
      });
      if (res.ok) {
        const url = URL.createObjectURL(await res.blob());
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => { URL.revokeObjectURL(url); setSpeaking(false); };
        audio.onerror = () => { URL.revokeObjectURL(url); setSpeaking(false); };
        await audio.play();
        return;
      }
    } catch {
      /* fall through to the browser's own voice */
    }
    // No ElevenLabs key, or the call failed: the browser can still speak.
    if (window.speechSynthesis) {
      const u = new SpeechSynthesisUtterance(clean);
      u.rate = 1.02;
      u.onend = () => setSpeaking(false);
      u.onerror = () => setSpeaking(false);
      window.speechSynthesis.speak(u);
    } else {
      setSpeaking(false);
    }
  }, [stopSpeaking]);

  /* -- the one path both typing and speech go through -------------------- */
  const send = useCallback(async (text, { spoken = false } = {}) => {
    if (!text.trim() || busy) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', content: text }]);
    const voiceBack = spoken || speechOn;

    const cmd = asCommand(text);
    if (cmd) {
      cmd.act(useStore.getState());
      setMessages((m) => [...m, { role: 'assistant', content: cmd.reply }]);
      if (voiceBack) speak(cmd.reply);
      return;
    }

    const state = useStore.getState();
    const run = state.result;
    const context = run
      ? {
          scenario: run.scenario?.title,
          provenance: run.scenario?.provenance,
          challenge: run.scenario?.challenge,
          current_stage: STAGES[state.stageIndex]?.name,
          metrics: run.metrics,
          ground_truth_error: run.ground_truth_error,
          homography_decomposed: run.homography_decomposed,
          settings: run.settings,
        }
      : null;

    setBusy(true);
    try {
      const res = await api.chat(
        [...messages.slice(-6), { role: 'user', content: text }].map((m) => ({
          role: m.role,
          content: m.content,
        })),
        context,
      );
      setMessages((m) => [...m, { role: 'assistant', content: res.reply }]);
      if (voiceBack) speak(res.reply);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: `Could not reach the assistant service. ${e.message}` },
      ]);
    } finally {
      setBusy(false);
    }
  }, [busy, messages, speechOn, speak]);

  /* -- speech in --------------------------------------------------------- */
  const toggleListening = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setVoiceError('Speech input needs Chrome, Edge or Safari. Typing works everywhere.');
      return;
    }
    if (listening) {
      recogRef.current?.stop();
      return;
    }
    setVoiceError('');
    stopSpeaking();

    const r = new SR();
    r.lang = 'en-IN';
    r.continuous = false;
    r.interimResults = false;
    r.maxAlternatives = 1;
    r.onstart = () => setListening(true);
    r.onend = () => setListening(false);
    r.onerror = (e) => {
      setListening(false);
      if (e.error === 'not-allowed') setVoiceError('Microphone permission denied.');
      else if (e.error === 'no-speech') setVoiceError('Did not catch that.');
    };
    r.onresult = (e) => {
      const said = e.results?.[0]?.[0]?.transcript;
      // A spoken question gets a spoken answer, whether or not the speaker is on.
      if (said) send(said, { spoken: true });
    };
    recogRef.current = r;
    r.start();
  }, [listening, send, stopSpeaking]);

  if (!open) {
    return (
      <button className="asst-fab" onClick={() => setOpen(true)} title="Open the analysis assistant">
        <Sparkles size={17} />
      </button>
    );
  }

  return (
    <div className="asst">
      <div className="asst-head">
        <Sparkles size={13} style={{ color: 'var(--a)' }} />
        <span>Vyom</span>
        <span style={{ marginLeft: 8, color: 'var(--text-faint)', fontSize: 10.5 }}>
          {result ? 'run in context' : 'no run yet'}
        </span>

        <button
          onClick={() => { if (speaking) stopSpeaking(); setSpeechOn((v) => !v); }}
          title={speechOn ? 'Speak replies: on' : 'Speak replies: off'}
          aria-pressed={speechOn}
          style={{
            marginLeft: 'auto', background: 'none', border: 'none', padding: 0,
            color: speechOn ? 'var(--a)' : 'var(--text-faint)',
          }}
        >
          {speechOn ? <Volume2 size={14} /> : <VolumeX size={14} />}
        </button>
        <button
          onClick={() => { stopSpeaking(); recogRef.current?.stop(); setOpen(false); }}
          style={{ background: 'none', border: 'none', color: 'var(--text-faint)', padding: 0 }}
          title="Close"
        >
          <X size={14} />
        </button>
      </div>

      <div className="asst-log">
        {messages.map((m, i) => (
          <div className={`msg ${m.role}`} key={i}>
            <ReactMarkdown>{m.content}</ReactMarkdown>
          </div>
        ))}
        {busy && (
          <div className="msg assistant" style={{ color: 'var(--text-faint)', fontStyle: 'italic' }}>
            Thinking…
          </div>
        )}
        {listening && (
          <div className="msg assistant" style={{ color: 'var(--a)', fontStyle: 'italic' }}>
            Listening…
          </div>
        )}
        {voiceError && (
          <div className="msg assistant" style={{ color: 'var(--warn)' }}>{voiceError}</div>
        )}
        <div ref={endRef} />
      </div>

      {/* A real form, so Enter submits the way it does everywhere else and the
          browser handles the key event rather than a hand-rolled listener. */}
      <form
        className="asst-input"
        onSubmit={(e) => { e.preventDefault(); send(input); }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={listening ? 'Listening…' : 'Ask, or say “run”…'}
          disabled={listening}
          autoComplete="off"
        />
        <button
          type="button"
          onClick={speaking ? stopSpeaking : toggleListening}
          title={speaking ? 'Stop speaking' : listening ? 'Stop listening' : 'Speak a question or command'}
          aria-pressed={listening}
          style={listening
            ? { background: 'var(--bad)', borderColor: 'var(--bad)', color: '#fff' }
            : speaking
              ? { color: 'var(--a)', borderColor: 'var(--a)' }
              : undefined}
        >
          {speaking ? <Square size={12} /> : listening ? <MicOff size={13} /> : <Mic size={13} />}
        </button>
        <button type="submit" title="Send" disabled={listening}>
          <Send size={13} />
        </button>
      </form>
    </div>
  );
}
