/**
 * The 3D stage.
 *
 * Two image planes sit side by side in space and every pipeline step is shown
 * happening to them: normalisation crossfades the texture, detection scatters
 * the real keypoints onto each plane, matching draws the real correspondences
 * across the gap, model fitting drops the rejected ones, alignment slides the
 * planes together and warps A by the estimated homography, and the assessment
 * step displaces a surface by correspondence density.
 *
 * Every coordinate comes from the API response. `toLocal` is the single place
 * that converts image pixels to plane space.
 *
 * Two structural decisions worth knowing about:
 *
 * - All animation is driven from ONE useFrame, in <Animator>, which advances a
 *   set of eased 0..1 values and passes them down as props. Children are then
 *   purely declarative. An earlier version had each child mutate its own object
 *   inside its own useFrame; the keypoint clouds' callbacks silently never ran,
 *   which left both clouds stacked at the origin with nothing in the code to say
 *   so. With a single driver the worst case is that motion stops - everything
 *   still renders in the right place.
 *
 * - There is no drei <Text>. It loads a font and suspends, and one suspended
 *   child blanks the whole boundary. Labels live in the HTML overlay instead.
 */
import { useMemo, useRef, useEffect, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

import { useStore, STAGES } from '../state/useStore';

const A_COLOR = '#5ec8c0';
const B_COLOR = '#e8a765';
const BAD_COLOR = '#e0715f';

const PLANE_W = 3.4;
// Separation along X, not Z. Stacked in depth, the near plane simply occluded
// the far one from any head-on view and the correspondence lines had nowhere to
// run. Side by side is the readable layout, and it is what makes orbiting worth
// doing: the matches become a visible sheaf in space.
const GAP_SPREAD = 2.15;
const DEPTH_STAGGER = 0.55;

const STAGE_KEYS = STAGES.map((s) => s.key);
const at = (k) => STAGE_KEYS.indexOf(k);

function toLocal(x, y, imgW, imgH, planeW, planeH) {
  return [(x / imgW - 0.5) * planeW, -(y / imgH - 0.5) * planeH];
}

/**
 * Load textures imperatively, so a slow image never suspends the scene, and keep
 * them in a module-level cache.
 *
 * The cache is what stops the planes flashing dark. They unmount at the
 * assessment stage, which shows a surface instead, and remounting used to
 * restart the load - so stepping back through the pipeline showed the empty
 * placeholder colour for as long as a half-megabyte PNG took to decode.
 */
const TEXTURE_CACHE = new Map();
// Per-run images carry a ?v=<run id> so a re-run never shows the previous
// run's normalisation. That makes every run add new entries, so those are
// bounded: the oldest per-run textures are released from the GPU. The scene
// tiles themselves (ten, unversioned) are never evicted - they stay on screen
// across runs, and they are the oldest entries in the Map.
const RUN_TEXTURES_MAX = 8;

function evictOldTextures() {
  const perRun = [...TEXTURE_CACHE.keys()].filter((u) => u.includes('?v='));
  for (const url of perRun.slice(0, Math.max(0, perRun.length - RUN_TEXTURES_MAX))) {
    TEXTURE_CACHE.get(url)._resolved?.dispose();
    TEXTURE_CACHE.delete(url);
  }
}

function loadTexture(url) {
  if (TEXTURE_CACHE.has(url)) return TEXTURE_CACHE.get(url);
  const promise = new Promise((resolve) => {
    new THREE.TextureLoader().load(
      url,
      (t) => {
        t.colorSpace = THREE.SRGBColorSpace;
        t.anisotropy = 8;
        promise._resolved = t;
        resolve(t);
      },
      undefined,
      () => resolve(null),
    );
  });
  TEXTURE_CACHE.set(url, promise);
  evictOldTextures();
  return promise;
}

function useImageTexture(url) {
  const [tex, setTex] = useState(null);

  useEffect(() => {
    if (!url) { setTex(null); return undefined; }
    let dead = false;
    loadTexture(url).then((t) => { if (!dead) setTex(t); });
    return () => { dead = true; };
  }, [url]);

  // Resolve synchronously on remount when the texture is already decoded, so
  // there is no frame where the plane has no image.
  const cached = TEXTURE_CACHE.get(url);
  if (!tex && cached && cached._resolved) return cached._resolved;
  return tex;
}

/* -------------------------------------------------------------------------- */
/* the single animation driver                                                 */
/* -------------------------------------------------------------------------- */
function Animator({ targets, onChange }) {
  const cur = useRef({ ...targets });
  const acc = useRef(0);

  useFrame((_, dt) => {
    let moved = false;
    const next = { ...cur.current };
    for (const k of Object.keys(targets)) {
      const to = targets[k];
      const from = next[k] ?? 0;
      const d = to - from;
      if (Math.abs(d) < 0.003) {
        if (from !== to) { next[k] = to; moved = true; }
      } else {
        next[k] = from + d * Math.min(1, dt * 2.6);
        moved = true;
      }
    }
    cur.current = next;

    // Publish at ~40 Hz. The scene is small enough that re-rendering it is cheap,
    // and this keeps React in charge of where everything sits.
    acc.current += dt;
    if (moved && acc.current > 0.025) {
      acc.current = 0;
      onChange(next);
    }
  });

  return null;
}

/* -------------------------------------------------------------------------- */
/* image plane                                                                 */
/* -------------------------------------------------------------------------- */
function ImagePlane({
  rawUrl, procUrl, planeW, planeH, tint, sign, gap, norm,
  homography, warp, imgW, imgH,
}) {
  const raw = useImageTexture(rawUrl);
  const proc = useImageTexture(procUrl);

  const x = sign * gap;
  const z = sign * DEPTH_STAGGER * (gap / GAP_SPREAD);

  // The estimated homography, converted from pixel space into plane units and
  // ramped by `warp`, so alignment is something you watch happen rather than a
  // cut to the answer.
  const matrix = useMemo(() => {
    if (!homography || warp <= 0.001) return null;
    const H = homography;
    const sx = planeW / imgW;
    const sy = planeH / imgH;
    const t = warp;
    const a = 1 + (H[0][0] - 1) * t;
    const b = H[0][1] * t * (sy / sx);
    const d = H[1][0] * t * (sx / sy);
    const e = 1 + (H[1][1] - 1) * t;
    const tx = (H[0][2] * sx - (planeW / 2) * (a - 1) - (planeH / 2) * b) * t;
    const ty = (-H[1][2] * sy + (planeH / 2) * (e - 1) + (planeW / 2) * d) * t;
    return new THREE.Matrix4().set(
      a, b, 0, tx + x,
      d, e, 0, ty,
      0, 0, 1, z,
      0, 0, 0, 1,
    );
  }, [homography, warp, planeW, planeH, imgW, imgH, x, z]);

  // Drive the object imperatively rather than by swapping between a `position`
  // prop and a `matrix` prop.
  //
  // R3F applies props but does not un-apply them: once matrixAutoUpdate had been
  // set false for the warp, it stayed false when the prop disappeared, so the
  // plane ignored `position` from then on and stayed wherever its last matrix
  // put it. Setting both fields explicitly every render removes that whole class
  // of stale-state bug.
  const group = useRef();
  useEffect(() => {
    const g = group.current;
    if (!g) return;
    if (matrix) {
      g.matrixAutoUpdate = false;
      g.matrix.copy(matrix);
      g.matrixWorldNeedsUpdate = true;
    } else {
      g.matrixAutoUpdate = true;
      g.position.set(x, 0, z);
      g.rotation.set(0, 0, 0);
      g.scale.set(1, 1, 1);
      g.updateMatrix();
    }
  });

  return (
    <group ref={group} position={[x, 0, z]}>
      <mesh>
        <planeGeometry args={[planeW, planeH]} />
        {/*
          The material is keyed on the texture so it is rebuilt when the image
          arrives. Assigning `map` to a material compiled without one leaves the
          shader with no sampler, so the plane stays a flat colour and the
          imagery never appears.
        */}
        {raw
          ? <meshBasicMaterial key="tex" map={raw} toneMapped={false} />
          : <meshBasicMaterial key="flat" color="#1b212b" toneMapped={false} />}
      </mesh>

      {proc && (
        <mesh position={[0, 0, 0.004]} visible={norm > 0.01}>
          <planeGeometry args={[planeW, planeH]} />
          <meshBasicMaterial key={proc.uuid} map={proc} transparent opacity={norm} toneMapped={false} />
        </mesh>
      )}

      <lineSegments position={[0, 0, 0.01]}>
        <edgesGeometry args={[new THREE.PlaneGeometry(planeW, planeH)]} />
        <lineBasicMaterial color={tint} transparent opacity={0.8} />
      </lineSegments>
    </group>
  );
}

/* -------------------------------------------------------------------------- */
/* keypoints                                                                   */
/* -------------------------------------------------------------------------- */
function Keypoints({ points, imgW, imgH, planeW, planeH, color, sign, gap, reveal, visible }) {
  const geom = useRef();

  const positions = useMemo(() => {
    const arr = new Float32Array(points.length * 3);
    for (let i = 0; i < points.length; i++) {
      const [lx, ly] = toLocal(points[i][0], points[i][1], imgW, imgH, planeW, planeH);
      arr[i * 3] = lx;
      arr[i * 3 + 1] = ly;
      arr[i * 3 + 2] = 0.02;
    }
    return arr;
  }, [points, imgW, imgH, planeW, planeH]);

  // Reveal progressively so the spatial density pattern is readable rather than
  // arriving as one flat wash of dots.
  const shown = Math.max(1, Math.floor(points.length * reveal));
  useEffect(() => {
    if (geom.current) geom.current.setDrawRange(0, shown);
  }, [shown, positions]);

  if (!points.length) return null;

  const x = sign * gap;
  const z = sign * DEPTH_STAGGER * (gap / GAP_SPREAD);

  return (
    <points position={[x, 0, z]} renderOrder={10} frustumCulled={false} visible={visible}>
      <bufferGeometry ref={geom}>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color={color}
        sizeAttenuation
        transparent
        opacity={0.95}
        depthWrite={false}
      />
    </points>
  );
}

/* -------------------------------------------------------------------------- */
/* correspondence lines                                                        */
/* -------------------------------------------------------------------------- */
function MatchLines({ result, planeW, planeH, showRejected, gap, reveal, fade, visible }) {
  const { keypoints_a: ka, keypoints_b: kb, matches, image } = result;
  const imgW = image.width;
  const imgH = image.height;
  const geom = useRef();

  const shown = useMemo(() => {
    const out = [];
    for (const m of matches) {
      const pa = ka[m.idx_a];
      const pb = kb[m.idx_b];
      if (!pa || !pb) continue;
      if (!showRejected && !m.inlier) continue;
      const [ax, ay] = toLocal(pa[0], pa[1], imgW, imgH, planeW, planeH);
      const [bx, by] = toLocal(pb[0], pb[1], imgW, imgH, planeW, planeH);
      out.push({ ax, ay, bx, by, inlier: !!m.inlier, conf: m.confidence ?? 0.5 });
    }
    // Inliers last, so they draw over the rejected ones.
    return out.sort((p, q) => Number(p.inlier) - Number(q.inlier));
  }, [matches, ka, kb, imgW, imgH, planeW, planeH, showRejected]);

  const zs = DEPTH_STAGGER * (gap / GAP_SPREAD);

  const { positions, colors } = useMemo(() => {
    const p = new Float32Array(shown.length * 6);
    const c = new Float32Array(shown.length * 6);
    const inA = new THREE.Color(A_COLOR);
    const inB = new THREE.Color(B_COLOR);
    const bad = new THREE.Color(BAD_COLOR);
    shown.forEach((l, i) => {
      p[i * 6] = l.ax - gap; p[i * 6 + 1] = l.ay; p[i * 6 + 2] = -zs;
      p[i * 6 + 3] = l.bx + gap; p[i * 6 + 4] = l.by; p[i * 6 + 5] = zs;
      // Confidence drives brightness, so a weak consensus looks weak.
      const k = l.inlier ? 0.5 + l.conf * 0.5 : 0.35;
      const ca = (l.inlier ? inA : bad).clone().multiplyScalar(k);
      const cb = (l.inlier ? inB : bad).clone().multiplyScalar(k);
      c[i * 6] = ca.r; c[i * 6 + 1] = ca.g; c[i * 6 + 2] = ca.b;
      c[i * 6 + 3] = cb.r; c[i * 6 + 4] = cb.g; c[i * 6 + 5] = cb.b;
    });
    return { positions: p, colors: c };
  }, [shown, gap, zs]);

  const count = Math.floor(shown.length * reveal) * 2;
  useEffect(() => {
    if (geom.current) geom.current.setDrawRange(0, count);
  }, [count, positions]);

  if (!shown.length) return null;

  return (
    <lineSegments renderOrder={9} frustumCulled={false} visible={visible}>
      <bufferGeometry ref={geom}>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <lineBasicMaterial
        vertexColors
        transparent
        opacity={0.85 * (1 - fade * 0.85)}
        depthWrite={false}
      />
    </lineSegments>
  );
}

/* -------------------------------------------------------------------------- */
/* density surface                                                             */
/* -------------------------------------------------------------------------- */
function DensitySurface({ analytics, planeW, planeH, visible }) {
  const geom = useMemo(() => {
    if (!analytics?.cells?.length) return null;
    const grid = analytics.grid;
    const g = new THREE.PlaneGeometry(planeW * 1.4, planeH * 1.4, grid - 1, grid - 1);
    const pos = g.attributes.position;
    const colors = new Float32Array(pos.count * 3);
    const lut = new Map(analytics.cells.map((c) => [`${c.row}:${c.col}`, c.density]));
    const low = new THREE.Color('#1b2430');
    const high = new THREE.Color(A_COLOR);
    for (let i = 0; i < pos.count; i++) {
      const col = i % grid;
      const row = Math.floor(i / grid);
      const d = lut.get(`${row}:${col}`) ?? 0;
      pos.setZ(i, d * 1.1);
      const c = low.clone().lerp(high, Math.min(1, d * 1.7));
      colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;
    }
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    g.computeVertexNormals();
    return g;
  }, [analytics, planeW, planeH]);

  if (!geom) return null;

  return (
    <group rotation={[-0.5, 0, 0]} visible={visible}>
      <mesh geometry={geom}>
        <meshStandardMaterial vertexColors roughness={0.8} metalness={0.05} />
      </mesh>
      <mesh geometry={geom} position={[0, 0, 0.006]}>
        <meshBasicMaterial wireframe color="#59657a" transparent opacity={0.25} />
      </mesh>
    </group>
  );
}

/* -------------------------------------------------------------------------- */
/* camera                                                                      */
/* -------------------------------------------------------------------------- */
// Distances are set so the pair reads as two separate images with room around
// them, and the match view is three-quarter rather than side-on: edge-on, the
// planes collapse to slivers and the sheaf of correspondences disappears.
const VIEWS = {
  acquire: [1.4, 0.9, 9.8],
  normalize: [0.7, 0.4, 8.8],
  detect: [-1.3, 0.6, 7.8],
  match: [3.6, 1.7, 8.8],
  ransac: [2.9, 1.3, 9.0],
  align: [0.0, 0.0, 7.2],
  analyze: [0.0, -4.6, 5.0],
};

/**
 * Move to the stage's viewpoint, then hand the camera back to OrbitControls.
 *
 * OrbitControls is switched off for the duration of the move. With damping on it
 * writes camera.position from its own spherical state every frame, so while the
 * rig was also lerping, the two fought: the camera got dragged somewhere between
 * the two answers - occasionally past the planes entirely - and the stage went
 * black until the move ended and OrbitControls won. Only one thing may drive the
 * camera at a time.
 */
function CameraRig({ stageKey, perspective, controlsRef }) {
  const settling = useRef(true);
  const target = useRef(new THREE.Vector3(...VIEWS.acquire));

  useEffect(() => {
    const v = perspective ? (VIEWS[stageKey] || VIEWS.acquire) : [0, 0, 8.4];
    target.current.set(v[0], v[1], v[2]);
    settling.current = true;
    const controls = controlsRef.current;
    if (controls) controls.enabled = false;
  }, [stageKey, perspective, controlsRef]);

  useFrame(({ camera }, dt) => {
    if (!settling.current) return;

    camera.position.lerp(target.current, Math.min(1, dt * 2.6));
    camera.lookAt(0, 0, 0);

    if (camera.position.distanceTo(target.current) < 0.03) {
      camera.position.copy(target.current);
      camera.lookAt(0, 0, 0);
      settling.current = false;
      const controls = controlsRef.current;
      if (controls) {
        // Re-seat the controls on where the camera actually is before handing
        // back, so the first drag does not jump.
        controls.target.set(0, 0, 0);
        controls.update();
        controls.enabled = true;
      }
    }
  });

  return null;
}

/* -------------------------------------------------------------------------- */
/* scene                                                                       */
/* -------------------------------------------------------------------------- */
function Scene({ result, analytics, stageKey, showAll, perspective }) {
  const controls = useRef();
  const imgW = result.image.width;
  const imgH = result.image.height;
  const planeW = PLANE_W;
  const planeH = PLANE_W * (imgH / imgW);

  const idx = at(stageKey);
  const targets = useMemo(() => ({
    norm: idx >= at('normalize') ? 1 : 0,
    detect: idx >= at('detect') ? 1 : 0,
    match: idx >= at('match') ? 1 : 0,
    align: idx >= at('align') ? 1 : 0,
  }), [idx]);

  const [t, setT] = useState(targets);
  const gap = GAP_SPREAD * (1 - t.align * 0.985);

  const isSurface = stageKey === 'analyze';
  const showRejected = (stageKey === 'match' || stageKey === 'ransac') && showAll;

  return (
    <>
      <ambientLight intensity={0.85} />
      <directionalLight position={[3, 5, 6]} intensity={0.65} />
      <Animator targets={targets} onChange={setT} />
      <CameraRig stageKey={stageKey} perspective={perspective} controlsRef={controls} />

      {/*
        Every layer stays mounted for the life of the result and is shown or
        hidden with `visible`. Mounting the keypoints, lines and surface only
        when their stage arrived made three.js compile their shaders at that
        moment, mid-transition, which is where the autoplay caught a blank
        frame. Now all programs compile on the first frame after a run.
      */}
      <group visible={!isSurface}>
        <ImagePlane
          rawUrl={result.image.raw_url_a} procUrl={result.image.proc_url_a}
          planeW={planeW} planeH={planeH} tint={A_COLOR}
          sign={-1} gap={gap} norm={t.norm}
          homography={result.homography} warp={t.align}
          imgW={imgW} imgH={imgH}
        />
        <ImagePlane
          rawUrl={result.image.raw_url_b} procUrl={result.image.proc_url_b}
          planeW={planeW} planeH={planeH} tint={B_COLOR}
          sign={1} gap={gap} norm={t.norm}
          homography={null} warp={0}
          imgW={imgW} imgH={imgH}
        />

        <Keypoints
          points={result.keypoints_a} imgW={imgW} imgH={imgH}
          planeW={planeW} planeH={planeH} color={A_COLOR}
          sign={-1} gap={gap} reveal={t.detect} visible={t.detect > 0.001}
        />
        <Keypoints
          points={result.keypoints_b} imgW={imgW} imgH={imgH}
          planeW={planeW} planeH={planeH} color={B_COLOR}
          sign={1} gap={gap} reveal={t.detect} visible={t.detect > 0.001}
        />

        <MatchLines
          result={result} planeW={planeW} planeH={planeH}
          showRejected={showRejected}
          gap={gap} reveal={t.match} fade={t.align} visible={t.match > 0.001}
        />
      </group>

      <DensitySurface analytics={analytics} planeW={planeW} planeH={planeH} visible={isSurface} />

      <OrbitControls
        ref={controls}
        enablePan={false}
        enableDamping
        dampingFactor={0.08}
        minDistance={1.8}
        maxDistance={16}
      />
    </>
  );
}

/* -------------------------------------------------------------------------- */
export default function Stage3D() {
  const result = useStore((s) => s.result);
  const analytics = useStore((s) => s.analytics);
  const stageIndex = useStore((s) => s.stageIndex);
  const showAll = useStore((s) => s.showAll);
  const perspective = useStore((s) => s.perspective);

  if (!result) return null;

  return (
    <Canvas
      dpr={[1, 2]}
      camera={{ position: VIEWS.acquire, fov: 42, near: 0.1, far: 100 }}
      gl={{ antialias: true, alpha: true }}
    >
      <Scene
        result={result}
        analytics={analytics}
        stageKey={STAGES[stageIndex]?.key ?? 'acquire'}
        showAll={showAll}
        perspective={perspective}
      />
    </Canvas>
  );
}
