/* =========================================================
   FORGOT PASSWORD WIZARD
========================================================= */
(function () {
  "use strict";

  const API_BASE = "/api/v1";
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const state = {
    email: "",
    reset_token: "",
    verifying: false,
    resetting: false,
    sending: false
  };

  /* ---------------------------------------------------------
     HELPERS
  --------------------------------------------------------- */
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
      
      const message = (data && data.message) || `Request failed (${res.status})`;
      return { ok: false, status: res.status, data, error: message };
    } catch {
      return { ok: false, status: 0, error: "Network error — could not reach the server." };
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

  function goToStep(n) {
    $$(".form-step").forEach((el) => el.classList.toggle("active", Number(el.dataset.panel) === n));
    $$(".step-ind").forEach((el) => {
      const num = Number(el.dataset.step);
      el.classList.toggle("active", num === n);
      el.classList.toggle("done", num < n);
    });
    const active = $(".form-step.active");
    const firstField = active && active.querySelector("input, button");
    if (firstField) setTimeout(() => firstField.focus(), 60);
  }

  // Password strength meter logic
  function scorePassword(pw) {
    let s = 0;
    if (pw.length >= 8) s++;
    if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) s++;
    if (/\d/.test(pw)) s++;
    if (/[^A-Za-z0-9]/.test(pw)) s++;
    return s;
  }

  /* ---------------------------------------------------------
     STEP 1 — SEND OTP
  --------------------------------------------------------- */
  const emailForm = $("#emailForm");
  const emailBtn = $("#emailBtn");
  const emailMessage = $("#emailMessage");
  const emailInput = $("#email");

  emailForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (state.sending) return;
    setMessage(emailMessage, "", "");

    const email = emailInput.value.trim();
    if (!email) {
      setMessage(emailMessage, "error", "Enter your email address.");
      return;
    }

    state.sending = true;
    setLoading(emailBtn, true);

    const result = await api("/auth/forgot-password", {
      method: "POST",
      body: { email },
    });

    setLoading(emailBtn, false);
    state.sending = false;

    if (!result.ok) {
      setMessage(emailMessage, "error", result.error || "Could not send reset code.");
      return;
    }

    state.email = email;
    $("#verifyEmailDisplay").textContent = email;
    $$(".otp-box").forEach((b) => { b.value = ""; b.classList.remove("filled"); });
    $("#otp").value = "";
    
    goToStep(2);
  });

  /* ---------------------------------------------------------
     STEP 2 — VERIFY OTP
  --------------------------------------------------------- */
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

  const otpForm = $("#otpForm");
  const otpBtn = $("#otpBtn");
  const otpMessage = $("#otpMessage");

  otpForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (state.verifying) return;
    setMessage(otpMessage, "", "");

    const otp = otpHidden.value.trim();
    if (!/^\d{6}$/.test(otp)) {
      setMessage(otpMessage, "error", "Enter the 6-digit code from your email.");
      return;
    }

    state.verifying = true;
    setLoading(otpBtn, true);

    const result = await api("/auth/verify-reset-otp", {
      method: "POST",
      body: { email: state.email, otp },
    });

    setLoading(otpBtn, false);
    state.verifying = false;

    if (!result.ok) {
      setMessage(otpMessage, "error", result.error || "Invalid or expired code.");
      return;
    }

    // Capture the reset token safely
    const payload = (result.data && result.data.data) || result.data || {};
    if (payload.reset_token) {
      state.reset_token = payload.reset_token;
    } else if (result.data.reset_token) {
      state.reset_token = result.data.reset_token;
    } else {
      setMessage(otpMessage, "error", "Server error: Reset token missing from response.");
      return;
    }

    console.log("✅ Reset Token captured:", state.reset_token);
    goToStep(3);
  });

  $("#backToStep1").addEventListener("click", () => {
    setMessage(otpMessage, "", "");
    goToStep(1);
  });

  /* ---------------------------------------------------------
     STEP 3 — RESET PASSWORD
  --------------------------------------------------------- */
  const resetForm = $("#resetForm");
  const resetBtn = $("#resetBtn");
  const resetMessage = $("#resetMessage");
  const newPasswordInput = $("#newPassword");
  const confirmInput = $("#confirmPassword");
  const pwMeter = $("#pwMeter");
  const togglePasswordBtn = $("#togglePassword");

  newPasswordInput.addEventListener("input", () => {
    const score = scorePassword(newPasswordInput.value);
    pwMeter.dataset.strength = String(score);
  });

  togglePasswordBtn.addEventListener("click", () => {
    const show = newPasswordInput.type === "password";
    newPasswordInput.type = show ? "text" : "password";
    togglePasswordBtn.textContent = show ? "Hide" : "Show";
  });

  resetForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (state.resetting) return;
    setMessage(resetMessage, "", "");

    const new_password = newPasswordInput.value;
    const confirm = confirmInput.value;

    // --- FRONTEND VALIDATION (Matches your backend rules) ---
    if (new_password.length < 8) {
      setMessage(resetMessage, "error", "Password must be at least 8 characters.");
      return;
    }
    if (!/[A-Z]/.test(new_password)) {
      setMessage(resetMessage, "error", "Password must contain at least one uppercase letter.");
      return;
    }
    if (!/[a-z]/.test(new_password)) {
      setMessage(resetMessage, "error", "Password must contain at least one lowercase letter.");
      return;
    }
    if (!/\d/.test(new_password)) {
      setMessage(resetMessage, "error", "Password must contain at least one number.");
      return;
    }
    // Check for special character (matches backend SPECIAL_CHAR_REGEX)
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]/.test(new_password)) {
      setMessage(resetMessage, "error", "Password must contain at least one special character (e.g., !@#$%^&*).");
      return;
    }
    if (new_password !== confirm) {
      setMessage(resetMessage, "error", "Passwords do not match.");
      return;
    }
    // ---------------------------------------------------------

    state.resetting = true;
    setLoading(resetBtn, true);

    const result = await api("/auth/reset-password", {
      method: "POST",
      body: { reset_token: state.reset_token, new_password },
    });

    setLoading(resetBtn, false);
    state.resetting = false;

    if (!result.ok) {
      setMessage(resetMessage, "error", result.error || "Failed to reset password.");
      return;
    }

    goToStep(4);
  });

})();