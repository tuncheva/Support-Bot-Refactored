// client-side chat UI logic 

function qs(sel) {
  return document.querySelector(sel);
}

function setHidden(el, hidden) {
  if (!el) return;
  el.hidden = hidden;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

function addBubble({ role, text, ts, debug }) {
  const chat = qs('#chat');
  if (!chat) return;

  // Remove empty state if present.
  const empty = chat.querySelector('.empty');
  if (empty) empty.remove();

  const row = document.createElement('div');
  row.className = `bubble-row ${role === 'user' ? 'bubble-row--user' : 'bubble-row--bot'}`;

  const bubble = document.createElement('div');
  bubble.className = `bubble ${role === 'user' ? 'bubble--user' : 'bubble--bot'}`;

  const textEl = document.createElement('div');
  textEl.className = 'bubble__text';
  textEl.innerHTML = escapeHtml(text);
  bubble.appendChild(textEl);

  if (debug) {
    const pre = document.createElement('pre');
    pre.className = 'bubble__debug';
    pre.textContent = JSON.stringify(debug, null, 2);
    bubble.appendChild(pre);
  }

  const meta = document.createElement('div');
  meta.className = 'bubble__meta';
  meta.textContent = ts || '';
  bubble.appendChild(meta);

  row.appendChild(bubble);
  chat.appendChild(row);

  // auto-scroll
  chat.scrollTop = chat.scrollHeight;
}

async function postJson(url, body, { timeoutMs = 45000 } = {}) {

  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data && data.error ? data.error : `Request failed (${res.status})`;
      throw new Error(msg);
    }
    return data;
  } catch (err) {
    if (err && err.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.');
    }
    throw err;
  } finally {
    clearTimeout(t);
  }
}

function showError(message) {
  const err = qs('#error');
  if (!err) return;
  err.textContent = message;
  setHidden(err, false);
}

function clearError() {
  const err = qs('#error');
  if (!err) return;
  err.textContent = '';
  setHidden(err, true);
}

function setLoading(loading) {
  const loadingEl = qs('#loading');
  const sendBtn = qs('#sendBtn');
  const input = qs('#messageInput');

  // Default: hidden
  setHidden(loadingEl, !loading);

  // Defensive: if CSS/HTML gets out of sync, force-hide by inline style too.
  if (loadingEl) {
    loadingEl.style.display = loading ? '' : 'none';
  }

  if (sendBtn) sendBtn.disabled = loading;
  if (input) input.disabled = loading;
}

function init() {
  const form = qs('#composer');
  const input = qs('#messageInput');
  const clearBtn = qs('#clearBtn');
  const debugToggle = qs('#debugToggle');
  const themeToggle = qs('#themeToggle');
  const chat = qs('#chat');

  if (chat) chat.scrollTop = chat.scrollHeight;

  // Ensure we never load with a stuck "Thinking…" indicator.
  setLoading(false);

  // Theme toggle
  const savedTheme = localStorage.getItem('theme') || 'light';
  if (savedTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    if (themeToggle) themeToggle.checked = true;
  }

  if (themeToggle) {
    themeToggle.addEventListener('change', () => {
      const theme = themeToggle.checked ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
    });
  }

  if (form && input) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearError();

      const message = (input.value || '').trim();
      if (!message) return;

      const debug = !!(debugToggle && debugToggle.checked);

      addBubble({ role: 'user', text: message, ts: new Date().toISOString() });
      input.value = '';
      setLoading(true);

      try {
        const data = await postJson('/api/chat', { message, debug });
        const replyText = (data && typeof data.reply === 'string') ? data.reply : '';
        if (!replyText) {
          throw new Error('No reply received from server.');
        }
        addBubble({
          role: 'bot',
          text: replyText,
          ts: new Date().toISOString(),
          debug: data.debug,
        });
      } catch (err) {
        showError(err && err.message ? err.message : String(err));
      } finally {
        setLoading(false);
        input.focus();
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
      clearError();
      setLoading(true);
      try {
        await postJson('/api/clear', {});
        window.location.reload();
      } catch (err) {
        showError(err.message || String(err));
        setLoading(false);
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', init);
