# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Was ist dieses Projekt?

Ein lokal laufender Signal-Bot für das Ferienhaus **Borgo Batone**.
Der Bot beantwortet Gästefragen automatisch über Signal — vollständig lokal, DSGVO-konform, ohne Cloud-Abhängigkeit.

Betreiber: Sven Friess / autark-AI (autark-ai.de). Das Projekt ist gleichzeitig Showcase für lokale KI in kleinen Betrieben.

---

## Technischer Stack

| Komponente | Detail |
|---|---|
| **Sprache** | Python (conda base environment) |
| **Signal-Anbindung** | signal-cli daemon via Unix Socket (`/tmp/signal-cli-socket`) |
| **KI-Backend** | Ollama (lokal, http://localhost:11434) |
| **Primärmodell** | `mistral:instruct` (Fallback: `granite3.3:2b`, `qwen2.5:7b`) |
| **KB-Editor** | FastAPI + eingebettetes HTML-Frontend (`kb_api.py`, Port 8000) |
| **Laufumgebung** | Mac mini M4, macOS |

---

## Architektur

```
Signal (Gast schreibt !bot ...)
        ↓
signal-cli daemon (Unix Socket /tmp/signal-cli-socket)
        ↓
signal_interface.py  ←→  JSON-RPC subscribeReceive / send
        ↓
borgo_bot_multi.py   ←  Routing nach Signal group_id
        ↓           ↘
  dev_bot          test_bot    community_test_bot
  (BorgoBotInstance je Gruppe)
        ↓
  Pipeline: InputValidator → KeywordExtractor → ContextManager
            → LLMHandler (Ollama) → ResponseFormatter / FallbackSystem
        ↓
Antwort zurück via signal-cli (nur an ursprüngliche Gruppe!)
```

**Wichtig:** Drei logisch getrennte Bot-Instanzen laufen in **einem** Prozess. Routing erfolgt strikt nach Signal-`group_id`. Antworten gehen immer nur an die Gruppe, aus der die Frage kam.

---

## Wichtige Dateien

| Datei | Zweck |
|---|---|
| `borgo_bot_multi.py` | Einstiegspunkt, `BorgoBotInstance`, Message-Loop |
| `config_multi_bot.py` | Zentrale Konfig: Group-IDs, Bot-Configs, alle Konstanten |
| `signal_interface.py` | JSON-RPC-Wrapper für signal-cli daemon |
| `kb_manager.py` | `!kb`-Kommandos für YAML-KB (nur DEV-Gruppe) |
| `kb_api.py` | FastAPI KB-Editor (lokal, Port 8000) |
| `borgo_knowledge_base.yaml` | Wissensbasis (Hausinfos, FAQ) |
| `llm_handler.py` | Ollama-Anfragen, Multi-Model-Fallback, Halluzinations-Erkennung |
| `context_manager.py` | Keyword-basiertes Context-Building aus YAML |
| `fallback_system.py` | Fallback-Antworten wenn LLM versagt |
| `monitoring.py` | Metriken, InteractionLog, `borgo_bot_metrics.json` |
| `message_deduplication.py` | TTL-basierte Dedup (verhindert Doppel-Antworten) |

---

## Services starten

```bash
# 1. signal-cli Daemon starten (Voraussetzung für den Bot)
signal-cli -a +4915755901211 daemon --socket /tmp/signal-cli-socket

# 2. Borgo-Bot starten (alle drei Instanzen in einem Prozess)
./start_all_borgo_bots.sh
# oder direkt:
python3 borgo_bot_multi.py

# 3. KB-Editor starten (optional, für Wissenbasis-Pflege)
python3 kb_api.py   # → http://localhost:8000

# Status prüfen
ollama list                        # Ollama-Modelle
ps aux | grep borgo_bot_multi      # Bot-Prozess
tail -f borgo_bot_multi.log        # Live-Log
```

---

## Group-IDs konfigurieren

Signal-Gruppen-IDs stehen in `config_multi_bot.py` unter `GROUP_IDS`. Beim Start validiert der Bot, dass alle IDs eindeutig sind und keine Platzhalter enthalten. IDs abrufen:

```bash
signal-cli -a +4915755901211 listGroups
```

---

## Bot-Kommandos (in Signal-Gruppen)

| Kommando | Gruppe | Funktion |
|---|---|---|
| `!bot <Frage>` | alle | Bot-Anfrage auslösen |
| `!kb add \| key \| kat \| kw1,kw2 \| Antwort` | nur DEV | KB-Eintrag hinzufügen |
| `!kb edit \| key \| kw1,kw2 \| Neue Antwort` | nur DEV | KB-Eintrag bearbeiten |
| `!kb delete \| key` | nur DEV | KB-Eintrag löschen |
| `!kb list` | nur DEV | Alle Einträge anzeigen |

---

## Coding-Prinzipien

- **Kein Cloud-API-Call** — alles läuft lokal über Ollama
- **DSGVO-konform** — keine Daten verlassen das Gerät
- **Einfach halten** — kein Framework-Overhead
- **Deutsch** — Kommentare, Logs und Bot-Antworten auf Deutsch
- Ollama-Timeouts und LLM-Fehler immer über `FallbackSystem` abfangen
- Antworten nie an eine andere Gruppe als die Ursprungsgruppe senden

---

## Bekannte Eigenheiten

- signal-cli daemon muss laufen, bevor der Bot startet — der Bot wartet und retryt automatisch alle 5 Sekunden
- Bei Modellwechsel immer Antwortqualität prüfen (`borgo_bot_multi.log`)
- `FORBIDDEN_PHRASES` in `config_multi_bot.py` verhindert, dass sich der Bot als KI outet
- `HALLUCINATION_PATTERNS` filtert erfundene Codes, Uhrzeiten, Telefonnummern aus LLM-Antworten heraus
