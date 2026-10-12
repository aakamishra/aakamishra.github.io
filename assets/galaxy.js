// Spiral galaxy point cloud behind the home hero.
import * as THREE from "three";

const canvas = document.querySelector(".hero canvas.scene");
const still = matchMedia("(prefers-reduced-motion: reduce)").matches;

function glowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const g = c.getContext("2d");
  const r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  r.addColorStop(0, "rgba(255,255,255,1)");
  r.addColorStop(0.25, "rgba(255,255,255,.55)");
  r.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = r;
  g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}

function galaxy(count, radius, arms, spin, inner, outer) {
  const pos = new Float32Array(count * 3);
  const col = new Float32Array(count * 3);
  const a = new THREE.Color(inner), b = new THREE.Color(outer), c = new THREE.Color();
  for (let i = 0; i < count; i++) {
    const r = Math.pow(Math.random(), 1.6) * radius;
    const arm = ((i % arms) / arms) * Math.PI * 2;
    const ang = arm + r * spin;
    const jitter = () => Math.pow(Math.random(), 3) * (Math.random() < 0.5 ? 1 : -1) * 0.55 * (r + 0.4);
    pos[i * 3] = Math.cos(ang) * r + jitter();
    pos[i * 3 + 1] = jitter() * 0.35;
    pos[i * 3 + 2] = Math.sin(ang) * r + jitter();
    c.copy(a).lerp(b, r / radius);
    col.set([c.r, c.g, c.b], i * 3);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  return geo;
}

function starfield(count, spread) {
  const pos = new Float32Array(count * 3);
  for (let i = 0; i < count * 3; i++) pos[i] = (Math.random() - 0.5) * spread;
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  return geo;
}

try {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100);
  const tex = glowTexture();

  const disk = new THREE.Points(
    galaxy(innerWidth < 700 ? 30000 : 70000, 7, 4, 0.9, "#FFC98A", "#5DBCE0"),
    new THREE.PointsMaterial({
      size: 0.06, map: tex, vertexColors: true, transparent: true,
      depthWrite: false, blending: THREE.AdditiveBlending,
    })
  );
  const stars = new THREE.Points(
    starfield(2500, 60),
    new THREE.PointsMaterial({
      size: 0.08, map: tex, color: "#C9D6E8", transparent: true, opacity: 0.7,
      depthWrite: false, blending: THREE.AdditiveBlending,
    })
  );
  const group = new THREE.Group();
  group.add(disk);
  group.rotation.set(0.95, 0, 0.35);
  scene.add(group, stars);

  const place = () => {
    const wide = innerWidth > 900;
    group.position.set(wide ? 2.3 : 0.6, wide ? -1.9 : -3.2, 0);
    camera.position.set(0, 0.6, wide ? 9.5 : 11.5);
  };

  const resize = () => {
    const { clientWidth: w, clientHeight: h } = canvas.parentElement;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    place();
  };
  new ResizeObserver(resize).observe(canvas.parentElement);
  resize();

  let mx = 0, my = 0;
  addEventListener("pointermove", (e) => {
    mx = e.clientX / innerWidth - 0.5;
    my = e.clientY / innerHeight - 0.5;
  });

  let visible = true;
  new IntersectionObserver(([e]) => (visible = e.isIntersecting)).observe(canvas);

  const clock = new THREE.Clock();
  const frame = () => {
    const t = clock.getElapsedTime();
    disk.rotation.y = t * 0.035;
    stars.rotation.y = t * 0.004;
    camera.position.x += (mx * 0.9 - camera.position.x) * 0.03;
    camera.position.y += (0.6 - my * 0.6 - camera.position.y) * 0.03;
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
  };
  if (still) frame();
  else renderer.setAnimationLoop(() => visible && frame());
} catch (err) {
  canvas.remove();
}
