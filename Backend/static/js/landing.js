/* =========================================================
   LANDING PAGE
========================================================= */
(function () {
  "use strict";
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const API_BASE = "/api/v1";

  async function api(path, { method = "GET", body } = {}) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method,
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      let data = null;
      try { data = await res.json(); } catch { data = null; }
      return { ok: res.ok, status: res.status, data };
    } catch {
      return { ok: false, status: 0, data: null };
    }
  }

  const AUTH = { user: null };

  // Sticky Nav
  const nav = document.getElementById("siteNav");
  if (nav) {
    window.addEventListener("scroll", () => {
      nav.classList.toggle("scrolled", window.scrollY > 24);
    }, { passive: true });
  }

  // Mobile Menu
  const navToggle = document.getElementById("navToggle");
  const mobileMenu = document.getElementById("mobileMenu");
  if (navToggle && mobileMenu) {
    navToggle.addEventListener("click", () => {
      const isOpen = navToggle.getAttribute("aria-expanded") === "true";
      navToggle.setAttribute("aria-expanded", String(!isOpen));
      mobileMenu.hidden = isOpen;
    });
  }

  // Reveal Animations
  const revealEls = document.querySelectorAll(".reveal");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealEls.forEach((el) => el.classList.add("in-view"));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in-view"); io.unobserve(e.target); } });
    }, { threshold: 0.12 });
    revealEls.forEach((el) => io.observe(el));
  }

  // Nav Auth Swapping
  function getInitials(name) {
    if (!name) return "?";
    const parts = name.trim().split(/[\s._-]+/).filter(Boolean);
    return parts.length === 1 ? parts[0][0].toUpperCase() : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  function applyLoggedOut() {
    AUTH.user = null;
    document.querySelectorAll(".nav-auth.nav-guest").forEach((el) => { el.hidden = false; });
    document.querySelectorAll(".nav-auth.nav-user").forEach((el) => { el.hidden = true; });
    
    const heroCta = document.getElementById("heroPrimaryCta");
    if (heroCta) { heroCta.href = "/register"; heroCta.innerHTML = 'Get Started <span class="arrow">→</span>'; }
    const previewCta = document.getElementById("previewPrimaryCta");
    if (previewCta) { previewCta.href = "/register"; previewCta.innerHTML = 'Get started <span class="arrow">→</span>'; }
  }

  function applyLoggedIn(user) {
    AUTH.user = user;
    document.querySelectorAll(".nav-auth.nav-guest").forEach((el) => { el.hidden = true; });
    document.querySelectorAll(".nav-auth.nav-user").forEach((el) => { el.hidden = false; });

    const display = user.username || user.email.split("@")[0] || "Account";
    const initials = getInitials(display);

    document.getElementById("navUsername").textContent = display;
    document.getElementById("navAvatar").textContent = initials;
    document.getElementById("mobileUsername").textContent = display;
    document.getElementById("mobileAvatar").textContent = initials;

    const heroCta = document.getElementById("heroPrimaryCta");
    if (heroCta) { heroCta.href = "/dashboard"; heroCta.innerHTML = 'Open dashboard <span class="arrow">→</span>'; }
    const previewCta = document.getElementById("previewPrimaryCta");
    if (previewCta) { previewCta.href = "/dashboard"; previewCta.innerHTML = 'Open your dashboard <span class="arrow">→</span>'; }
  }

  async function checkAuthStatus() {
    const res = await api("/auth/status");
    if (res.ok && res.data && res.data.data && res.data.data.authenticated === true) {
      applyLoggedIn(res.data.data.user);
    } else {
      applyLoggedOut();
    }
  }

  // Logout
  async function handleLogout(btn) {
    btn.disabled = true;
    const csrf = sessionStorage.getItem("segmind_csrf_token") || "";
    await api("/auth/logout", { method: "POST", headers: { "X-CSRF-TOKEN": csrf } });
    sessionStorage.removeItem("segmind_csrf_token");
    window.location.href = "/";
  }

  const navLogout = document.getElementById("navLogoutBtn");
  const mobileLogout = document.getElementById("mobileLogoutBtn");
  if (navLogout) navLogout.addEventListener("click", () => handleLogout(navLogout));
  if (mobileLogout) mobileLogout.addEventListener("click", () => handleLogout(mobileLogout));

  checkAuthStatus();
})();