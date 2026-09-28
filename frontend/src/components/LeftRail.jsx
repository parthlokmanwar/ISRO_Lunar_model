/**
 * Left rail: what to run, and how to run it.
 *
 * Two sections only. A scenario library where every card states its provenance
 * up front, and the pipeline controls that actually change the result. Anything
 * that would merely decorate the panel is left out; a control that does not
 * change a number does not belong next to the numbers.
 */
import { useState } from 'react';
import { Play, Loader2, RotateCcw, ChevronDown, Sliders, Layers } from 'lucide-react';

import { useStore } from '../state/useStore';

const PROVENANCE_HELP = {
  REAL: 'Both images are unmodified Chandrayaan-2 observations of the same ground.',
  DERIVED: 'Real pixels put through a sensor or band model. The applied transform is known, so accuracy is measured against ground truth.',
  SIMULATED: 'Real pixels re-illuminated by a physical model. The applied transform is known.',
};

function Section({ icon: Icon, title, count, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="section">
      <div
        className="section-head clickable"
        onClick={() => setOpen((o) => !o)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setOpen((o) => !o)}
        aria-expanded={open}
      >
        <Icon size={12} />
        <span>{title}</span>
        {count != null && <span className="count num">{count}</span>}
        <ChevronDown
          size={12}
          style={{ marginLeft: count != null ? 6 : 'auto', transform: open ? 'none' : 'rotate(-90deg)', transition: 'transform 0.15s' }}
        />
      </div>
      {open && <div className="section-body">{children}</div>}
    </div>
  );
}

function Slider({ label, value, unit, min, max, step, onChange, hint }) {
  return (
    <div className="ctl">
      <div className="ctl-label">
        <span title={hint}>{label}</span>
        <span className="val">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </div>
  );
}

function ScenarioCard({ scenario, active, disabled, onSelect }) {
  const a = scenario.image_a;
  const b = scenario.image_b;
  const dSun =
    a.sun_elevation != null && b.sun_elevation != null
      ? Math.abs(a.sun_elevation - b.sun_elevation).toFixed(1)
      : null;

  return (
    <button
      className="scn"
      aria-current={active}
      disabled={disabled}
      onClick={() => onSelect(scenario.id)}
      title={PROVENANCE_HELP[scenario.provenance]}
    >
      <div className="scn-top">
        <span className="scn-name">{scenario.title}</span>
        <span className={`tag ${scenario.provenance.toLowerCase()}`} style={{ marginLeft: 'auto' }}>
          {scenario.provenance}
        </span>
      </div>

      <div className="scn-thumbs">
        <img src={a.thumb_url || a.url} alt={`${scenario.title} source`} loading="lazy" />
        <img src={b.thumb_url || b.url} alt={`${scenario.title} reference`} loading="lazy" />
      </div>

      <div className="scn-meta">
        <span>{a.sensor}</span>
        <span>&rarr;</span>
        <span>{b.sensor}</span>
        {a.gsd_m ? <span>{a.gsd_m} m/px</span> : null}
        {dSun ? <span>&Delta;sun {dSun}&deg;</span> : null}
        {scenario.ground_truth_homography ? <span style={{ color: 'var(--accent)' }}>ground truth</span> : null}
      </div>

      {scenario.challenge && <div className="scn-challenge">{scenario.challenge}</div>}
    </button>
  );
}

export default function LeftRail() {
  const scenarios = useStore((s) => s.scenarios);
  const scenarioId = useStore((s) => s.scenarioId);
  const select = useStore((s) => s.select);
  const settings = useStore((s) => s.settings);
  const update = useStore((s) => s.update);
  const reset = useStore((s) => s.reset);
  const run = useStore((s) => s.run);
  const running = useStore((s) => s.running);
  const catalogError = useStore((s) => s.catalogError);

  return (
    <aside className="rail left">
      {catalogError && (
        <div className="banner">
          Could not load the scenario catalogue: {catalogError}
          <br />
          <span style={{ color: 'var(--text-faint)' }}>
            Run <code>python scripts/build_scenarios.py</code>, then restart the API.
          </span>
        </div>
      )}

      <Section icon={Layers} title="Scenarios" count={scenarios.length}>
        {scenarios.map((s) => (
          <ScenarioCard
            key={s.id}
            scenario={s}
            active={s.id === scenarioId}
            disabled={running}
            onSelect={select}
          />
        ))}
        {!scenarios.length && !catalogError && (
          <div style={{ color: 'var(--text-faint)', fontSize: 11.5, padding: '6px 2px' }}>
            Loading&hellip;
          </div>
        )}
      </Section>

      <Section icon={Sliders} title="Pipeline" defaultOpen>
        <div className="ctl">
          <div className="ctl-label"><span>Detector</span></div>
          <select
            className="ctl-input"
            value={settings.detector}
            onChange={(e) => update({ detector: e.target.value })}
          >
            <option value="auto">DISK + LightGlue (learned)</option>
            <option value="sift">SIFT + FLANN (classical)</option>
          </select>
        </div>

        <div className="ctl">
          <div className="ctl-label"><span>Robust estimator</span></div>
          <select
            className="ctl-input"
            value={settings.ransac_method}
            onChange={(e) => update({ ransac_method: e.target.value })}
          >
            <option value="MAGSAC">MAGSAC++</option>
            <option value="RANSAC">RANSAC</option>
            <option value="LMEDS">Least median of squares</option>
            <option value="RHO">PROSAC (RHO)</option>
          </select>
        </div>

        <Slider
          label="Inlier threshold" unit=" px"
          value={settings.ransac_threshold} min={0.5} max={12} step={0.5}
          onChange={(v) => update({ ransac_threshold: v })}
          hint="Maximum reprojection error for a correspondence to count as an inlier."
        />
        <Slider
          label="CLAHE clip limit" unit=""
          value={settings.clahe_clip_limit} min={0.5} max={10} step={0.5}
          onChange={(v) => update({ clahe_clip_limit: v })}
          hint="Higher values equalise illumination harder, at the cost of amplifying noise."
        />
        <Slider
          label="Match confidence floor" unit=""
          value={settings.confidence_threshold} min={0} max={0.9} step={0.05}
          onChange={(v) => update({ confidence_threshold: v })}
          hint="Discard correspondences the matcher is less certain about before fitting."
        />
        <Slider
          label="Max keypoints" unit=""
          value={settings.max_keypoints} min={256} max={4096} step={256}
          onChange={(v) => update({ max_keypoints: v })}
          hint="Detector budget per image."
        />

        <label className="switch" style={{ marginBottom: 12 }}>
          <input
            type="checkbox"
            checked={settings.suppress_shadows}
            onChange={(e) => update({ suppress_shadows: e.target.checked })}
          />
          Suppress deep shadow
        </label>

        <button className="btn" onClick={run} disabled={running || !scenarioId}>
          {running ? <><Loader2 size={14} className="spin" /> Running</> : <><Play size={14} /> Run pipeline</>}
        </button>
        <button className="btn ghost" style={{ marginTop: 6 }} onClick={reset} disabled={running}>
          <RotateCcw size={13} /> Reset settings
        </button>
      </Section>
    </aside>
  );
}
