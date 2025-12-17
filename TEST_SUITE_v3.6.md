# 🧪 Borgo-Bot v3.6 Test Suite

## Quick Validation Tests

Nach Deployment von v3.6 diese Tests durchführen, um sicherzustellen dass alle Fixes funktionieren.

---

## TEST 1: Pool-Konsistenz (KRITISCH)

### Problem in v3.5:
Gleiche Frage "!bot pool technik" lieferte 6+ verschiedene Antworten

### Test-Cases:

```
Test 1.1: Pool-Nutzung (Regeln)
Input:    !bot pool
Expected: Pool-Regeln (Saison Mai-Sept, 8-22 Uhr, VOR Schwimmen duschen, Badekleidung)
Should NOT mention: Filteranlage, Technikraum, Chlor-Dosierung

Test 1.2: Pool-Technikraum
Input:    !bot pool technik
Expected: Technikraum neben Pool, NUR Fachpersonal, Filteranlage/Pumpen/Chlor
Should NOT mention: "kein Pool-System", "historisch", Schwimmregeln

Test 1.3: Synonym "Poolraum"
Input:    !bot poolraum
Expected: Gleiche Antwort wie 1.2 (Technikraum)

Test 1.4: Schwimmen
Input:    !bot schwimmen
Expected: Pool-Regeln (wie 1.1)

Test 1.5: Wasseraufbereitung
Input:    !bot wasseraufbereitung pool
Expected: Technikraum-Info (wie 1.2)
```

### Konsistenz-Check:
- [ ] "!bot pool technik" gibt 3x hintereinander GLEICHE Antwort
- [ ] Keine Halluzinationen ("kein Pool-System")
- [ ] Klare Trennung Nutzung vs Technik

---

## TEST 2: Sicherungskasten (NEU)

### Problem in v3.5:
Fehlinterpretation als "Wertsachen-Safe"

### Test-Cases:

```
Test 2.1: Sicherungskasten
Input:    !bot sicherungskasten
Expected: Elektrische Sicherungen, Standorte, FI-Schalter, Troubleshooting
Should NOT mention: Wertsachen, Safe, Tresor, Diebstahl

Test 2.2: Synonym "Sicherung"
Input:    !bot sicherung
Expected: Gleiche Antwort wie 2.1

Test 2.3: Synonym "FI-Schalter"
Input:    !bot fi-schalter
Expected: Elektrische Sicherungen (sollte matchen)

Test 2.4: Stromausfall Context
Input:    !bot stromausfall was tun
Expected: Sollte Sicherungskasten-Info oder Strom-Entry matchen
```

### Validierung:
- [ ] Keine Erwähnung von Wertgegenständen
- [ ] Praktische Troubleshooting-Steps enthalten
- [ ] Nach-Gewitter-Hinweis enthalten

---

## TEST 3: Bettwäsche (NEU)

### Problem in v3.5:
Keine Antwort

### Test-Cases:

```
Test 3.1: Bettwäsche
Input:    !bot bettwäsche
Expected: Check-in/Check-out Prozedur, Wäschesack, Schrank-Location
Should mention: "Bei Abreise IMMER abziehen"

Test 3.2: Synonym "Laken"
Input:    !bot laken
Expected: Bettwäsche-Info (wie 3.1)

Test 3.3: Synonym "Bettzeug"
Input:    !bot bettzeug
Expected: Bettwäsche-Info (wie 3.1)

Test 3.4: Englisch
Input:    !bot sheets
Expected: Bettwäsche-Info (sollte matchen)
```

### Validierung:
- [ ] Antwort vorhanden (nicht leer)
- [ ] Check-out Hinweis enthalten
- [ ] Keine Verwirrung mit Waschmaschine-Entry

---

## TEST 4: Bot Version/Status (META)

### Problem in v3.5:
"!bot version" gab generische Info statt Bot-Version

### Test-Cases:

```
Test 4.1: Version
Input:    !bot version
Expected: "Version: 3.6", Features-Liste, Knowledge Base Info
Should NOT be: Generische WLAN/Pizza/Müll Übersicht

Test 4.2: Status
Input:    !bot status
Expected: "Version 3.6 | Bereit für deine Fragen" + Themenliste

Test 4.3: Case-Insensitive
Input:    !bot VERSION
Expected: Gleich wie 4.1 (case-insensitive matching sollte funktionieren)
```

### Validierung:
- [ ] "3.6" wird erwähnt
- [ ] Features-Liste vorhanden
- [ ] Kein Generic-Fallback

---

## TEST 5: Ruhezeiten-Konsistenz

### Problem in v3.5:
Mal "20 Uhr", mal "22 Uhr"

### Test-Cases:

```
Test 5.1: Pool-Regeln
Input:    !bot pool regeln
Expected: "Nach 22 Uhr leise sein"
Should NOT say: "20 Uhr"

Test 5.2: Hunde
Input:    !bot hunde
Expected: "Ruhezeiten ab 22 Uhr"

Test 5.3: Allgemeine Regeln
Input:    !bot regeln
Expected: "Ruhezeiten: 22:00 - 08:00 Uhr"
```

### Validierung:
- [ ] ALLE Ruhezeit-Erwähnungen sagen "22:00 Uhr"
- [ ] Keine "20 Uhr" Erwähnungen mehr

---

## TEST 6: Bereits funktionierende Features (Regression-Tests)

Diese sollten weiterhin gut funktionieren:

```
Test 6.1: Schlangen (war perfekt)
Input:    !bot schlangen
Expected: 2 Arten (Zornnatter/Vipern), Verhalten, Krankenhaus Lucca +39 0583 9701

Test 6.2: Waschmaschine (war gut)
Input:    !bot waschmaschine
Expected: Villa Barsotti + Casa Gabriello, PayPal, NUR Oceanwash

Test 6.3: Gastank (war gut)
Input:    !bot gastank
Expected: Technikraum Villa Barsotti, Onsite-Gruppe, Sicherheitshinweise

Test 6.4: Hunde (war gut)
Input:    !bot hunde
Expected: Willkommen, Leine auf Gemeinschaftsflächen, Reinigung nach Aufenthalt

Test 6.5: Wasser-Problem (war gut)
Input:    !bot kein wasser dusche
Expected: Vorlaufzeit, Hauptventil prüfen, Onsite-Gruppe
```

### Validierung:
- [ ] Alle bisherigen guten Antworten bleiben unverändert
- [ ] Keine Regression durch neue Entries

---

## STRESS-TEST: Konsistenz über Zeit

```
Wiederhole 5x hintereinander:
!bot pool technik

Erwartung:
→ Alle 5 Antworten sollten identisch oder nahezu identisch sein
→ KEINE Halluzinationen
→ KEINE "kein Pool-System" Aussagen
```

---

## SCHNELL-CHECK (1 Minute)

Für schnelles Deployment-Verification:

```bash
# Diese 5 Commands nacheinander:
!bot status           # → Sollte "3.6" zeigen
!bot pool             # → Regeln (Nutzung)
!bot pool technik     # → Technikraum
!bot sicherungskasten # → Elektro (NICHT Wertsachen)
!bot bettwäsche       # → Info vorhanden
```

✅ Wenn alle 5 korrekt antworten → Deployment OK  
❌ Wenn einer fehlschlägt → Checke Logs & YAML-Syntax

---

## LOGGING & DEBUGGING

### Bei Fehlern prüfen:

1. **Keywords extracted:**
   ```
   Log sollte zeigen:
   "pool" + "technik" → Sollte pool_technikraum matchen
   "pool" solo → Sollte pool_nutzung matchen
   ```

2. **Context verwendet:**
   ```
   Sollte zeigen:
   context_entries = 1 (nur ein Entry matched)
   NICHT: context_entries = 3 (Duplikate!)
   ```

3. **Hallucination-Check:**
   ```
   Sollte KEINE Warnings zeigen für:
   - "historisch"
   - "kein Pool-System"
   ```

---

## PERFORMANCE TRACKING

### Metriken sammeln (optional):

```python
# Über 20 Test-Queries tracken:
- Average response time (Target: < 6 Sekunden)
- Hallucination rate (Target: 0%)
- Consistency rate (Target: 100% für gleiche Frage)
- Fallback rate (Target: < 5%)
```

---

## COMMUNITY-ROLLOUT TEST

### Nach Initial-Validation:

1. **Ankündigung posten** (siehe CHANGELOG)

2. **First 24h Monitoring:**
   - Alle Pool-Fragen im Chat beobachten
   - Neue Entry-Usage tracken (Sicherungskasten, Bettwäsche)
   - Unerwartete Fallbacks notieren

3. **Feedback sammeln:**
   - Was funktioniert besser als vorher?
   - Welche Fragen werden jetzt nicht mehr gestellt? (= Bot beantwortet sie!)
   - Neue Content-Gaps identifiziert?

---

## SUCCESS CRITERIA

### v3.6 ist erfolgreich deployed wenn:

- [x] Pool-Fragen 100% konsistent (keine Halluzinationen)
- [x] Sicherungskasten gibt Elektro-Info (nicht Wertsachen)
- [x] Bettwäsche-Frage wird beantwortet
- [x] "!bot version" zeigt 3.6
- [x] Ruhezeiten überall 22:00 Uhr
- [x] Keine Regression bei bisherigen guten Entries
- [x] Community-Feedback positiv

---

## ROLLBACK-PLAN

Falls v3.6 Probleme macht:

```bash
# Zurück zu v3.5:
cp borgo_knowledge_base_v3.5_backup.yaml borgo_knowledge_base.yaml

# Config zurück:
BOT_VERSION = "3.5"

# Bot neu starten:
systemctl restart borgo-bot

# In Community posten:
"Kurze Probleme mit v3.6 - zurück auf v3.5 für Stabilität.
Fix kommt bald! 🔧"
```

---

**Test Suite Version:** 3.6  
**Last Updated:** 17. Dezember 2024  
**Test Coverage:** 25+ Test Cases  
**Estimated Test Time:** 15-20 Minuten (komplett), 1 Min (Quick-Check)
