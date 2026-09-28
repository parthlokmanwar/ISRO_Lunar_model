/**
 * Right rail: what the pipeline just did, and how much to trust it.
 *
 * The ordering is deliberate. Accuracy first, then the evidence behind it, then
 * the transform, then coverage. Every value is either present because the run
 * produced it or absent; there are no placeholder numbers, so an empty panel
 * means nothing has been run rather than "the demo is fine".
 */
import { Download, AlertTriangle, CheckCircle2, Target, Crosshair, Grid3x3, Clock } from 'lucide-react';

import { api } from '../lib/api';
import { useStore } from '../state/useStore';

function Metric({ label, value, unit, sub, tone, bar, badge }) {
  return (
    <div className="metric">
      <div className="metric-label">
        <span>{label}</span>
        {badge}
      </div>
      <div className="metric-value" style={tone ? { color: `var(--${tone})` } : undefined}>
        {value}
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
      {sub && <div className="metric-sub">{sub}</div>}
      {bar != null && (
        <div className="bar">
          <span className={tone} style={{ width: `${Math.max(2, Math.min(100, bar))}%` }} />
        </div>
      )}
    </div>
  );
}

function Rows({ title, rows }) {
  return (
    <div className="metric">
      <div className="metric-label"><span>{title}</span></div>
      <dl style={{ margin: 0 }}>
        {rows.map(([k, v]) => (
          <div className="kv" key={k}>
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export default function RightRail() {
  const result = useStore((s) => s.result);
  const analytics = useStore((s) => s.analytics);
  const error = useStore((s) => s.error);
  const running = useStore((s) => s.running);

  if (error) {
    return (
      <aside className="rail right">
        <div className="banner">
          <strong style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <AlertTriangle size={13} /> Run failed
          </strong>
          {error}
        </div>
      </aside>
    );
  }

  if (!result) {
    return (
      <aside className="rail right">
        <div className="metric" style={{ color: 'var(--text-faint)', fontSize: 12, lineHeight: 1.6 }}>
          {running
            ? 'Running the pipeline…'
            : 'Pick a scenario and run the pipeline. Results appear here as they are computed — nothing is shown until it has been measured.'}
        </div>
      </aside>
    );
  }

  const m = result.metrics;
  const gt = result.ground_truth_error;
  const H = result.homography_decomposed;

  const subPixel = m.rmse_px < 1;
  const rmseTone = m.degenerate ? 'warn' : subPixel ? 'ok' : m.rmse_px < 3 ? 'a' : 'warn';
  const ratioTone = m.inlier_ratio > 0.5 ? 'ok' : m.inlier_ratio > 0.25 ? 'warn' : 'bad';

  const gtTone = gt
    ? gt.mean_corner_error_px < 3 ? 'ok' : gt.mean_corner_error_px < 15 ? 'warn' : 'bad'
    : null;

  return (
    <aside className="rail right">
      {/* Accuracy against truth, when we have it. This goes first because it is
          the only number here that cannot be gamed by a confident wrong fit. */}
      {gt && (
        <Metric
          label="Ground-truth error"
          badge={<Target size={11} style={{ marginLeft: 'auto', opacity: 0.6 }} />}
          value={gt.mean_corner_error_px.toFixed(2)}
          unit="px"
          tone={gtTone}
          bar={100 - Math.min(100, gt.mean_corner_error_px * 4)}
          sub={`Mean corner displacement from the known transform. Worst corner ${gt.max_corner_error_px.toFixed(2)} px.`}
        />
      )}

      <Metric
        label="Reprojection RMSE"
        badge={
          m.degenerate ? (
            <AlertTriangle size={11} style={{ marginLeft: 'auto', color: 'var(--warn)' }} />
          ) : subPixel ? (
            <CheckCircle2 size={11} style={{ marginLeft: 'auto', color: 'var(--ok)' }} />
          ) : null
        }
        value={m.rmse_px.toFixed(3)}
        unit="px"
        tone={rmseTone}
        bar={100 - Math.min(100, m.rmse_px * 20)}
        sub={
          m.rmse_m != null
            ? `${m.rmse_m.toFixed(3)} m on the ground at ${m.gsd_m} m/px · median ${m.median_error_px.toFixed(2)} px, p90 ${m.p90_error_px.toFixed(2)} px`
            : `median ${m.median_error_px.toFixed(2)} px, p90 ${m.p90_error_px.toFixed(2)} px`
        }
      />

      {m.warning && (
        <div className="metric">
          <div className="note warn">{m.warning}</div>
        </div>
      )}

      {gt && !m.degenerate && gt.mean_corner_error_px > 15 && (
        <div className="metric">
          <div className="note warn">
            RMSE looks good but the fit is {gt.mean_corner_error_px.toFixed(0)} px from the
            true transform. The inliers agree with each other and with the wrong model —
            which is exactly why reprojection error alone is not sufficient evidence.
          </div>
        </div>
      )}

      <Metric
        label="Inlier consensus"
        badge={<Crosshair size={11} style={{ marginLeft: 'auto', opacity: 0.6 }} />}
        value={(m.inlier_ratio * 100).toFixed(1)}
        unit="%"
        tone={ratioTone}
        bar={m.inlier_ratio * 100}
        sub={`${m.num_inliers} of ${m.num_matches} correspondences survived ${result.settings.ransac_method}`}
      />

      <Rows
        title="Detection"
        rows={[
          ['Keypoints A', m.num_keypoints_a.toLocaleString()],
          ['Keypoints B', m.num_keypoints_b.toLocaleString()],
          ['Putative matches', m.num_matches.toLocaleString()],
          ['Inliers', m.num_inliers.toLocaleString()],
          ['Max residual', `${m.max_error_px.toFixed(2)} px`],
        ]}
      />

      {H && (
        <>
          <Rows
            title="Estimated transform"
            rows={[
              ['Translation', `${H.translation_x.toFixed(1)}, ${H.translation_y.toFixed(1)} px`],
              ['Rotation', `${H.rotation_deg.toFixed(3)}°`],
              ['Scale', H.scale_mean.toFixed(5)],
              ['Shear', `${H.shear_deg.toFixed(3)}°`],
            ]}
          />
          <div className="metric">
            <div className="metric-label"><span>Homography</span></div>
            <div className="hmx">
              {result.homography.flat().map((v, i) => (
                <span key={i}>{Math.abs(v) < 0.001 ? v.toExponential(1) : v.toFixed(4)}</span>
              ))}
            </div>
          </div>
        </>
      )}

      {analytics && (
        <Metric
          label="Correspondence coverage"
          badge={<Grid3x3 size={11} style={{ marginLeft: 'auto', opacity: 0.6 }} />}
          value={(analytics.uniformity * 100).toFixed(0)}
          unit="%"
          tone={analytics.uniformity > 0.5 ? 'ok' : 'warn'}
          bar={analytics.uniformity * 100}
          sub={`${analytics.uniformity_label} distribution across the frame. Matches clustered in one region extrapolate poorly across the rest.`}
        />
      )}

      <Rows
        title="Stage timings"
        rows={result.stages.map((s) => [s.label, `${s.ms.toFixed(0)} ms`])}
      />

      <div className="metric">
        <div className="metric-label"><Clock size={11} /><span>Total {m.total_ms.toFixed(0)} ms</span></div>
        <a
          className="btn ghost"
          style={{ textDecoration: 'none', marginTop: 6 }}
          href={api.csvUrl(result.result_id)}
        >
          <Download size={13} /> Correspondences (CSV)
        </a>
        <a
          className="btn ghost"
          style={{ textDecoration: 'none', marginTop: 6 }}
          href={api.jsonUrl(result.result_id)}
        >
          <Download size={13} /> Full result (JSON)
        </a>
      </div>

      {result.scenario?.notes && (
        <div className="metric">
          <div className="metric-label"><span>About this scenario</span></div>
          <div className="note">{result.scenario.notes}</div>
        </div>
      )}
    </aside>
  );
}
