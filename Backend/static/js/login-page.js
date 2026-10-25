/* =========================================================
   LOGIN PAGE
========================================================= */
(function () {
    "use strict";

    const API_BASE = "/api/v1";
    const $ = (sel, root = document) => root.querySelector(sel);

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

    async function api(path, { method = "POST", body, headers = {} } = {}) {
        try {
            const res = await fetch(`${API_BASE}${path}`, {
                method,
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json",
                    ...headers,
                },
                body: body ? JSON.stringify(body) : undefined,
            });

            let data = null;
            try { data = await res.json(); } catch { data = null; }

            if (res.ok) return { ok: true, status: res.status, data };

            const message =
                (data && data.error && (data.error.message || data.error.code)) ||
                (data && data.message) ||
                (data && data.error) ||
                `Request failed (${res.status})`;

            return { ok: false, status: res.status, data, error: typeof message === "string" ? message : "Request failed" };
        } catch {
            return { ok: false, status: 0, error: "Network error — could not reach the server." };
        }
    }

    const form = $("#loginForm");
    const loginBtn = $("#loginBtn");
    const messageEl = $("#loginMessage");
    const noticeEl = $("#loginNotice");

    const identifierInput = $("#identifier");
    const passwordInput = $("#password");
    const rememberInput = $("#rememberMe");
    const toggleBtn = $("#togglePassword");
    const forgotBtn = $("#forgotBtn");

    const params = new URLSearchParams(window.location.search);
    
    if (params.get("from")) {
        if (noticeEl) {
            noticeEl.hidden = false;
            noticeEl.textContent = "Please sign in to continue.";
        }
    } else if (params.get("verified") === "1" && noticeEl) {
        noticeEl.hidden = false;
        noticeEl.textContent = "✓ Your email has been verified. Sign in to continue.";
    } else if (params.get("reason") === "logged_out" && noticeEl) {
        noticeEl.hidden = false;
        noticeEl.textContent = "You have been logged out.";
    }

    // Auto-redirect if ALREADY signed in
    (async () => {
        if (params.get("from")) return; // Stop loop if we just got bounced here

        const res = await api("/auth/status", { method: "GET" });
        if (!res.ok || !res.data) return;

        const payload = (res.data.data) || res.data || {};
        if (payload.authenticated === true && payload.user) {
            window.location.replace("/dashboard");
        }
    })();

    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            const show = passwordInput.type === "password";
            passwordInput.type = show ? "text" : "password";
            toggleBtn.textContent = show ? "Hide" : "Show";
        });
    }

    if (forgotBtn) {
        forgotBtn.addEventListener("click", () => {
            // Redirect to the forgot password page
            window.location.href = "/forgot-password";
        });
    }

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            setMessage(messageEl, "", "");

            const identifier = identifierInput.value.trim();
            const password = passwordInput.value;
            const remember = rememberInput.checked;

            if (!identifier || !password) {
                setMessage(messageEl, "error", "Please fill in all fields.");
                return;
            }

            setLoading(loginBtn, true);

            const result = await api("/auth/login", {
                method: "POST",
                body: { identifier, password, remember },
            });

            setLoading(loginBtn, false);

            if (!result.ok) {
                setMessage(messageEl, "error", result.error || "Invalid credentials.");
                return;
            }

            const payload = (result.data && result.data.data) || result.data || {};
            const csrf = payload.csrf_token || "";
            if (csrf) {
                try { sessionStorage.setItem("segmind_csrf_token", csrf); } catch {}
            }

            setMessage(messageEl, "success", "Signed in. Redirecting…");
            setTimeout(() => {
                window.location.href = "/dashboard";
            }, 500);
        });
    }
})();