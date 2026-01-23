#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Borgo Bot v3.2 - Performance Analyzer
======================================

Analysiert die gesammelten Performance-Daten aus der Testphase
und gibt Empfehlungen für die optimale Bot-Konfiguration.

Usage:
    python3 analyze_performance.py logs/borgo_bot.log
"""

import sys
import re
from collections import defaultdict
from datetime import datetime

def parse_log_file(log_path):
    """Parse Log-Datei und extrahiere Performance-Daten."""
    
    data = {
        'signal_times': [],
        'llm_times': [],
        'queue_waits': [],
        'requests': [],
        'errors': defaultdict(int),
        'uptime_hours': 0,
    }
    
    start_time = None
    end_time = None
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Timestamp extrahieren
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if timestamp_match:
                current_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                if start_time is None:
                    start_time = current_time
                end_time = current_time
            
            # Signal-CLI Timings
            signal_match = re.search(r'Signal-CLI: ([\d.]+)s', line)
            if signal_match:
                data['signal_times'].append(float(signal_match.group(1)))
            
            # LLM Timings
            llm_match = re.search(r'Dauer: ([\d.]+)s', line)
            if llm_match and 'LLM-Antwort' in line:
                data['llm_times'].append(float(llm_match.group(1)))
            
            # Queue Wait
            queue_match = re.search(r'Queue-Wait: ([\d.]+)s', line)
            if queue_match:
                data['queue_waits'].append(float(queue_match.group(1)))
            
            # Requests
            if 'Frage erkannt:' in line:
                data['requests'].append(current_time if timestamp_match else None)
            
            # Errors
            if 'Send-Timeout' in line:
                data['errors']['signal_timeout'] += 1
            elif 'LLM-Timeout' in line:
                data['errors']['llm_timeout'] += 1
            elif 'Fehler beim Senden' in line:
                data['errors']['signal_error'] += 1
    
    # Berechne Uptime
    if start_time and end_time:
        uptime = (end_time - start_time).total_seconds() / 3600
        data['uptime_hours'] = uptime
    
    return data


def calculate_stats(values):
    """Berechne Statistiken für eine Liste von Werten."""
    if not values:
        return None
    
    return {
        'count': len(values),
        'min': min(values),
        'max': max(values),
        'avg': sum(values) / len(values),
        'median': sorted(values)[len(values) // 2],
    }


def analyze_peak_times(requests):
    """Analysiere Peak-Zeiten."""
    if not requests:
        return {}
    
    hourly_counts = defaultdict(int)
    for req_time in requests:
        if req_time:
            hourly_counts[req_time.hour] += 1
    
    if not hourly_counts:
        return {}
    
    peak_hour = max(hourly_counts.items(), key=lambda x: x[1])
    return {
        'peak_hour': peak_hour[0],
        'peak_count': peak_hour[1],
        'hourly_distribution': dict(hourly_counts)
    }


def recommend_workers(signal_avg, queue_max, target_wait=1.0):
    """Empfehle Anzahl Worker basierend auf Metriken."""
    
    # Einfache Heuristik
    if queue_max < 0.5:
        return 1, "Kein Bottleneck erkannt"
    elif queue_max < 1.0:
        return 2, "Leichter Bottleneck bei Spitzenzeiten"
    elif queue_max < 2.0:
        workers = max(3, int(signal_avg / target_wait) + 1)
        return workers, "Bottleneck erkannt"
    else:
        workers = max(5, int(signal_avg / target_wait) + 2)
        return workers, "Starker Bottleneck!"


def print_report(data):
    """Drucke detaillierten Performance-Report."""
    
    print("\n" + "="*70)
    print("📊 BORGO BOT v3.2 - PERFORMANCE ANALYSIS REPORT")
    print("="*70)
    
    # Grunddaten
    print(f"\n⏱️  Test-Dauer: {data['uptime_hours']:.1f} Stunden")
    print(f"📨 Total Requests: {len(data['requests'])}")
    
    if data['uptime_hours'] > 0:
        requests_per_hour = len(data['requests']) / data['uptime_hours']
        print(f"📈 Durchschnitt: {requests_per_hour:.1f} Requests/Stunde")
    
    # Signal-CLI Performance
    print("\n" + "-"*70)
    print("📤 SIGNAL-CLI PERFORMANCE")
    print("-"*70)
    
    signal_stats = calculate_stats(data['signal_times'])
    if signal_stats:
        print(f"   Count: {signal_stats['count']}")
        print(f"   Average: {signal_stats['avg']:.2f}s")
        print(f"   Median: {signal_stats['median']:.2f}s")
        print(f"   Min: {signal_stats['min']:.2f}s")
        print(f"   Max: {signal_stats['max']:.2f}s")
        
        # Bewertung
        if signal_stats['avg'] < 2.0:
            print("   ✅ Bewertung: Sehr gut")
        elif signal_stats['avg'] < 3.0:
            print("   ✅ Bewertung: Gut")
        elif signal_stats['avg'] < 5.0:
            print("   ⚠️  Bewertung: Akzeptabel")
        else:
            print("   🚨 Bewertung: Langsam - Netzwerk prüfen!")
    else:
        print("   ⚠️  Keine Daten gefunden")
    
    # LLM Performance
    print("\n" + "-"*70)
    print("🧠 LLM PERFORMANCE")
    print("-"*70)
    
    llm_stats = calculate_stats(data['llm_times'])
    if llm_stats:
        print(f"   Count: {llm_stats['count']}")
        print(f"   Average: {llm_stats['avg']:.2f}s")
        print(f"   Median: {llm_stats['median']:.2f}s")
        print(f"   Min: {llm_stats['min']:.2f}s")
        print(f"   Max: {llm_stats['max']:.2f}s")
        
        # Bewertung
        if llm_stats['avg'] < 3.0:
            print("   ✅ Bewertung: Sehr gut")
        elif llm_stats['avg'] < 4.0:
            print("   ✅ Bewertung: Gut")
        elif llm_stats['avg'] < 6.0:
            print("   ⚠️  Bewertung: Akzeptabel")
        else:
            print("   🚨 Bewertung: Langsam - CPU checken!")
    else:
        print("   ⚠️  Keine Daten gefunden")
    
    # Queue Performance
    print("\n" + "-"*70)
    print("⏳ QUEUE PERFORMANCE")
    print("-"*70)
    
    queue_stats = calculate_stats(data['queue_waits'])
    if queue_stats:
        print(f"   Count: {queue_stats['count']}")
        print(f"   Average: {queue_stats['avg']:.3f}s")
        print(f"   Median: {queue_stats['median']:.3f}s")
        print(f"   Max: {queue_stats['max']:.3f}s")
        
        # Kritische Bewertung
        if queue_stats['max'] < 0.5:
            print("   ✅ Bewertung: Perfekt - 1 Worker ausreichend")
        elif queue_stats['max'] < 1.0:
            print("   ⚠️  Bewertung: Grenzwertig - 2 Worker empfohlen")
        elif queue_stats['max'] < 2.0:
            print("   🚨 Bewertung: Bottleneck - 3+ Worker nötig!")
        else:
            print("   🚨 Bewertung: Starker Bottleneck - 5+ Worker nötig!")
    else:
        print("   ⚠️  Keine Daten gefunden")
    
    # Gesamt-Response-Zeit
    if signal_stats and llm_stats:
        print("\n" + "-"*70)
        print("🎯 GESAMT-RESPONSE-ZEIT")
        print("-"*70)
        
        total_avg = signal_stats['avg'] + llm_stats['avg']
        total_max = signal_stats['max'] + llm_stats['max']
        
        print(f"   Average: {total_avg:.2f}s")
        print(f"   Max: {total_max:.2f}s")
        
        if total_avg < 6.0:
            print("   ✅ Bewertung: Gut - Benutzer warten nicht zu lange")
        elif total_avg < 8.0:
            print("   ⚠️  Bewertung: Akzeptabel - Optimierung möglich")
        else:
            print("   🚨 Bewertung: Zu langsam - Verbesserung nötig!")
    
    # Fehler-Analyse
    print("\n" + "-"*70)
    print("🚨 FEHLER-ANALYSE")
    print("-"*70)
    
    total_errors = sum(data['errors'].values())
    if total_errors > 0:
        print(f"   Total Errors: {total_errors}")
        for error_type, count in data['errors'].items():
            print(f"   - {error_type}: {count}")
        
        if len(data['requests']) > 0:
            error_rate = (total_errors / len(data['requests'])) * 100
            print(f"   Error Rate: {error_rate:.1f}%")
            
            if error_rate < 5:
                print("   ✅ Bewertung: Sehr gut")
            elif error_rate < 10:
                print("   ⚠️  Bewertung: Akzeptabel")
            else:
                print("   🚨 Bewertung: Zu hoch - Problem untersuchen!")
    else:
        print("   ✅ Keine Fehler gefunden - Perfekt!")
    
    # Peak-Zeiten
    peak_data = analyze_peak_times(data['requests'])
    if peak_data:
        print("\n" + "-"*70)
        print("📈 PEAK-ZEITEN ANALYSE")
        print("-"*70)
        
        print(f"   Stärkste Stunde: {peak_data['peak_hour']}:00 Uhr")
        print(f"   Requests in Peak: {peak_data['peak_count']}")
        
        # Top 3 Stunden
        sorted_hours = sorted(
            peak_data['hourly_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        print("\n   Top 3 aktivste Stunden:")
        for hour, count in sorted_hours:
            print(f"   - {hour:02d}:00 Uhr: {count} Requests")
    
    # Worker-Empfehlung
    if signal_stats and queue_stats:
        print("\n" + "="*70)
        print("🎯 EMPFEHLUNGEN")
        print("="*70)
        
        workers, reason = recommend_workers(
            signal_stats['avg'],
            queue_stats['max']
        )
        
        print(f"\n💡 Empfohlene Worker-Anzahl: {workers}")
        print(f"   Grund: {reason}")
        
        if workers == 1:
            print("\n   ✅ Aktuelles Setup ist optimal")
            print("   → Keine Änderung nötig")
        else:
            print(f"\n   ⚠️  Änderung empfohlen:")
            print(f"   → Ändere NUM_WORKERS = {workers} im Bot-Code")
            print(f"   → Erwartete Verbesserung: ~{100 - (100 / workers):.0f}% schneller")
        
        # LLM-Empfehlung
        if llm_stats['avg'] > 4.0:
            print("\n💡 LLM zu langsam:")
            print("   → Teste kleineres Modell: llama3.2:1b")
            print("   → Oder: Mehr CPU-Ressourcen für Ollama")
        
        # Weitere Optimierungen
        print("\n💡 Weitere Optimierungen:")
        if signal_stats['avg'] > 3.0:
            print("   → Signal-CLI Performance prüfen")
            print("   → Netzwerk-Latenz optimieren")
        
        if total_errors > 0:
            print(f"   → Fehlerrate reduzieren (aktuell {total_errors} Fehler)")
    
    print("\n" + "="*70)
    print("✅ Analyse abgeschlossen")
    print("="*70 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_performance.py <log_file>")
        print("Example: python3 analyze_performance.py logs/borgo_bot.log")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    print(f"\n🔍 Analysiere Log-Datei: {log_file}")
    print("Bitte warten...")
    
    try:
        data = parse_log_file(log_file)
        print_report(data)
        
        # Optional: Daten als JSON exportieren
        if '--export' in sys.argv:
            import json
            export_file = 'performance_analysis.json'
            
            # Konvertiere für JSON (datetime nicht serialisierbar)
            export_data = {
                'signal_times': data['signal_times'],
                'llm_times': data['llm_times'],
                'queue_waits': data['queue_waits'],
                'uptime_hours': data['uptime_hours'],
                'total_requests': len(data['requests']),
                'errors': dict(data['errors'])
            }
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"📊 Daten exportiert nach: {export_file}\n")
        
    except FileNotFoundError:
        print(f"❌ Fehler: Datei '{log_file}' nicht gefunden!")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fehler beim Analysieren: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
