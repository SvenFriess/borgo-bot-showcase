# Borgo-Bot Version History

## Versionierungsschema-Änderung (Januar 2026)

**Von 3.x → 0.x Versionierung gewechselt**

Das alte Schema (3.91) war irreführend und suggerierte Produktionsreife.
Das neue Schema (0.99) zeigt ehrlich den Pre-1.0 Entwicklungsstatus.
Version 1.0 wird erst nach erfolgreichem Community-Test (8.1.2026)
erreicht und folgt damit Semantic Versioning Standards für Pre-Release
Software.

---

## v1.0-rc.2 - KB Fixes & Log-Analyse (2026-04-12)

### 🔍 Log-Analyse (Jan–Apr 2026)
Vollständige Analyse von 432.768 Log-Zeilen aus dem Testbetrieb.

**Ergebnisse:**
- 64 verarbeitete Anfragen, 58 erfolgreich (91%), 6 Fallback (9%)
- Ø Response-Zeit: 12s, Median 12s, Max 25.8s
- 42/64 Anfragen (66%) über 10s → ALERT (Slow Response)
- LLM-Modell: qwen2.5:7b dominant (46x), mistral:instruct nur 8x (konfigurationsabweichung!)
- Restart-Häufung im Februar (bis zu 24x/Tag) → Instabilität signal-cli Socket
- Seit März stabil

**Identifizierte Fallback-Ursachen:**
- `Arztpraxis` (3x): synonyms-Match funktioniert nicht zuverlässig → eigener Entry-Key angelegt
- `Rattengift` (2x): keywords-Feld-Bug → heute behoben
- `Wasser Il Leccio` (1x): fehlende Synonyme → erweitert

### 🐛 Bug: keyword_extractor ignoriert keywords-Feld
**Problem:** Neue KB-Einträge wurden mit `keywords:`-Feld angelegt. Der
`keyword_extractor.py` liest dieses Feld nicht aus — er matcht ausschließlich
auf Entry-Key (lowercase) und `synonyms:`-Feld.
Resultat: `Keywords extracted: High=0, Med=0, Low=0` → Fallback statt Antwort.

**Fix:** Entry-Key von `schaedlingsbekaempfung` → `rattengift` umbenannt,
alle relevanten Begriffe in `synonyms:` verschoben.

**Bekanntes Codeproblem (offen):** `keywords:`-Feld in `keyword_extractor.py`
implementieren ODER Feld aus YAML-Schema und KB-Editor entfernen.

### ✅ KB-Erweiterungen (borgo_knowledge_base.yaml)
**4 neue Einträge** aus OnSite-Chat-Analyse (April 2026):

| Entry-Key | Kategorie | Inhalt |
|---|---|---|
| `rattengift` | safety | Köderboxen Firma Romani, Best Box, Positionen, Abholung |
| `heizung_gabriello` | facilities | Heizzeiten 06-09 + 17-22 Uhr, Thermostat Küchentür |
| `muell_rfid` | rules | RFID-Pflicht ab Mai 2026, ASCIT, neue Tonnen |
| `ausflug_carrara` | activities | Marmotour Michaelangelo, +39 338 783 9855 |

**2 bestehende Einträge erweitert:**

`arztpraxis` — neuer eigener Entry-Key (vorher nur synonym unter `arzt`):
- Behebt 3 Fallbacks aus dem Testbetrieb
- Gleicher Antwort-Inhalt wie `arzt`

`wasser` — Synonyme erweitert:
- Neu: `absperrung`, `sperrwasserhahn`, `wasserabsperrung`, `il leccio`,
  `leccio`, `hauptventil`, `technikraum`
- Behebt Fallback bei Freitext-Query "Wo sind Absperrungen für Wasser am Il Leccio?"

**Gesamtstand KB:** 63 Einträge (vorher 58)

### ⚙️ Config-Empfehlung (offen)
`FUZZY_MATCH_THRESHOLD`: 0.80 → 0.70 senken.
Tippfehler wie `Artzpraxis` (t/z vertauscht) scheitern am aktuellen Threshold.

### 📁 Files Changed
- `borgo_knowledge_base.yaml` — 4 neue Einträge, 2 erweitert, 63 Einträge gesamt
- `config_multi_bot.py` — FUZZY_MATCH_THRESHOLD Anpassung empfohlen (offen)
- `keyword_extractor.py` — keywords-Feld-Integration empfohlen (offen)

### 🚀 Status
**Release Candidate** — Bot läuft stabil, alle bekannten Fallback-Ursachen adressiert.
Bereit für Go Live nach Docker/Hetzner-Migration und DEV-Nummer-Beschaffung.

---

## v1.0-rc.1 - Community-Test abgeschlossen (2026-01-07)

### 🎯 Community-Test Phase beendet
- Testphase mit ausgewählten Mitgliedern erfolgreich abgeschlossen
- Bot beantwortet Fragen zu allen Kernthemen korrekt
- Human-in-the-Loop System für neue KB-Einträge aktiv

### ✅ Fixes & Verbesserungen
- Multi-Bot-Architektur: DEV, TEST, Community-Test parallel aktiv
- Context-Isolation verbessert (MAX_CONTEXT_WORDS ~800)
- Halluzinations-Erkennung validiert
- YAML hot-reload via Watchdog

### 🚀 Status
**Community-Test abgeschlossen** — Rollout an alle 100+ Mitglieder ausstehend

---

## v0.99 - CRITICAL FIX: LLM Response Validation (2026-01-07)

### 🐛 Critical Bug Fixed
**Problem:** LLM-generierte Antworten wurden systematisch abgelehnt
- `is_helpful()` Validierung zu streng: Minimum 20 Zeichen
- Kurze, präzise Antworten wie "1 kg Mehl (Tipo 00)" (19 chars) wurden rejected
- Resultat: Fallback statt echter LLM-Response

### ✅ Comprehensive Fixes

**1. Response Validation (fallback_system.py)**
- `is_helpful()`: Minimum Length von 20 → 10 Zeichen
- Ermöglicht kurze, präzise Antworten

**2. YAML Content Migration (borgo_knowledge_base.yaml)**
- 55 Einträge von `content:` → `answer:` konvertiert
- Bug existierte seit v0.31 (context_manager las 'answer:', YAML hatte 'content:')
- Context Building: 0 words → 164 words

**3. Config Cleanup (config_multi_bot.py)**
- Doppelte FALLBACK_RESPONSES Definition entfernt (Zeile 536-543)
- Verhindert KeyError: 'unknown' bei Fallback-Fehlern

**4. Debug Logging (llm_handler.py)**
- LLM Response Content wird geloggt (erste 500 chars)
- Hilft bei zukünftiger Diagnose von Validierungs-Issues

### 📊 Test Results
```
Query: !Bot Wie viel Mehl für Pizza?
Response: 1 kg Mehl (Tipo 00)
Status: ✅ SUCCESS

Query: !Bot WLAN Passwort?
Response: B3estUs3Cabl3
Status: ✅ SUCCESS

Query: !Bot Pool Regeln?
Response: [Vollständige strukturierte Liste]
Status: ✅ SUCCESS

Query: !Bot Pizzaofen Anleitung?
Response: [Detaillierte Schritt-für-Schritt Anleitung]
Status: ✅ SUCCESS
```

### 🎯 Impact
- **Context Building:** ✅ Funktioniert (164 words statt 0)
- **LLM Generation:** ✅ Generiert korrekte Antworten
- **Response Validation:** ✅ Akzeptiert kurze & lange Antworten
- **Fallback System:** ✅ KeyError behoben

### 📁 Files Changed
- `borgo_knowledge_base.yaml` - 55 field migrations
- `fallback_system.py` - is_helpful() threshold adjusted
- `config_multi_bot.py` - duplicate definition removed
- `llm_handler.py` - enhanced debug logging
- `borgo_bot_community_only.py` - logging.DEBUG enabled

### 🚀 Status
**PRODUCTION READY** - Bot antwortet korrekt auf alle Test-Queries
