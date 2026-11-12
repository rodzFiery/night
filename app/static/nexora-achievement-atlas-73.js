/* NEXORA 73 — accessible, progressive-enhancement Collection Atlas.
   Filtering and ordering only; the server remains the source of earned state. */
(function () {
  "use strict";
  function init() {
    const root = document.querySelector(".nexora-discovery71");
    if (!root) return;
    const grid = root.querySelector(".nexora-discovery-grid71");
    if (!grid) return;
    const cards = Array.from(grid.querySelectorAll(".nexora-discovery-goal71"));
    if (!cards.length) return;

    const toolbar = document.createElement("div");
    toolbar.className = "nexora-atlas-toolbar73";
    toolbar.setAttribute("aria-label", "Achievement Atlas controls");
    function field(labelText, control) {
      const label = document.createElement("label");
      const title = document.createElement("span");
      title.textContent = labelText;
      label.append(title, control);
      toolbar.append(label);
      return control;
    }
    const search = field("SEARCH GOALS", document.createElement("input"));
    search.type = "search";
    search.placeholder = "Find a chapter or objective";
    search.autocomplete = "off";
    const world = field("WORLD", document.createElement("select"));
    for (const value of ["ALL", ...new Set(cards.map(card => card.dataset.world73))]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value === "ALL" ? "All connected worlds" : value;
      world.append(option);
    }
    const status = field("COLLECTION", document.createElement("select"));
    for (const [value, title] of [["all", "All goals"], ["available", "Not yet earned"], ["earned", "Earned"]]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = title;
      status.append(option);
    }
    const order = field("ORDER", document.createElement("select"));
    for (const [value, title] of [["original", "Catalog order"], ["title", "Name A–Z"], ["unearned", "Available first"]]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = title;
      order.append(option);
    }
    const counter = document.createElement("p");
    counter.className = "nexora-atlas-count73";
    counter.setAttribute("role", "status");
    counter.setAttribute("aria-live", "polite");
    const empty = document.createElement("p");
    empty.className = "nexora-atlas-empty73";
    empty.textContent = "No achievements match these filters. Try another world or search.";
    empty.hidden = true;
    grid.before(toolbar, counter);
    grid.after(empty);
    const original = new Map(cards.map((card, index) => [card, index]));
    function apply() {
      const query = search.value.trim().toLocaleLowerCase();
      const selectedWorld = world.value;
      const selectedStatus = status.value;
      const selectedOrder = order.value;
      const sorted = cards.slice().sort((a, b) => {
        if (selectedOrder === "title") {
          return a.dataset.title73.localeCompare(b.dataset.title73) || original.get(a) - original.get(b);
        }
        if (selectedOrder === "unearned") {
          return Number(a.dataset.earned73 === "true") - Number(b.dataset.earned73 === "true") ||
            original.get(a) - original.get(b);
        }
        return original.get(a) - original.get(b);
      });
      let visible = 0;
      for (const card of sorted) {
        const match = (selectedWorld === "ALL" || card.dataset.world73 === selectedWorld) &&
          (selectedStatus === "all" || (card.dataset.earned73 === "true") === (selectedStatus === "earned")) &&
          (!query || card.textContent.toLocaleLowerCase().includes(query));
        card.hidden = !match;
        if (match) visible++;
        grid.append(card);
      }
      counter.textContent = visible + " of " + cards.length + " known achievements shown";
      empty.hidden = visible !== 0;
    }
    for (const control of [search, world, status, order]) {
      control.addEventListener(control === search ? "input" : "change", apply);
    }
    apply();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
