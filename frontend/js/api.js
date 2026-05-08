// All API calls use relative paths — nginx proxies /auth/, /classes/, /users/ to Flask.
// For local dev without Docker, change this to 'http://localhost:8000'
const API = '';

// ── Auth helpers ──────────────────────────────────────────────────────────────

// Decode JWT payload (public data — no secret needed)
function decodeJwt(token) {
  try {
    const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(b64));
  } catch {
    return null;
  }
}

// Call this after a successful login to persist session data.
// The teammate's login page should call: saveLoginData(data.access_token, enteredName)
function saveLoginData(accessToken, name = '') {
  const payload = decodeJwt(accessToken);
  localStorage.setItem('token', accessToken);
  localStorage.setItem('role', payload?.role ?? '');
  if (name) localStorage.setItem('name', name);
}

function getToken() { return localStorage.getItem('token'); }
function getRole()  { return localStorage.getItem('role'); }
function getName()  { return localStorage.getItem('name') || ''; }
function isLoggedIn() { return !!getToken(); }

function logout() {
  localStorage.clear();
  window.location.href = 'login.html';
}

// Redirect to login if not authenticated. If role is provided, also checks it.
function requireAuth(role = null) {
  if (!isLoggedIn()) {
    window.location.href = 'login.html';
    return false;
  }
  if (role && getRole() !== role) {
    window.location.href = 'classes.html';
    return false;
  }
  return true;
}

// ── Fetch wrapper ─────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(API + path, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) throw new Error(data.message || `Error ${res.status}`);
  return data;
}

// ── Navbar ────────────────────────────────────────────────────────────────────

function renderNav(activePage = '') {
  const role = getRole();
  const loggedIn = isLoggedIn();

  const links = [
    { href: 'classes.html',       label: 'Classes',      page: 'classes',       show: true },
    { href: 'my-classes.html',    label: 'My Classes',   page: 'my-classes',    show: loggedIn && role === 'member' },
    { href: 'create-class.html',  label: 'Create Class', page: 'create-class',  show: loggedIn && role === 'trainer' },
    { href: 'settings.html',      label: 'Settings',     page: 'settings',      show: loggedIn && role === 'member' },
  ];

  const navLinks = links
    .filter(l => l.show)
    .map(l => `<li><a href="${l.href}"${activePage === l.page ? ' class="active"' : ''}>${l.label}</a></li>`)
    .join('');

  const authLink = loggedIn
    ? `<li><button class="btn-logout" onclick="logout()">Logout</button></li>`
    : `<li><a href="login.html">Login</a></li>`;

  const nav = document.createElement('nav');
  nav.className = 'navbar';
  nav.innerHTML = `
    <a href="classes.html" class="navbar-brand">FitClass</a>
    <ul class="navbar-links">${navLinks}${authLink}</ul>
  `;
  document.body.prepend(nav);
}

// ── UI utilities ──────────────────────────────────────────────────────────────

function showMsg(el, text, type = 'error') {
  el.textContent = text;
  el.className = `msg msg-${type}`;
  el.style.display = 'block';
}

function hideMsg(el) {
  el.style.display = 'none';
  el.textContent = '';
}

// Format YYYY-MM-DD to a readable string like "Mon, Jan 5, 2026"
function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
}

// Escape HTML to prevent XSS when inserting user-provided text
function esc(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
