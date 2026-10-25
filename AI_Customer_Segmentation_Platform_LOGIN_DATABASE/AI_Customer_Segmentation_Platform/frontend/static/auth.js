async function logoutUser() {
  try { await fetch("/logout", { method: "POST", credentials: "same-origin" }); }
  finally { window.location.href = "/login"; }
}
document.addEventListener("DOMContentLoaded", async () => {
  const welcome = document.getElementById("welcomeUser");
  if (!welcome) return;
  try {
    const response = await fetch("/api/me", { credentials: "same-origin" });
    if (response.status === 401) { window.location.href = "/login"; return; }
    const user = await response.json();
    welcome.textContent = user.name ? `Welcome, ${user.name}` : "Welcome";
  } catch (_) { welcome.textContent = "Welcome"; }
});
