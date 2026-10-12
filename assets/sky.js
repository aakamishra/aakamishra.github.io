// Celestial sphere: RA/Dec grid, the ecliptic, bright reference stars,
// and a marker for each object photographed on this page.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const stage = document.querySelector(".sky-stage");
const canvas = stage.querySelector("canvas");
const labels = stage.querySelector(".sky-labels");
const targets = JSON.parse(document.getElementById("sky-data").textContent);
const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
const R = 5;

// Bright stars for orientation: [name, RA hours, Dec degrees].
const BRIGHT = [
  ["Sirius", 6.75, -16.7], ["Canopus", 6.4, -52.7], ["Arcturus", 14.26, 19.2],
  ["Vega", 18.62, 38.8], ["Capella", 5.28, 46.0], ["Rigel", 5.24, -8.2],
  ["Procyon", 7.66, 5.2], ["Betelgeuse", 5.92, 7.4], ["Altair", 19.85, 8.9],
  ["Aldebaran", 4.6, 16.5], ["Antares", 16.49, -26.4], ["Spica", 13.42, -11.2],
  ["Pollux", 7.76, 28.0], ["Fomalhaut", 22.96, -29.6], ["Deneb", 20.69, 45.3],
  ["Regulus", 10.14, 12.0], ["Polaris", 2.53, 89.3], ["Castor", 7.58, 31.9],
  ["Bellatrix", 5.42, 6.35], ["Achernar", 1.63, -57.2],
];

const toVec = (raH, decD, r = R) => {
  const ra = (raH / 24) * Math.PI * 2, dec = (decD * Math.PI) / 180;
  return new THREE.Vector3(r * Math.cos(dec) * Math.cos(ra), r * Math.sin(dec), -r * Math.cos(dec) * Math.sin(ra));
};

function glowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const g = c.getContext("2d");
  const r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  r.addColorStop(0, "rgba(255,255,255,1)");
  r.addColorStop(0.3, "rgba(255,255,255,.5)");
  r.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = r;
  g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}

const line = (pts, color, opacity) =>
  new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(pts),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity })
  );

try {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.set(9, 4, 11);
  const tex = glowTexture();
  const sphere = new THREE.Group();
  scene.add(sphere);

  // Faint shell so the sphere reads as a solid.
  sphere.add(new THREE.Mesh(
    new THREE.SphereGeometry(R * 0.995, 64, 48),
    new THREE.MeshBasicMaterial({ color: "#0B1626", transparent: true, opacity: 0.55 })
  ));

  // Declination circles every 30 degrees; equator brighter.
  for (let d = -60; d <= 60; d += 30) {
    const pts = [];
    for (let h = 0; h <= 24; h += 0.1) pts.push(toVec(h, d));
    sphere.add(line(pts, "#7FDBEF", d === 0 ? 0.45 : 0.14));
  }
  // Right-ascension meridians every 2 hours.
  for (let h = 0; h < 24; h += 2) {
    const pts = [];
    for (let d = -90; d <= 90; d += 2) pts.push(toVec(h, d));
    sphere.add(line(pts, "#7FDBEF", 0.12));
  }
  // Ecliptic, where the Sun, Moon and planets travel.
  const eps = (23.44 * Math.PI) / 180, ecl = [];
  for (let l = 0; l <= 360; l += 1) {
    const lam = (l * Math.PI) / 180;
    const ra = Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam));
    const dec = Math.asin(Math.sin(eps) * Math.sin(lam));
    ecl.push(toVec(((ra < 0 ? ra + 2 * Math.PI : ra) * 12) / Math.PI, (dec * 180) / Math.PI));
  }
  sphere.add(line(ecl, "#FFC98A", 0.6));

  // Reference stars.
  const sg = new THREE.BufferGeometry().setFromPoints(BRIGHT.map(([, h, d]) => toVec(h, d, R * 1.002)));
  sphere.add(new THREE.Points(sg, new THREE.PointsMaterial({
    size: 0.22, map: tex, color: "#DCE6F5", transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  })));

  // Photographed objects.
  const marks = targets.filter((t) => t.ra !== null).map((t) => {
    const p = toVec(t.ra, t.dec, R * 1.01);
    const s = new THREE.Sprite(new THREE.SpriteMaterial({
      map: tex, color: "#FFC98A", transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    }));
    s.position.copy(p);
    s.scale.setScalar(0.55);
    sphere.add(s);
    const b = document.createElement("button");
    b.type = "button";
    if (t.side === "left") b.classList.add("left");
    b.textContent = t.label;
    b.addEventListener("click", () => select(t.id));
    labels.append(b);
    return { t, p, s, b };
  });

  // Distant background dust (decorative, not real stars).
  const dust = new Float32Array(1800 * 3);
  for (let i = 0; i < 1800; i++) {
    const v = new THREE.Vector3().randomDirection().multiplyScalar(30 + Math.random() * 20);
    dust.set([v.x, v.y, v.z], i * 3);
  }
  const dg = new THREE.BufferGeometry();
  dg.setAttribute("position", new THREE.BufferAttribute(dust, 3));
  scene.add(new THREE.Points(dg, new THREE.PointsMaterial({ size: 0.12, map: tex, color: "#8FA3BF", transparent: true, opacity: 0.5, depthWrite: false })));

  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.enableZoom = false;
  controls.autoRotate = !still;
  controls.autoRotateSpeed = 0.5;

  const resize = () => {
    const { clientWidth: w, clientHeight: h } = stage;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.position.setLength(w < 600 ? 19 : 15.5);
    camera.updateProjectionMatrix();
  };
  new ResizeObserver(resize).observe(stage);
  resize();

  function select(id) {
    document.querySelectorAll(".shot.on").forEach((e) => e.classList.remove("on"));
    const card = document.getElementById(id);
    if (card) {
      card.classList.add("on");
      card.scrollIntoView({ behavior: still ? "auto" : "smooth", block: "center" });
    }
    marks.forEach((m) => m.b.classList.toggle("on", m.t.id === id));
  }

  const v = new THREE.Vector3(), toCam = new THREE.Vector3();
  const frame = () => {
    controls.update();
    renderer.render(scene, camera);
    const { clientWidth: w, clientHeight: h } = stage;
    for (const m of marks) {
      m.s.getWorldPosition(v);
      toCam.copy(camera.position).sub(v);
      const front = v.dot(toCam) > 0;
      v.project(camera);
      m.b.style.left = `${((v.x + 1) / 2) * w}px`;
      m.b.style.top = `${((1 - v.y) / 2) * h}px`;
      m.b.style.opacity = front ? 1 : 0;
      m.b.tabIndex = front ? 0 : -1;
    }
  };
  renderer.setAnimationLoop(frame);
} catch (err) {
  stage.remove();
}
