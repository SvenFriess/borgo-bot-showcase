"""
kb_api.py - Borgo-Bot Knowledge Base Editor
FastAPI Server mit eingebettetem HTML-Frontend

Start: python3 kb_api.py
URL:   http://localhost:8000

Optional mit ngrok: ngrok http 8000
"""

import logging
import re
from pathlib import Path
from typing import Optional

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import pending_store as ps
from approval_notifier import notify_admin_new_change

# ─── Config ───────────────────────────────────────────────────────────────────

YAML_PATH = Path(__file__).parent / "borgo_knowledge_base.yaml"
PORT = 8000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Borgo-Bot KB Editor", version="1.0")
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="/home/bot/borgo-bot/static"), name="static")

# ─── Models ───────────────────────────────────────────────────────────────────

class KBEntry(BaseModel):
    key: str
    category: str = "general"
    priority: str = "medium"
    synonyms: list[str] = []
    content: str

class KBEntryUpdate(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    synonyms: Optional[list[str]] = None
    content: Optional[str] = None

# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_kb() -> dict:
    if not YAML_PATH.exists():
        raise HTTPException(status_code=500, detail=f"YAML nicht gefunden: {YAML_PATH}")
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_kb(kb: dict) -> None:
    with open(YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(kb, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
    logger.info(f"💾 YAML gespeichert: {YAML_PATH}")

def sanitize_key(key: str) -> str:
    key = key.strip().lower()
    key = re.sub(r"[^a-z0-9_äöüß]", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key

# ─── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/entries")
def get_entries():
    kb = load_kb()
    pending_keys = {c["entry_key"] for c in ps.get_pending()}
    entries = []
    for key, val in kb.items():
        entries.append({
            "key": key,
            "category": val.get("category", "general"),
            "priority": val.get("priority", "medium"),
            "synonyms": val.get("synonyms", []),
            "content": val.get("answer") or val.get("content", ""),
            "_pending": key in pending_keys,
        })
    entries.sort(key=lambda e: (e["category"], e["key"]))
    return {"entries": entries, "total": len(entries)}

@app.get("/api/pending")
def get_pending():
    items = ps.get_pending()
    return {"pending": items, "total": len(items)}

@app.post("/api/entries")
def create_entry(entry: KBEntry):
    key = sanitize_key(entry.key)
    if not key:
        raise HTTPException(status_code=400, detail="Schlüssel darf nicht leer sein")
    kb = load_kb()
    if key in kb:
        raise HTTPException(status_code=409, detail=f"Eintrag '{key}' existiert bereits")
    new_data = {
        "category": entry.category,
        "priority": entry.priority,
        "synonyms": entry.synonyms,
        "answer": entry.content,
    }
    short_id = ps.add_change(
        action="create", entry_key=key,
        new_data=new_data, old_data=None, editor="kb-editor"
    )
    notify_admin_new_change(short_id, "create", key, entry.content[:120])
    return {"status": "pending", "id": short_id, "key": key,
            "message": f"Neuer Eintrag #{short_id} wartet auf Admin-Freigabe"}

@app.put("/api/entries/{key}")
def update_entry(key: str, update: KBEntryUpdate):
    key = sanitize_key(key)
    if not key:
        raise HTTPException(status_code=400, detail="Ungültiger Schlüssel")
    kb = load_kb()
    if key not in kb:
        raise HTTPException(status_code=404, detail=f"Eintrag '{key}' nicht gefunden")
    old_data = dict(kb[key])
    new_data = dict(kb[key])
    if update.category is not None:
        new_data["category"] = update.category
    if update.priority is not None:
        new_data["priority"] = update.priority
    if update.synonyms is not None:
        new_data["synonyms"] = update.synonyms
    if update.content is not None:
        new_data["answer"] = update.content
    short_id = ps.add_change(
        action="update", entry_key=key,
        new_data=new_data, old_data=old_data, editor="kb-editor"
    )
    preview = new_data.get("answer", "")[:120]
    notify_admin_new_change(short_id, "update", key, preview)
    return {"status": "pending", "id": short_id, "key": key,
            "message": f"Änderung #{short_id} wartet auf Admin-Freigabe"}

@app.delete("/api/entries/{key}")
def delete_entry(key: str):
    key = sanitize_key(key)
    if not key:
        raise HTTPException(status_code=400, detail="Ungültiger Schlüssel")
    kb = load_kb()
    if key not in kb:
        raise HTTPException(status_code=404, detail=f"Eintrag '{key}' nicht gefunden")
    old_data = dict(kb[key])
    short_id = ps.add_change(
        action="delete", entry_key=key,
        new_data={}, old_data=old_data, editor="kb-editor"
    )
    notify_admin_new_change(short_id, "delete", key, str(old_data)[:120])
    return {"status": "pending", "id": short_id, "key": key,
            "message": f"Löschung #{short_id} wartet auf Admin-Freigabe"}

@app.get("/api/stats")
def get_stats():
    kb = load_kb()
    by_cat = {}
    for val in kb.values():
        cat = val.get("category", "general")
        by_cat[cat] = by_cat.get(cat, 0) + 1
    return {"total": len(kb), "by_category": by_cat}

# ─── Frontend ─────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Borgo-Bot · Knowledge Base</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --terra: #B85042;
    --terra-dark: #8c3a31;
    --terra-light: #d4756a;
    --sand: #E7E8D1;
    --sand-dark: #d4d5b8;
    --sage: #A7BEAE;
    --sage-dark: #7fa08a;
    --ink: #2c2416;
    --ink-light: #5a4f3f;
    --white: #fdfcf8;
    --shadow: 0 2px 16px rgba(44,36,22,0.10);
    --radius: 10px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--sand);
    color: var(--ink);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* ── Header ── */
  header {
    background: var(--terra);
    color: var(--white);
    padding: 18px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 12px rgba(184,80,66,0.3);
  }
  header h1 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.7rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  header h1 span { opacity: 0.7; font-weight: 400; }
  #stats-bar {
    font-size: 0.82rem;
    opacity: 0.85;
    display: flex;
    gap: 16px;
  }
  #stats-bar b { opacity: 1; }

  /* ── Layout ── */
  .layout {
    display: grid;
    grid-template-columns: 300px 1fr;
    flex: 1;
    height: calc(100vh - 62px);
  }

  /* ── Sidebar ── */
  .sidebar {
    max-height: calc(100vh - 62px);
    height: 100%;
    background: var(--white);
    border-right: 1px solid var(--sand-dark);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .sidebar-top {
    padding: 16px;
    border-bottom: 1px solid var(--sand-dark);
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  #search {
    width: 100%;
    padding: 8px 12px;
    border: 1.5px solid var(--sand-dark);
    border-radius: var(--radius);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    background: var(--sand);
    color: var(--ink);
    outline: none;
    transition: border-color 0.2s;
  }
  #search:focus { border-color: var(--terra); }
  #cat-filter {
    padding: 7px 10px;
    border: 1.5px solid var(--sand-dark);
    border-radius: var(--radius);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    background: var(--sand);
    color: var(--ink);
    outline: none;
    cursor: pointer;
  }
  #cat-filter:focus { border-color: var(--terra); }
  .sidebar-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }
  .entry-item {
    padding: 10px 16px;
    cursor: pointer;
    border-left: 3px solid transparent;
    transition: all 0.15s;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .entry-item:hover { background: var(--sand); border-left-color: var(--terra-light); }
  .entry-item.active { background: #fdf0ee; border-left-color: var(--terra); }
  .entry-key {
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--ink);
  }
  .entry-pending {
    font-size: 0.75rem;
    margin-left: 4px;
    opacity: 0.9;
  }
  .entry-cat {
    font-size: 0.74rem;
    color: var(--ink-light);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .btn-new {
    flex-shrink: 0;
    margin: 12px 16px;
    padding: 10px;
    background: var(--terra);
    color: var(--white);
    border: none;
    border-radius: var(--radius);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
    letter-spacing: 0.02em;
  }
  .btn-new:hover { background: var(--terra-dark); }

  /* ── Editor ── */
  .editor {
    display: flex;
    flex-direction: column;
    background: var(--white);
    overflow: hidden;
  }
  .editor-header {
    padding: 20px 28px 16px;
    border-bottom: 1px solid var(--sand-dark);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }
  .editor-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--terra);
  }
  .editor-actions { display: flex; gap: 10px; }
  .btn {
    padding: 8px 18px;
    border-radius: var(--radius);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: all 0.15s;
  }
  .btn-save { background: var(--sage); color: var(--ink); }
  .btn-save:hover { background: var(--sage-dark); }
  .btn-delete { background: #f5e8e7; color: var(--terra); }
  .btn-delete:hover { background: #f0d0cc; }
  .btn-cancel { background: var(--sand); color: var(--ink-light); }
  .btn-cancel:hover { background: var(--sand-dark); }

  .editor-body {
    flex: 1;
    overflow-y: auto;
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .field-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  label {
    font-size: 0.78rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--ink-light);
  }
  input[type=text], select, textarea {
    width: 100%;
    padding: 10px 14px;
    border: 1.5px solid var(--sand-dark);
    border-radius: var(--radius);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.92rem;
    color: var(--ink);
    background: var(--white);
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  input[type=text]:focus, select:focus, textarea:focus {
    border-color: var(--terra);
    box-shadow: 0 0 0 3px rgba(184,80,66,0.1);
  }
  input[readonly] { background: var(--sand); color: var(--ink-light); cursor: default; }
  textarea {
    resize: vertical;
    min-height: 180px;
    line-height: 1.6;
  }

  /* ── Empty state ── */
  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: var(--ink-light);
    text-align: center;
    padding: 40px;
  }
  .empty-icon { font-size: 3rem; opacity: 0.4; }
  .empty-state h2 { font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; font-weight: 600; }
  .empty-state p { font-size: 0.88rem; opacity: 0.7; }

  /* ── Toast ── */
  #toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 12px 20px;
    border-radius: var(--radius);
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--white);
    box-shadow: var(--shadow);
    opacity: 0;
    transform: translateY(8px);
    transition: all 0.25s;
    pointer-events: none;
    z-index: 1000;
  }
  #toast.show { opacity: 1; transform: translateY(0); }
  #toast.pending { background: #e8a020; }
  #toast.success { background: var(--sage-dark); }
  #toast.error { background: var(--terra); }

  /* ── Confirm dialog ── */
  .overlay {
    display: none;
    position: fixed; inset: 0;
    background: rgba(44,36,22,0.4);
    z-index: 500;
    align-items: center;
    justify-content: center;
  }
  .overlay.show { display: flex; }
  .dialog {
    background: var(--white);
    border-radius: 14px;
    padding: 28px 32px;
    max-width: 360px;
    box-shadow: 0 8px 40px rgba(44,36,22,0.2);
    text-align: center;
  }
  .dialog h3 { font-family: 'Cormorant Garamond', serif; font-size: 1.3rem; margin-bottom: 8px; }
  .dialog p { font-size: 0.88rem; color: var(--ink-light); margin-bottom: 20px; }
  .dialog-btns { display: flex; gap: 10px; justify-content: center; }


  /* ── Mobile Responsive ── */
  @media (max-width: 768px) {
    .layout {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr;
      height: auto;
      min-height: calc(100vh - 62px);
    }
    .sidebar {
      max-height: 45vh;
      height: 45vh;
      border-right: none;
      border-bottom: 1px solid var(--sand-dark);
    }
    .editor {
      min-height: 55vh;
      overflow-y: auto;
    }
    .field-row {
      grid-template-columns: 1fr;
    }
    header {
      padding: 12px 16px;
    }
    header h1 {
      font-size: 1.3rem;
    }
  }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--sand-dark); border-radius: 3px; }
</style>
</head>
<body>

<header>
  <h1>Borgo-Bot <span>· Knowledge Base</span></h1>
  <div id="stats-bar"><span>Einträge: <b id="stat-total">–</b></span></div>
</header>

<div class="layout">
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-top">
      <input id="search" type="text" placeholder="🔍  Suchen…" oninput="filterEntries()">
      <select id="cat-filter" onchange="filterEntries()">
        <option value="">Alle Kategorien</option>
        <option>basics</option><option>facilities</option><option>safety</option>
        <option>rules</option><option>contact</option><option>emergency</option>
        <option>faq</option><option>seasonal</option><option>technical</option><option>general</option>
      </select>
    </div>
    <div id="entry-list" class="sidebar-list"></div>
    <button class="btn-new" onclick="newEntry()">+ Neuer Eintrag</button>
  </aside>

  <!-- Editor -->
  <main class="editor" id="editor-panel">
    <div class="empty-state">
      <div class="empty-icon">🌿</div>
      <h2>Knowledge Base Editor</h2>
      <p>Wähle einen Eintrag aus der Liste<br>oder erstelle einen neuen.</p>
    </div>
  </main>
</div>

<!-- Delete Confirm -->
<div class="overlay" id="confirm-overlay">
  <div class="dialog">
    <h3>Eintrag löschen?</h3>
    <p id="confirm-text">Dieser Eintrag wird dauerhaft gelöscht.</p>
    <div class="dialog-btns">
      <button class="btn btn-cancel" onclick="closeConfirm()">Abbrechen</button>
      <button class="btn btn-delete" onclick="confirmDelete()">Löschen</button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
let allEntries = [];
let currentKey = null;
let isNew = false;
let pendingDeleteKey = null;

// XSS-Schutz: HTML-Sonderzeichen escapen
function esc(str) {
  const d = document.createElement('div');
  d.textContent = str ?? '';
  return d.innerHTML;
}

async function loadEntries() {
  const res = await fetch('/api/entries');
  const data = await res.json();
  allEntries = data.entries;
  document.getElementById('stat-total').textContent = data.total;
  renderList(allEntries);
}

function renderList(entries) {
  const list = document.getElementById('entry-list');
  list.innerHTML = '';
  entries.forEach(e => {
    const div = document.createElement('div');
    const pendingBadge = e._pending ? `<span class="entry-pending">⏳</span>` : '';
    div.className = 'entry-item' + (e.key === currentKey ? ' active' : '');
    div.innerHTML = `<span class="entry-key">${esc(e.key)}</span>${pendingBadge}<span class="entry-cat">${esc(e.category)}</span>`;
    div.dataset.key = e.key;
    div.addEventListener('click', () => openEntry(div.dataset.key));
    list.appendChild(div);
  });
}

function filterEntries() {
  const q = document.getElementById('search').value.toLowerCase();
  const cat = document.getElementById('cat-filter').value;
  const filtered = allEntries.filter(e =>
    (!cat || e.category === cat) &&
    (!q || e.key.includes(q) || e.content.toLowerCase().includes(q) ||
     (e.synonyms || []).some(s => s.includes(q)))
  );
  renderList(filtered);
}

function openEntry(key) {
  currentKey = key;
  isNew = false;
  const e = allEntries.find(x => x.key === key);
  if (!e) return;
  renderEditor(e, false);
  document.querySelectorAll('.entry-item').forEach(el => {
    el.classList.toggle('active', el.querySelector('.entry-key').textContent === key);
  });
}

function newEntry() {
  currentKey = null;
  isNew = true;
  renderEditor({ key:'', category:'general', priority:'medium', synonyms:[], content:'' }, true);
  document.querySelectorAll('.entry-item').forEach(el => el.classList.remove('active'));
}

function renderEditor(e, editable) {
  const panel = document.getElementById('editor-panel');
  // Struktur ohne Userdaten aufbauen, Werte per JS setzen (XSS-sicher)
  panel.innerHTML = `
    <div class="editor-header">
      <div class="editor-title" id="ed-title"></div>
      <div class="editor-actions">
        ${!isNew ? `<button class="btn btn-delete" id="btn-del">Löschen</button>` : ''}
        <button class="btn btn-cancel" onclick="cancelEdit()">Abbrechen</button>
        <button class="btn btn-save" onclick="saveEntry()">Speichern</button>
      </div>
    </div>
    <div class="editor-body">
      <div class="field-row">
        <div class="field-group">
          <label>Schlüssel</label>
          <input type="text" id="f-key" ${!isNew ? 'readonly' : ''} placeholder="z.B. pizzaofen">
        </div>
        <div class="field-group">
          <label>Kategorie</label>
          <select id="f-cat">
            ${['basics','facilities','safety','rules','contact','emergency','faq','seasonal','technical','general']
              .map(c => `<option>${esc(c)}</option>`).join('')}
          </select>
        </div>
      </div>
      <div class="field-row">
        <div class="field-group">
          <label>Keywords / Synonyme</label>
          <input type="text" id="f-syn" placeholder="wlan, wifi, internet">
        </div>
        <div class="field-group">
          <label>Priorität</label>
          <select id="f-prio">
            ${['high','medium','low'].map(p => `<option>${esc(p)}</option>`).join('')}
          </select>
        </div>
      </div>
      <div class="field-group">
        <label>Antworttext</label>
        <textarea id="f-content" placeholder="Antwort für Gäste…"></textarea>
      </div>
    </div>
  `;
  // Werte sicher über DOM-Properties setzen (kein HTML-Parsing)
  document.getElementById('ed-title').textContent = isNew ? 'Neuer Eintrag' : e.key;
  document.getElementById('f-key').value = e.key ?? '';
  document.getElementById('f-syn').value = (e.synonyms || []).join(', ');
  document.getElementById('f-content').value = e.content ?? '';
  // Selects auf korrekten Wert setzen
  const catSel = document.getElementById('f-cat');
  for (const opt of catSel.options) { if (opt.value === e.category) opt.selected = true; }
  const prioSel = document.getElementById('f-prio');
  for (const opt of prioSel.options) { if (opt.value === e.priority) opt.selected = true; }
  // Löschen-Button via data-Attribut (kein inline-onclick mit Userdaten)
  const delBtn = document.getElementById('btn-del');
  if (delBtn) {
    delBtn.dataset.key = e.key;
    delBtn.addEventListener('click', () => askDelete(delBtn.dataset.key));
  }
}

async function saveEntry() {
  const key = document.getElementById('f-key').value.trim();
  const category = document.getElementById('f-cat').value;
  const priority = document.getElementById('f-prio').value;
  const synonyms = document.getElementById('f-syn').value.split(',').map(s=>s.trim()).filter(Boolean);
  const content = document.getElementById('f-content').value.trim();

  if (!key) { toast('Schlüssel darf nicht leer sein', 'error'); return; }
  if (!content) { toast('Antworttext darf nicht leer sein', 'error'); return; }

  try {
    let res;
    if (isNew) {
      res = await fetch('/api/entries', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({key, category, priority, synonyms, content})
      });
    } else {
      res = await fetch(`/api/entries/${currentKey}`, {
        method: 'PUT',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({category, priority, synonyms, content})
      });
    }
    if (!res.ok) {
      const err = await res.json();
      toast(err.detail || 'Fehler', 'error');
      return;
    }
    const result = await res.json();
    if (result.status === 'pending') {
      toast(`⏳ Änderung #${result.id} wartet auf Admin-Freigabe`, 'pending');
    } else {
      toast(isNew ? `✅ "${key}" erstellt` : `✅ "${currentKey}" gespeichert`, 'success');
    }
    await loadEntries();
    if (result.status !== 'pending' || isNew) openEntry(isNew ? key : currentKey);
  } catch(e) {
    toast('Verbindungsfehler', 'error');
  }
}

function askDelete(key) {
  pendingDeleteKey = key;
  // textContent ist XSS-sicher — kein innerHTML nötig
  document.getElementById('confirm-text').textContent = `"${key}" wird dauerhaft gelöscht.`;
  document.getElementById('confirm-overlay').classList.add('show');
}
function closeConfirm() {
  document.getElementById('confirm-overlay').classList.remove('show');
  pendingDeleteKey = null;
}
async function confirmDelete() {
  if (!pendingDeleteKey) return;
  const key = pendingDeleteKey;
  closeConfirm();
  try {
    const res = await fetch(`/api/entries/${key}`, { method: 'DELETE' });
    if (!res.ok) { toast('Fehler beim Löschen', 'error'); return; }
    toast(`🗑️ "${key}" gelöscht`, 'success');
    currentKey = null;
    document.getElementById('editor-panel').innerHTML = `<div class="empty-state"><div class="empty-icon">🌿</div><h2>Eintrag gelöscht</h2><p>Wähle einen Eintrag aus der Liste.</p></div>`;
    await loadEntries();
  } catch(e) { toast('Verbindungsfehler', 'error'); }
}

function cancelEdit() {
  currentKey = null;
  isNew = false;
  document.getElementById('editor-panel').innerHTML = `<div class="empty-state"><div class="empty-icon">🌿</div><h2>Knowledge Base Editor</h2><p>Wähle einen Eintrag aus der Liste<br>oder erstelle einen neuen.</p></div>`;
  document.querySelectorAll('.entry-item').forEach(el => el.classList.remove('active'));
}

let toastTimer;
function toast(msg, type='success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.className = '', 3000);
}

loadEntries();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return HTMLResponse(content=HTML)


# ─── Run ──────────────────────────────────────────────────────────────────────

@app.get("/anleitung", response_class=HTMLResponse)
async def anleitung():
    path = Path(__file__).parent / "kb_editor_anleitung.html"
    return HTMLResponse(content=path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if not YAML_PATH.exists():
        print(f"⚠️  YAML nicht gefunden: {YAML_PATH}")
        print("   Bitte Pfad in kb_api.py anpassen (YAML_PATH)")
    else:
        print(f"✅ YAML gefunden: {YAML_PATH}")

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")

