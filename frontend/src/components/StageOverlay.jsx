/**
 * The 2D layer over the 3D stage: what you are looking at, and the few view
 * controls worth having. Kept sparse so it never competes with the imagery.
 */
import { Box, Square, GitCompare, Loader2 } from 'lucide-react';

import { useStore, STAGES, currentScenario } from '../state/useStore';

export default function StageOverlay() {
  const result = useStore((s) => s.result);
  const running = useStore((s) => s.running);
  const stageIndex = useStore((s) => s.stageIndex);
  const showAll = useStore((s) => s.showAll);
  const toggleShowAll = useStore((s) => s.toggleShowAll);
  const perspective = useStore((s) => s.perspective);
  const togglePerspective = useStore((s) => s.togglePerspective);
  const scenario = useStore(currentScenario);
  const run = useStore((s) => s.run);

  const stage = STAGES[stageIndex];
  const apiStage = result?.stages?.find((s) => s.key === stage.key);

  if (running) {
    return (
      <div className="stage-empty">
        <Loader2 size={22} className="spin" style={{ color: 'var(--a)' }} />
        <h2>Running the correspondence pipeline</h2>
        <p>
          Detecting features, matching descriptors and fitting a robust model on
          {' '}{scenario ? scenario.title.toLowerCase() : 'the selected scenario'}.
        </p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="stage-empty">
        <h2>{scenario ? scenario.title : 'No scenario selected'}</h2>
        <p>
          {scenario
            ? scenario.notes
            : 'Choose a scenario from the left to begin.'}
        </p>
        {scenario && (
          <button className="btn" style={{ width: 'auto', padding: '8px 18px', marginTop: 6 }} onClick={run}>
            Run pipeline
          </button>
        )}
      </div>
    );
  }

  const showMatchLegend = ['match', 'ransac'].includes(stage.key);

  return (
    <div className="stage-overlay">
      <div className="stage-topbar">
        <div className="stage-caption fade-in" key={stage.key}>
          <h3>
            {stageIndex + 1}. {stage.name}
            {result.scenario?.provenance && (
              <span className={`tag ${result.scenario.provenance.toLowerCase()}`} style={{ marginLeft: 8 }}>
                {result.scenario.provenance}
              </span>
            )}
          </h3>
          <p>{apiStage?.detail || stage.blurb}</p>
        </div>

        <div className="stage-tools">
          {showMatchLegend && (
            <button
              className="tool"
              aria-pressed={showAll}
              onClick={toggleShowAll}
              title="Also draw the correspondences the model rejected"
            >
              <GitCompare size={12} /> Rejected
            </button>
          )}
          <button
            className="tool"
            aria-pressed={perspective}
            onClick={togglePerspective}
            title={perspective ? 'Switch to a flat, face-on view' : 'Switch to the perspective view'}
          >
            {perspective ? <Box size={12} /> : <Square size={12} />}
            {perspective ? '3D' : '2D'}
          </button>
        </div>
      </div>

      <div className="stage-legend">
        <span className="swatch"><i style={{ background: 'var(--a)' }} /> A · {result.scenario?.title ? '' : ''}source</span>
        <span className="swatch"><i style={{ background: 'var(--b)' }} /> B · reference</span>
        {showMatchLegend && (
          <>
            <span className="swatch"><i style={{ background: 'linear-gradient(90deg,#5ec8c0,#e8a765)' }} /> inlier (brighter = more confident)</span>
            {showAll && <span className="swatch"><i style={{ background: 'var(--bad)' }} /> rejected</span>}
          </>
        )}
        {stage.key === 'align' && <span>drag to orbit · scroll to zoom</span>}
        {stage.key === 'analyze' && <span>height and colour = density of reliable correspondences</span>}
      </div>
    </div>
  );
}
