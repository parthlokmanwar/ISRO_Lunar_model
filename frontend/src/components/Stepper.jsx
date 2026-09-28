/**
 * Stage transport under the 3D view.
 *
 * Each step shows the real measured duration of that stage from the API
 * response, so the strip doubles as a profile of where the time actually went.
 * Steps are only navigable once a run exists; there is nothing to step through
 * before that.
 */
import { useEffect } from 'react';
import { ChevronLeft, ChevronRight, Play, Pause } from 'lucide-react';

import { useStore, STAGES } from '../state/useStore';

const AUTOPLAY_MS = 2600;

export default function Stepper() {
  const result = useStore((s) => s.result);
  const stageIndex = useStore((s) => s.stageIndex);
  const setStage = useStore((s) => s.setStage);
  const next = useStore((s) => s.next);
  const prev = useStore((s) => s.prev);
  const playing = useStore((s) => s.playing);
  const togglePlay = useStore((s) => s.togglePlay);

  const enabled = Boolean(result);

  // Autoplay walks forward and stops at the end rather than looping, so the
  // sequence finishes on the assessment rather than snapping back to the start
  // mid-explanation.
  useEffect(() => {
    if (!playing || !enabled) return undefined;
    if (stageIndex >= STAGES.length - 1) {
      togglePlay();
      return undefined;
    }
    const t = setTimeout(next, AUTOPLAY_MS);
    return () => clearTimeout(t);
  }, [playing, enabled, stageIndex, next, togglePlay]);

  // Keyboard transport. Ignored while typing in the assistant.
  useEffect(() => {
    const onKey = (e) => {
      if (!enabled) return;
      const tag = e.target?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); prev(); }
      else if (e.key === ' ') { e.preventDefault(); togglePlay(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [enabled, next, prev, togglePlay]);

  const msFor = (key) => result?.stages?.find((s) => s.key === key)?.ms;

  return (
    <div className="stepper">
      <div className="transport">
        <button onClick={prev} disabled={!enabled || stageIndex === 0} title="Previous stage (left arrow)">
          <ChevronLeft size={15} />
        </button>
        <button
          onClick={togglePlay}
          disabled={!enabled}
          title={playing ? 'Pause (space)' : 'Play through stages (space)'}
        >
          {playing ? <Pause size={13} /> : <Play size={13} />}
        </button>
        <button
          onClick={next}
          disabled={!enabled || stageIndex >= STAGES.length - 1}
          title="Next stage (right arrow)"
        >
          <ChevronRight size={15} />
        </button>
      </div>

      <div className="steps">
        {STAGES.map((s, i) => {
          const ms = msFor(s.key);
          return (
            <button
              key={s.key}
              className={`step${i < stageIndex ? ' done' : ''}`}
              aria-current={i === stageIndex}
              disabled={!enabled}
              onClick={() => setStage(i)}
              title={s.blurb}
            >
              <div className="step-bar"><span /></div>
              <div className="step-name">{i + 1}. {s.name}</div>
              <div className="step-ms">{ms != null ? `${ms.toFixed(0)} ms` : '—'}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
