"""
Borgo-Bot v3.5 - Monitoring System
Phase 6: Performance-Tracking, Logging und Alerting
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from collections import defaultdict, deque
from dataclasses import dataclass, asdict

from config import (
    LOG_LEVEL,
    LOG_FILE,
    TRACK_METRICS,
    ALERT_THRESHOLDS
)

logger = logging.getLogger(__name__)


@dataclass
class InteractionLog:
    """Repräsentiert eine einzelne Bot-Interaktion"""
    timestamp: str
    query: str
    query_length: int
    keywords_found: List[str]
    keywords_confidence: str
    context_entries: int
    context_words: int
    model_used: Optional[str]
    response_length: int
    response_time_ms: float
    validation_issues: List[str]
    fallback_used: bool
    fallback_reason: Optional[str]
    success: bool


class MonitoringSystem:
    """
    Überwacht Bot-Performance und Qualität
    Tracked Metriken, detektiert Probleme, sendet Alerts
    """
    
    def __init__(self, metrics_file: str = "borgo_bot_metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.session_start = datetime.now()
        
        # Real-time Metrics
        self.metrics = {
            'total_interactions': 0,
            'successful_interactions': 0,
            'failed_interactions': 0,
            'total_response_time_ms': 0,
            'avg_response_time_ms': 0,
            'keywords_found_rate': 0,
            'fallback_rate': 0,
            'validation_failure_rate': 0,
        }
        
        # Detailed Tracking
        self.interactions: deque = deque(maxlen=1000)  # Letzte 1000 Interactions
        self.hourly_stats: Dict = defaultdict(lambda: {
            'interactions': 0,
            'failures': 0,
            'avg_response_time': 0
        })
        
        # Alert-Tracking
        self.alerts_sent = []
        self.last_alert_time = {}
        
        # Performance-Fenster (letzte 10 Interactions für schnelle Checks)
        self.recent_response_times = deque(maxlen=10)
    
    def log_interaction(self, log_entry: InteractionLog):
        """
        Logged eine Bot-Interaktion
        
        Args:
            log_entry: InteractionLog Objekt
        """
        self.interactions.append(log_entry)
        self._update_metrics(log_entry)
        self._check_for_alerts(log_entry)
        
        # Speichere periodisch
        if self.metrics['total_interactions'] % 10 == 0:
            self._save_metrics()
        
        logger.info(f"📊 Interaction logged: {log_entry.query[:50]}... "
                   f"(Success: {log_entry.success}, Time: {log_entry.response_time_ms:.0f}ms)")
    
    def _update_metrics(self, log_entry: InteractionLog):
        """Updated Metriken basierend auf neuem Log"""
        self.metrics['total_interactions'] += 1
        
        if log_entry.success:
            self.metrics['successful_interactions'] += 1
        else:
            self.metrics['failed_interactions'] += 1
        
        # Response Time
        self.metrics['total_response_time_ms'] += log_entry.response_time_ms
        self.metrics['avg_response_time_ms'] = (
            self.metrics['total_response_time_ms'] / 
            self.metrics['total_interactions']
        )
        self.recent_response_times.append(log_entry.response_time_ms)
        
        # Rates
        total = self.metrics['total_interactions']
        self.metrics['keywords_found_rate'] = (
            sum(1 for i in self.interactions if i.keywords_found) / 
            len(self.interactions) * 100
        ) if self.interactions else 0
        
        self.metrics['fallback_rate'] = (
            sum(1 for i in self.interactions if i.fallback_used) / 
            len(self.interactions) * 100
        ) if self.interactions else 0
        
        self.metrics['validation_failure_rate'] = (
            sum(1 for i in self.interactions if i.validation_issues) / 
            len(self.interactions) * 100
        ) if self.interactions else 0
        
        # Hourly Stats
        hour_key = datetime.now().strftime("%Y-%m-%d %H:00")
        self.hourly_stats[hour_key]['interactions'] += 1
        if not log_entry.success:
            self.hourly_stats[hour_key]['failures'] += 1
        
        # Update avg response time for this hour
        hour_interactions = [
            i for i in self.interactions 
            if i.timestamp.startswith(hour_key.split()[0])
        ]
        if hour_interactions:
            self.hourly_stats[hour_key]['avg_response_time'] = (
                sum(i.response_time_ms for i in hour_interactions) / 
                len(hour_interactions)
            )
    
    def _check_for_alerts(self, log_entry: InteractionLog):
        """
        Prüft ob Alerts gesendet werden sollen
        Verhindert Alert-Spam durch Cooldown
        """
        alerts = []
        
        # Alert 1: Langsame Response
        if (TRACK_METRICS.get('query_processing_time') and
            log_entry.response_time_ms > ALERT_THRESHOLDS['slow_response_seconds'] * 1000):
            alerts.append({
                'type': 'slow_response',
                'message': f"Slow response: {log_entry.response_time_ms:.0f}ms",
                'severity': 'warning'
            })
        
        # Alert 2: Hohe Fehlerrate (letzte 10 Interactions)
        recent = list(self.interactions)[-10:]
        if len(recent) >= 10:
            error_rate = sum(1 for i in recent if not i.success) / len(recent) * 100
            if error_rate > ALERT_THRESHOLDS['high_error_rate_percent']:
                alerts.append({
                    'type': 'high_error_rate',
                    'message': f"High error rate: {error_rate:.1f}% in last 10 interactions",
                    'severity': 'critical'
                })
        
        # Alert 3: Halluzinationen häufen sich
        hour_key = datetime.now().strftime("%Y-%m-%d %H")
        recent_hour = [
            i for i in self.interactions 
            if i.timestamp.startswith(hour_key)
        ]
        hallucination_count = sum(
            1 for i in recent_hour 
            if any('hallucination' in issue.lower() for issue in i.validation_issues)
        )
        if hallucination_count >= ALERT_THRESHOLDS['hallucination_count_per_hour']:
            alerts.append({
                'type': 'hallucination_spike',
                'message': f"Hallucination spike: {hallucination_count} in last hour",
                'severity': 'critical'
            })
        
        # Sende Alerts (mit Cooldown)
        for alert in alerts:
            self._send_alert(alert)
    
    def _send_alert(self, alert: Dict):
        """
        Sendet Alert
        Implementiert Cooldown um Spam zu vermeiden
        """
        alert_type = alert['type']
        now = datetime.now()
        
        # Check Cooldown (5 Minuten)
        if alert_type in self.last_alert_time:
            time_since_last = now - self.last_alert_time[alert_type]
            if time_since_last < timedelta(minutes=5):
                logger.debug(f"Alert cooldown active for {alert_type}")
                return
        
        # Sende Alert
        alert['timestamp'] = now.isoformat()
        self.alerts_sent.append(alert)
        self.last_alert_time[alert_type] = now
        
        # Log mit entsprechendem Level
        log_func = logger.critical if alert['severity'] == 'critical' else logger.warning
        log_func(f"🚨 ALERT: {alert['message']}")
        
        # Hier könnte man z.B. E-Mails, Slack-Nachrichten etc. senden
        # self._send_email_alert(alert)
        # self._send_slack_alert(alert)
    
    def get_metrics(self) -> Dict:
        """Gibt aktuelle Metriken zurück"""
        uptime = datetime.now() - self.session_start
        
        return {
            **self.metrics,
            'session_uptime_seconds': uptime.total_seconds(),
            'session_start': self.session_start.isoformat(),
            'alerts_sent_count': len(self.alerts_sent),
            'recent_avg_response_time_ms': (
                sum(self.recent_response_times) / len(self.recent_response_times)
                if self.recent_response_times else 0
            )
        }
    
    def get_hourly_report(self, hours: int = 24) -> Dict:
        """
        Gibt stündlichen Report zurück
        
        Args:
            hours: Anzahl Stunden zurück
        
        Returns:
            Dict mit stündlichen Statistiken
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        relevant_stats = {
            hour: stats 
            for hour, stats in self.hourly_stats.items()
            if datetime.fromisoformat(hour.replace(' ', 'T')) >= cutoff
        }
        
        return relevant_stats
    
    def get_problem_patterns(self) -> Dict:
        """
        Analysiert Interactions und findet Problem-Patterns
        
        Returns:
            Dict mit erkannten Patterns
        """
        patterns = {
            'most_failed_queries': [],
            'slowest_queries': [],
            'most_common_fallback_reasons': defaultdict(int),
            'most_common_validation_issues': defaultdict(int),
        }
        
        # Gescheiterte Queries
        failed = [i for i in self.interactions if not i.success]
        if failed:
            query_failures = defaultdict(int)
            for interaction in failed:
                query_failures[interaction.query] += 1
            
            patterns['most_failed_queries'] = sorted(
                query_failures.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        
        # Langsame Queries
        slow_threshold = ALERT_THRESHOLDS['slow_response_seconds'] * 1000
        slow = [i for i in self.interactions if i.response_time_ms > slow_threshold]
        if slow:
            patterns['slowest_queries'] = [
                (i.query[:50], i.response_time_ms)
                for i in sorted(slow, key=lambda x: x.response_time_ms, reverse=True)[:5]
            ]
        
        # Fallback-Gründe
        for interaction in self.interactions:
            if interaction.fallback_reason:
                patterns['most_common_fallback_reasons'][interaction.fallback_reason] += 1
        
        # Validation Issues
        for interaction in self.interactions:
            for issue in interaction.validation_issues:
                patterns['most_common_validation_issues'][issue] += 1
        
        return patterns
    
    def _save_metrics(self):
        """Speichert Metriken zu JSON-File"""
        try:
            data = {
                'metrics': self.get_metrics(),
                'hourly_stats': dict(self.hourly_stats),
                'recent_interactions': [
                    asdict(i) for i in list(self.interactions)[-100:]
                ],
                'alerts': self.alerts_sent,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Metrics saved to {self.metrics_file}")
        
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def load_metrics(self) -> bool:
        """Lädt Metriken von File"""
        try:
            if not self.metrics_file.exists():
                logger.info("No previous metrics file found")
                return False
            
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Lade Daten
            if 'hourly_stats' in data:
                self.hourly_stats = defaultdict(
                    lambda: {'interactions': 0, 'failures': 0, 'avg_response_time': 0},
                    data['hourly_stats']
                )
            
            if 'alerts' in data:
                self.alerts_sent = data['alerts']
            
            logger.info(f"Metrics loaded from {self.metrics_file}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            return False
    
    def generate_summary_report(self) -> str:
        """Generiert textuellen Summary-Report"""
        metrics = self.get_metrics()
        problems = self.get_problem_patterns()
        
        report_lines = [
            "=" * 70,
            "BORGO-BOT MONITORING REPORT",
            "=" * 70,
            "",
            f"Session Start: {metrics['session_start']}",
            f"Uptime: {metrics['session_uptime_seconds']:.0f}s",
            "",
            "## INTERACTIONS ##",
            f"Total: {metrics['total_interactions']}",
            f"Successful: {metrics['successful_interactions']} "
            f"({metrics['successful_interactions']/metrics['total_interactions']*100:.1f}%)" 
            if metrics['total_interactions'] > 0 else "N/A",
            f"Failed: {metrics['failed_interactions']} "
            f"({metrics['failed_interactions']/metrics['total_interactions']*100:.1f}%)"
            if metrics['total_interactions'] > 0 else "N/A",
            "",
            "## PERFORMANCE ##",
            f"Avg Response Time: {metrics['avg_response_time_ms']:.0f}ms",
            f"Recent Avg: {metrics['recent_avg_response_time_ms']:.0f}ms",
            "",
            "## QUALITY ##",
            f"Keywords Found Rate: {metrics['keywords_found_rate']:.1f}%",
            f"Fallback Rate: {metrics['fallback_rate']:.1f}%",
            f"Validation Failure Rate: {metrics['validation_failure_rate']:.1f}%",
            "",
            "## ALERTS ##",
            f"Total Alerts Sent: {metrics['alerts_sent_count']}",
        ]
        
        # Add recent alerts
        if self.alerts_sent:
            report_lines.append("")
            report_lines.append("Recent Alerts:")
            for alert in self.alerts_sent[-5:]:
                report_lines.append(f"  [{alert['severity'].upper()}] {alert['message']}")
        
        # Add problem patterns
        if problems['most_failed_queries']:
            report_lines.append("")
            report_lines.append("## PROBLEM PATTERNS ##")
            report_lines.append("Most Failed Queries:")
            for query, count in problems['most_failed_queries']:
                report_lines.append(f"  {count}x: {query[:50]}")
        
        report_lines.append("")
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)


# ========================================
# TESTS
# ========================================

def test_monitoring():
    """Test-Suite für Monitoring System"""
    
    monitor = MonitoringSystem("test_metrics.json")
    
    print("=" * 70)
    print("MONITORING SYSTEM TESTS")
    print("=" * 70)
    
    # Simuliere verschiedene Interactions
    test_interactions = [
        # Erfolgreiche Interaktionen
        InteractionLog(
            timestamp=datetime.now().isoformat(),
            query="Wie viel Mehl für Pizza?",
            query_length=25,
            keywords_found=['pizza', 'pizzaofen'],
            keywords_confidence='high',
            context_entries=2,
            context_words=150,
            model_used='mistral:7b-instruct',
            response_length=120,
            response_time_ms=3500,
            validation_issues=[],
            fallback_used=False,
            fallback_reason=None,
            success=True
        ),
        # Gescheiterte Interaktion
        InteractionLog(
            timestamp=datetime.now().isoformat(),
            query="Blablabla nonsense",
            query_length=17,
            keywords_found=[],
            keywords_confidence='none',
            context_entries=0,
            context_words=0,
            model_used=None,
            response_length=80,
            response_time_ms=500,
            validation_issues=[],
            fallback_used=True,
            fallback_reason='no_keywords',
            success=False
        ),
        # Langsame Interaktion (Alert!)
        InteractionLog(
            timestamp=datetime.now().isoformat(),
            query="Sind Hunde erlaubt?",
            query_length=19,
            keywords_found=['hunde'],
            keywords_confidence='high',
            context_entries=1,
            context_words=100,
            model_used='mistral:7b-instruct',
            response_length=200,
            response_time_ms=15000,  # 15 Sekunden!
            validation_issues=[],
            fallback_used=False,
            fallback_reason=None,
            success=True
        ),
    ]
    
    # Logge Interactions
    print("\n### Logging Interactions ###\n")
    for interaction in test_interactions:
        monitor.log_interaction(interaction)
        print(f"Logged: {interaction.query[:30]}... "
              f"(Success: {interaction.success}, Time: {interaction.response_time_ms:.0f}ms)")
    
    # Metriken
    print("\n### Current Metrics ###\n")
    metrics = monitor.get_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # Problem Patterns
    print("\n### Problem Patterns ###\n")
    problems = monitor.get_problem_patterns()
    
    if problems['most_failed_queries']:
        print("Failed Queries:")
        for query, count in problems['most_failed_queries']:
            print(f"  {count}x: {query}")
    
    if problems['slowest_queries']:
        print("\nSlowest Queries:")
        for query, time_ms in problems['slowest_queries']:
            print(f"  {time_ms:.0f}ms: {query}")
    
    # Alerts
    print("\n### Alerts ###\n")
    if monitor.alerts_sent:
        for alert in monitor.alerts_sent:
            print(f"  [{alert['severity'].upper()}] {alert['message']}")
    else:
        print("  No alerts sent")
    
    # Summary Report
    print("\n### Summary Report ###\n")
    print(monitor.generate_summary_report())
    
    # Save
    monitor._save_metrics()
    print(f"\n✅ Metrics saved to {monitor.metrics_file}")
    
    # Cleanup
    if monitor.metrics_file.exists():
        monitor.metrics_file.unlink()


if __name__ == "__main__":
    test_monitoring()
