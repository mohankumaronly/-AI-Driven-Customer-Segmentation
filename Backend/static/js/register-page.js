/* =========================================================
   REGISTER PAGE
========================================================= */
(function () {
  "use strict";

  const API_BASE = "/api/v1";
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  // 1. AUTO-REDIRECT IF LOGGED IN
  (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/status`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        if (data.data && data.data.authenticated === true) {
          window.location.replace("/dashboard");
        }
      }
    } catch {}
  })();

  const state = { username: "", email: "", password: "", step: 1, resendTimer: null, verifying: false, registering: false };

  async function api(path, { method = "POST", body } = {}) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method,
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      let data = null;
      try { data = await res.json(); } catch { data = null; }
      if (res.ok) return { ok: true, status: res.status, data };

      let fieldErrors = (data && data.errors && Array.isArray(data.errors)) ? data.errors : [];
      const message = (data && data.message) || `Request failed (${res.status})`;

      return { ok: false, status: res.status, data, error: message, fieldErrors };
    } catch {
      return { ok: false, status: 0, error: "Network error", fieldErrors: [] };
    }
  }

  function setMessage(el, type, text) {
    if (!el) return;
    el.textContent = text || "";
    el.className = "form-message" + (type ? " " + type : "");
    el.hidden = !text;
  }

  function setLoading(btn, loading) {
    if (!btn) return;
    btn.classList.toggle("loading", loading);
    btn.disabled = loading;
    const spinner = btn.querySelector(".btn-spinner");
    if (spinner) spinner.hidden = !loading;
  }

  function setFieldError(input, hintEl, message) {
    if (input) input.setAttribute("aria-invalid", message ? "true" : "false");
    if (hintEl) {
      hintEl.textContent = message || hintEl.dataset.defaultHint || "";
      hintEl.classList.toggle("error", Boolean(message));
      hintEl.classList.remove("ok");
    }
  }

  function setFieldOk(input, hintEl, message) {
    if (input) input.removeAttribute("aria-invalid");
    if (hintEl) {
      hintEl.textContent = message || hintEl.dataset.defaultHint || "";
      hintEl.classList.remove("error");
      hintEl.classList.toggle("ok", Boolean(message));
    }
  }

  $$(".field-hint").forEach((h) => { h.dataset.defaultHint = h.textContent.trim(); });

  const USERNAME_RE = /^[a-zA-Z0-9_]{3,32}$/;
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function scorePassword(pw) {
    let s = 0;
    if (pw.length >= 8) s++;
    if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) s++;
    if (/\d/.test(pw)) s++;
    if (/[^A-Za-z0-9]/.test(pw)) s++;
    return s;
  }

  function goToStep(n) {
    state.step = n;
    $$(".form-step").forEach((el) => el.classList.toggle("active", Number(el.dataset.panel) === n));
    $$(".step-ind").forEach((el) => {
      const num = Number(el.dataset.step);
      el.classList.toggle("active", num === n);
      el.classList.toggle("done", num < n);
    });
  }

  const registerForm = $("#registerForm");
  const registerBtn = $("#registerBtn");
  const registerMessage = $("#registerMessage");

  const usernameInput = $("#username");
  const emailInput = $("#email");
  const passwordInput = $("#password");
  const confirmInput = $("#confirmPassword");
  const termsInput = $("#terms");

  const usernameHint = $('[data-hint="username"]');
  const emailHint = $('[data-hint="email"]');
  const passwordHint = $('[data-hint="password"]');
  const confirmHint = $('[data-hint="confirmPassword"]');
  const pwMeter = $("#pwMeter");
  const togglePasswordBtn = $("#togglePassword");

  passwordInput.addEventListener("input", () => {
    const score = scorePassword(passwordInput.value);
    pwMeter.dataset.strength = String(score);
    if (passwordInput.value.length === 0) setFieldError(passwordInput, passwordHint, "");
    else if (passwordInput.value.length < 8) setFieldError(passwordInput, passwordHint, "Password must be at least 8 characters.");
    else setFieldOk(passwordInput, passwordHint, "");
    if (confirmInput.value) validateConfirm();
  });

  confirmInput.addEventListener("input", validateConfirm);

  function validateConfirm() {
    if (!confirmInput.value) return setFieldError(confirmInput, confirmHint, "");
    if (confirmInput.value !== passwordInput.value) return setFieldError(confirmInput, confirmHint, "Passwords do not match.");
    setFieldOk(confirmInput, confirmHint, "Passwords match.");
    return true;
  }

  togglePasswordBtn.addEventListener("click", () => {
    const show = passwordInput.type === "password";
    passwordInput.type = show ? "text" : "password";
    togglePasswordBtn.textContent = show ? "Hide" : "Show";
  });

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (state.registering) return;
    setMessage(registerMessage, "", "");

    const username = usernameInput.value.trim();
    const email = emailInput.value.trim().toLowerCase();
    const password = passwordInput.value;
    let hasError = false;

    if (!USERNAME_RE.test(username)) { setFieldError(usernameInput, usernameHint, "Use 3–32 characters: letters, numbers, underscores."); hasError = true; }
    else setFieldOk(usernameInput, usernameHint, "");

    if (!EMAIL_RE.test(email)) { setFieldError(emailInput, emailHint, "Enter a valid email."); hasError = true; }
    else setFieldOk(emailInput, emailHint, "");

    if (password.length < 8) { setFieldError(passwordInput, passwordHint, "Password must be at least 8 characters."); hasError = true; }
    else setFieldOk(passwordInput, passwordHint, "");

    if (!validateConfirm()) hasError = true;

    if (!termsInput.checked) { setMessage(registerMessage, "error", "Please accept the Terms."); hasError = true; }

    if (hasError) return;

    state.registering = true;
    setLoading(registerBtn, true);

    const result = await api("/auth/register", { method: "POST", body: { username, email, password } });

    setLoading(registerBtn, false); // Reset loading state!
    state.registering = false;

    if (!result.ok) {
      if (result.fieldErrors && result.fieldErrors.length > 0) {
        const err = result.fieldErrors[0];
        if (err.field === "username") setFieldError(usernameInput, usernameHint, err.message);
        else if (err.field === "email") setFieldError(emailInput, emailHint, err.message);
        else if (err.field === "password") setFieldError(passwordInput, passwordHint, err.message);
        else setMessage(registerMessage, "error", err.message);
      } else {
        setMessage(registerMessage, "error", result.error || "Registration failed.");
      }
      return;
    }

    state.username = username;
    state.email = email;
    state.password = password;
    $("#verifyEmailDisplay").textContent = email;
    $$(".otp-box").forEach((b) => { b.value = ""; b.classList.remove("filled"); });
    $("#otp").value = "";
    setMessage($("#verifyMessage"), "", "");
    goToStep(2);
    startResendCooldown();
  });

  const otpBoxes = $$(".otp-box");
  const otpHidden = $("#otp");

  otpBoxes.forEach((box, idx) => {
    box.addEventListener("input", (e) => {
      const val = e.target.value.replace(/\D/g, "").slice(-1);
      e.target.value = val;
      box.classList.toggle("filled", Boolean(val));
      otpHidden.value = otpBoxes.map((b) => b.value).join("");
      if (val && idx < otpBoxes.length - 1) otpBoxes[idx + 1].focus();
    });
    box.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !box.value && idx > 0) otpBoxes[idx - 1].focus();
    });
  });

  const resendBtn = $("#resendBtn");
  const resendLabel = $("#resendLabel");

  function startResendCooldown() {
    if (state.resendTimer) clearInterval(state.resendTimer);
    let left = 60;
    resendBtn.disabled = true;
    resendLabel.textContent = `Resend in ${left}s`;
    state.resendTimer = setInterval(() => {
      left -= 1;
      if (left <= 0) { clearInterval(state.resendTimer); resendBtn.disabled = false; resendLabel.textContent = "Resend code"; }
      else resendLabel.textContent = `Resend in ${left}s`;
    }, 1000);
  }

  $("#verifyForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (state.verifying) return;
    setMessage($("#verifyMessage"), "", "");
    const otp = otpHidden.value.trim();
    if (!/^\d{6}$/.test(otp)) return setMessage($("#verifyMessage"), "error", "Enter the 6-digit code.");

    state.verifying = true;
    setLoading($("#verifyBtn"), true);
    const result = await api("/auth/verify-email", { method: "POST", body: { email: state.email, otp } });
    
    setLoading($("#verifyBtn"), false); // Reset loading state!
    state.verifying = false;

    if (!result.ok) return setMessage($("#verifyMessage"), "error", result.error || "Invalid code.");
    
    if (state.resendTimer) clearInterval(state.resendTimer);
    goToStep(3);
    setTimeout(() => { window.location.href = "/login?verified=1"; }, 4000);
  });
})();