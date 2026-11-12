/* NEXORA 80 — progressive-enhancement Command Center.
   Native details keep every existing server-rendered system accessible.
   No storage, fetch, mutation, or hidden progression state.
*/
(function () {
  "use strict";
  const MODULES = [
    ["nexora-collection-anchor79", "Achievement Atlas", "Discover earned and unearned goals", "COLLECTION"],
    [".nexora-mastery72", "Collection Mastery", "Your collection rank and rank thresholds", "MASTERY"],
    ["nexora-pursuits-anchor79", "Achievement Pursuits", "Recommended objectives and next goals", "PURSUITS"],
    [".nexora-intel75", "Settlement Intelligence", "Haven milestones and facility bottlenecks", "INTELLIGENCE"],
    ["nexora-roadmap-anchor79", "Development Roadmap", "Priority upgrades and milestone requirements", "ROADMAP"],
    [".nexora-forecast77", "Resource Forecast", "Construction prices, shortages and blockers", "FORECAST"],
    ["nexora-readiness-anchor79", "Economic Readiness", "Current production and theoretical resource waits", "READINESS"]
  ];
  function init() {
    const command = document.querySelector(".nexora-command79");
    if (!command) return;
    const modules = [];
    for (const [selector, title, description, code] of MODULES) {
      const section = selector.startsWith(".") ?
        document.querySelector(selector) : document.getElementById(selector);
      if (!section || !section.parentNode) continue;
      const details = document.createElement("details");
      details.className = "nexora-command-module80";
      details.dataset.module80 = code;
      const summary = document.createElement("summary");
      summary.className = "nexora-command-summary80";
      const heading = document.createElement("span");
      heading.className = "nexora-command-summary-heading80";
      const name = document.createElement("strong");
      name.textContent = title;
      const hint = document.createElement("small");
      hint.textContent = description;
      heading.append(name, hint);
      const action = document.createElement("span");
      action.className = "nexora-command-summary-action80";
      action.textContent = "EXPAND";
      summary.append(heading, action);
      section.before(details);
      details.append(summary, section);
      modules.push({ section, details, code });
      details.addEventListener("toggle", () => {
        action.textContent = details.open ? "COLLAPSE" : "EXPAND";
      });
    }
    if (!modules.length) return;
    const toolbar = document.createElement("div");
    toolbar.className = "nexora-command-toolbar80";
    const expand = document.createElement("button");
    expand.type = "button";
    expand.textContent = "EXPAND ALL MODULES";
    const collapse = document.createElement("button");
    collapse.type = "button";
    collapse.textContent = "COLLAPSE ALL MODULES";
    expand.addEventListener("click", () => modules.forEach(item => { item.details.open = true; }));
    collapse.addEventListener("click", () => modules.forEach(item => { item.details.open = false; }));
    toolbar.append(expand, collapse);
    command.after(toolbar);

    // Keep the first module visible by default without overwhelming the profile.
    modules[0].details.open = true;

    function revealHash() {
      const id = decodeURIComponent(location.hash.slice(1));
      if (!id) return;
      const target = document.getElementById(id);
      if (!target) return;
      for (const item of modules) {
        if (item.section === target || item.section.contains(target)) {
          item.details.open = true;
          requestAnimationFrame(() => target.scrollIntoView({ block: "start" }));
          break;
        }
      }
    }
    window.addEventListener("hashchange", revealHash);
    revealHash();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else init();
})();
