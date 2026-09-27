"use strict";
const year = document.getElementById("year");
if (year) year.textContent = String(new Date().getFullYear());

// Diagrams: render <img> only if the Excalidraw export exists.
// Expected files: assets/visuals/diagrams/<name>.png
// Missing files keep the placeholder caption, never a broken image.
(function () {
  const slots = document.querySelectorAll(".diagram-pending[data-diagram]");
  slots.forEach((slot) => {
    const name = slot.getAttribute("data-diagram");
    if (!name || /[^a-z0-9-]/.test(name)) return;
    const probe = new Image();
    probe.onload = () => {
      const img = document.createElement("img");
      img.src = probe.src;
      img.alt = name + " architecture diagram";
      img.loading = "lazy";
      slot.prepend(img);
      slot.classList.remove("diagram-pending");
      slot.classList.add("diagram-ready");
    };
    probe.src = "assets/visuals/diagrams/" + name + ".png";
  });
})();
