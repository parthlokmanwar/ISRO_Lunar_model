import { useEffect, useState } from 'react';
import { Images } from 'lucide-react';

import LeftRail from './components/LeftRail';
import RightRail from './components/RightRail';
import Stage3D from './components/Stage3D';
import StageOverlay from './components/StageOverlay';
import Stepper from './components/Stepper';
import Assistant from './components/Assistant';
import Examples from './components/Examples';
import { useStore, currentScenario } from './state/useStore';
import './styles/app.css';

export default function App() {
  const loadScenarios = useStore((s) => s.loadScenarios);
  const scenario = useStore(currentScenario);
  const result = useStore((s) => s.result);
  const [showExamples, setShowExamples] = useState(false);

  useEffect(() => {
    loadScenarios();
  }, [loadScenarios]);

  return (
    <div className="app">
      <header className="head">
        <div className="head-mark" />
        <div>
          <div className="head-title">Lunar Correspondence Engine</div>
          <div className="head-sub">
            Chandrayaan-2 multi-sensor image registration &middot; SIH26166
          </div>
        </div>

        <div className="head-spacer" />

        {scenario && (
          <>
            <span className="tag">{scenario.image_a.sensor} &rarr; {scenario.image_b.sensor}</span>
            {scenario.geo?.lat_center != null && (
              <span className="tag num">
                {Math.abs(scenario.geo.lat_center).toFixed(3)}&deg;{scenario.geo.lat_center >= 0 ? 'N' : 'S'}{' '}
                {Math.abs(scenario.geo.lon_center).toFixed(3)}&deg;{scenario.geo.lon_center >= 0 ? 'E' : 'W'}
              </span>
            )}
            <span className={`tag ${scenario.provenance.toLowerCase()}`}>{scenario.provenance}</span>
          </>
        )}
        {result && <span className="tag num">{result.metrics.total_ms.toFixed(0)} ms</span>}

        <button
          className="head-examples"
          onClick={() => setShowExamples(true)}
          title="Recorded runs with figures, for checking the project without waiting on a live run"
        >
          <Images size={13} /> Examples
        </button>
      </header>

      <LeftRail />

      <main className="main">
        <div className="stage">
          <Stage3D />
          <StageOverlay />
          <Assistant />
        </div>
        <Stepper />
      </main>

      <RightRail />

      {showExamples && <Examples onClose={() => setShowExamples(false)} />}
    </div>
  );
}
