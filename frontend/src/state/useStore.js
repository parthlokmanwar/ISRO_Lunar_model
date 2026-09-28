/**
 * Application state.
 *
 * Everything the 3D stage draws is derived from `result`, which is the raw
 * response from POST /api/match. Keeping one source of truth is what stops the
 * visualisation and the numbers from drifting apart: in the previous build the
 * telemetry panel had its own hardcoded fallbacks, so the HUD showed a plausible
 * RMSE and a full inlier grid before anything had been run.
 */
import { create } from 'zustand';
import { api } from '../lib/api';

export const STAGES = [
  { key: 'acquire',   name: 'Acquire',      blurb: 'Native-resolution tiles cut from the shared ground footprint.' },
  { key: 'normalize', name: 'Normalise',    blurb: 'CLAHE equalisation and shadow suppression, so illumination stops dominating appearance.' },
  { key: 'detect',    name: 'Detect',       blurb: 'Learned keypoints located independently in each image.' },
  { key: 'match',     name: 'Match',        blurb: 'Descriptor correspondences, drawn brighter where the matcher is more confident.' },
  { key: 'ransac',    name: 'Fit model',    blurb: 'Robust homography estimation; correspondences inconsistent with the model are rejected.' },
  { key: 'align',     name: 'Align',        blurb: 'Image A warped into image B. Grey means registered; red and cyan fringes are residual error.' },
  { key: 'analyze',   name: 'Assess',       blurb: 'Where across the frame the terrain produced reliable correspondences.' },
];

const DEFAULT_SETTINGS = {
  detector: 'auto',
  ransac_method: 'MAGSAC',
  ransac_threshold: 3.0,
  clahe_clip_limit: 3.0,
  suppress_shadows: true,
  max_keypoints: 2048,
  confidence_threshold: 0.1,
};

export const useStore = create((set, get) => ({
  scenarios: [],
  catalogError: null,
  scenarioId: null,

  settings: { ...DEFAULT_SETTINGS },
  result: null,
  analytics: null,

  running: false,
  error: null,
  stageIndex: 0,
  playing: false,
  showAll: false,     // draw rejected matches alongside inliers
  perspective: true,  // 3D camera vs flat-on

  async loadScenarios() {
    try {
      const cat = await api.scenarios();
      const list = cat.scenarios || [];
      set({ scenarios: list, catalogError: null });
      if (!get().scenarioId && list.length) set({ scenarioId: list[0].id });
    } catch (e) {
      set({ catalogError: e.message });
    }
  },

  select(scenarioId) {
    set({ scenarioId, result: null, analytics: null, stageIndex: 0, error: null, playing: false });
  },

  update(patch) {
    set({ settings: { ...get().settings, ...patch } });
  },

  reset() {
    set({ settings: { ...DEFAULT_SETTINGS } });
  },

  async run() {
    const { scenarioId, settings } = get();
    if (!scenarioId) return;
    // The previous result is deliberately left in place while the new one is
    // computed. Clearing it unmounts the 3D canvas, which tears down and
    // recreates the WebGL context and reloads every texture, so the first
    // seconds after a run showed an empty stage. The overlay covers it instead.
    set({ running: true, error: null, analytics: null, stageIndex: 0, playing: false });
    try {
      const result = await api.match({ scenario_id: scenarioId, ...settings });
      set({ result, running: false, stageIndex: 0, playing: true });
      try {
        set({ analytics: await api.analytics(result.result_id) });
      } catch {
        /* analytics is supplementary; a run without inliers has nothing to assess */
      }
    } catch (e) {
      set({ error: e.message, running: false });
    }
  },

  setStage: (i) => set({ stageIndex: Math.max(0, Math.min(STAGES.length - 1, i)) }),
  next: () => set((s) => ({ stageIndex: Math.min(STAGES.length - 1, s.stageIndex + 1) })),
  prev: () => set((s) => ({ stageIndex: Math.max(0, s.stageIndex - 1) })),
  togglePlay: () => set((s) => ({ playing: !s.playing })),
  toggleShowAll: () => set((s) => ({ showAll: !s.showAll })),
  togglePerspective: () => set((s) => ({ perspective: !s.perspective })),
}));

export const currentScenario = (s) => s.scenarios.find((x) => x.id === s.scenarioId) || null;
