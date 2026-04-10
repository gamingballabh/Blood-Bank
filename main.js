/**
 * HemaTrack — main.js
 * Handles: sidebar toggle · live clock · flash auto-dismiss · form UX
 */

document.addEventListener("DOMContentLoaded", () => {

  // ── Sidebar toggle (mobile) ────────────────────────────────────────────
  const sidebar  = document.getElementById("sidebar");
  const toggle   = document.getElementById("sidebarToggle");
  const overlay  = document.getElementById("sidebarOverlay");

  function openSidebar() {
    sidebar.classList.add("open");
    overlay.classList.add("active");
    document.body.style.overflow = "hidden";
  }

  function closeSidebar() {
    sidebar.classList.remove("open");
    overlay.classList.remove("active");
    document.body.style.overflow = "";
  }

  if (toggle)  toggle.addEventListener("click", openSidebar);
  if (overlay) overlay.addEventListener("click", closeSidebar);

  // Close sidebar on ESC key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && sidebar.classList.contains("open")) {
      closeSidebar();
    }
  });


  // ── Live clock ────────────────────────────────────────────────────────
  const clockEl = document.getElementById("liveClock");

  function updateClock() {
    if (!clockEl) return;
    const now = new Date();
    clockEl.textContent = now.toLocaleString("en-IN", {
      weekday: "short",
      day:     "2-digit",
      month:   "short",
      hour:    "2-digit",
      minute:  "2-digit",
    });
  }

  updateClock();
  setInterval(updateClock, 30_000); // update every 30s


  // ── Flash message auto-dismiss ────────────────────────────────────────
  const flashes = document.querySelectorAll(".flash-msg");
  flashes.forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s ease, transform .4s ease";
      el.style.opacity    = "0";
      el.style.transform  = "translateY(-6px)";
      setTimeout(() => el.remove(), 420);
    }, 4000); // dismiss after 4 seconds
  });


  // ── Form: prevent double-submit ───────────────────────────────────────
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", function () {
      const btn = this.querySelector("button[type='submit']");
      if (!btn) return;

      // Brief loading state
      btn.disabled = true;
      const original = btn.innerHTML;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>Saving…`;

      // Re-enable after 3s in case of server error
      setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = original;
      }, 3000);
    });
  });


  // ── Animate level bars on load (inventory page) ───────────────────────
  // Bars start at 0 via CSS animation, JS just ensures they render
  document.querySelectorAll(".level-bar__fill").forEach((bar) => {
    const target = bar.style.width;
    bar.style.width = "0%";
    setTimeout(() => { bar.style.width = target; }, 100);
  });

});
