// Research filters, BibTeX copy, and the portrait tilt.
const filters = document.querySelector(".filters");
if (filters) {
  filters.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    filters.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
    const tag = b.dataset.tag;
    document.querySelectorAll(".pub").forEach((p) => {
      p.hidden = tag !== "all" && !p.dataset.tags.split(" ").includes(tag);
    });
  });
}

document.querySelectorAll("[data-copy]").forEach((b) => {
  b.addEventListener("click", async () => {
    const text = document.getElementById(b.dataset.copy).textContent;
    try {
      await navigator.clipboard.writeText(text);
      b.textContent = "Copied";
    } catch {
      getSelection().selectAllChildren(document.getElementById(b.dataset.copy));
      b.textContent = "Selected";
    }
    setTimeout(() => (b.textContent = "Copy"), 1600);
  });
});

const card = document.querySelector(".portrait .card");
if (card && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const box = card.parentElement;
  box.addEventListener("pointermove", (e) => {
    const r = box.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
    card.style.transform = `rotateY(${(x - 0.5) * 8}deg) rotateX(${(0.5 - y) * 8}deg)`;
  });
  box.addEventListener("pointerleave", () => (card.style.transform = ""));
}
