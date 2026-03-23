"""
Central Data Collector - BACKWARD COMPATIBLE VERSION
Works with existing monitoring agents while supporting new features
"""

import json
import sqlite3
from datetime import datetime, timedelta
from time_utils import now_utc, utc_to_ist
from typing import Dict, List, Any
import logging
from collections import defaultdict
import threading
import queue

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CentralCollector:
    """Centralized collector for all monitoring data - BACKWARD COMPATIBLE"""
    
    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path
        self.data_queue = queue.Queue(maxsize=1000)  # Fixed: bounded queue prevents unbounded memory growth
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with BACKWARD COMPATIBLE schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Metrics table - BACKWARD COMPATIBLE (accepts both old and new format)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                agent_id TEXT,
                server_name TEXT,
                hostname TEXT,
                ip_address TEXT,
                cpu_percent REAL,
                cpu_count INTEGER,
                memory_total_mb REAL,
                memory_used_mb REAL,
                memory_percent REAL,
                disk_total_gb REAL,
                disk_used_gb REAL,
                disk_percent REAL,
                network_bytes_sent INTEGER,
                network_bytes_recv INTEGER,
                network_connections INTEGER,
                process_count INTEGER,
                UNIQUE(timestamp, agent_id)
            )
        ''')
        
        # Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                agent_id TEXT,
                server_name TEXT,
                source TEXT,
                severity TEXT,
                message TEXT,
                log_file TEXT,
                stack_trace TEXT,
                processed BOOLEAN DEFAULT 0,
                anomaly_score REAL
            )
        ''')
        
        # HTTP Metrics table (NEW - optional)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS http_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                agent_id TEXT,
                server_name TEXT,
                url TEXT,
                endpoint TEXT,
                method TEXT,
                status_code INTEGER,
                response_time_ms REAL,
                response_size_bytes INTEGER,
                error_message TEXT,
                is_success BOOLEAN
            )
        ''')
        
        # Incidents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT UNIQUE,
                start_time DATETIME,
                end_time DATETIME,
                status TEXT,
                severity TEXT,
                affected_servers TEXT,
                incident_type TEXT,
                root_cause TEXT,
                summary TEXT,
                solution TEXT,
                related_events TEXT,
                attack_details TEXT
            )
        ''')
        
        # Migrate existing DB: add attack_details if missing
        try:
            cursor.execute('ALTER TABLE incidents ADD COLUMN attack_details TEXT')
        except Exception:
            pass  # Column already exists
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                agent_id TEXT,
                server_name TEXT,
                prediction_type TEXT,
                confidence REAL,
                predicted_issue TEXT,
                time_to_failure_minutes INTEGER,
                recommendation TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)')
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully (backward compatible)")
    
    def ingest_data(self, data: Dict[str, Any]):
        """Ingest data from monitoring agents - BACKWARD COMPATIBLE"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store metrics
            metrics = data.get('metrics', {})
            if metrics:
                cursor.execute('''
                    INSERT OR REPLACE INTO metrics 
                    (timestamp, agent_id, server_name, hostname, ip_address,
                     cpu_percent, cpu_count, memory_total_mb, memory_used_mb, 
                     memory_percent, disk_total_gb, disk_used_gb, disk_percent,
                     network_bytes_sent, network_bytes_recv, network_connections,
                     process_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.get('timestamp'),
                    metrics.get('agent_id'),
                    metrics.get('server_name'),
                    metrics.get('hostname'),
                    metrics.get('ip_address'),
                    metrics.get('cpu', {}).get('percent_total'),
                    metrics.get('cpu', {}).get('count'),
                    metrics.get('memory', {}).get('total_mb'),
                    metrics.get('memory', {}).get('used_mb'),
                    metrics.get('memory', {}).get('percent'),
                    metrics.get('disk', {}).get('total_gb') or 0,  # Fixed: was incorrectly falling back to disk_percent
                    metrics.get('disk', {}).get('used_gb') or 0,
                    metrics.get('disk', {}).get('percent'),
                    metrics.get('network', {}).get('bytes_sent') or 0,
                    metrics.get('network', {}).get('bytes_recv') or 0,
                    metrics.get('network', {}).get('connections'),
                    metrics.get('processes', {}).get('total_count')
                ))
            
            # Store events
            events = data.get('log_events', [])
            for event in events:
                stack_trace = json.dumps(event.get('stack_trace', [])) if 'stack_trace' in event else None
                
                cursor.execute('''
                    INSERT INTO events 
                    (timestamp, agent_id, server_name, source, severity, 
                     message, log_file, stack_trace)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.get('timestamp'),
                    data.get('agent_id'),
                    event.get('server'),
                    event.get('source'),
                    event.get('severity'),
                    event.get('message'),
                    event.get('log_file'),
                    stack_trace
                ))
            
            # Store HTTP metrics (NEW - optional, if provided)
            http_metrics = data.get('http_metrics', [])
            for http in http_metrics:
                cursor.execute('''
                    INSERT INTO http_metrics
                    (timestamp, agent_id, server_name, url, endpoint, 
                     method, status_code, response_time_ms, response_size_bytes,
                     error_message, is_success)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    http.get('timestamp'),
                    data.get('agent_id'),
                    http.get('server_name'),
                    http.get('url'),
                    http.get('endpoint'),
                    http.get('method', 'GET'),
                    http.get('status_code'),
                    http.get('response_time_ms'),
                    http.get('response_size_bytes'),
                    http.get('error_message'),
                    http.get('status_code', 0) < 400 if http.get('status_code') else False
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Ingested data from {data.get('agent_id')}: "
                       f"{len(events)} events, {len(http_metrics)} HTTP metrics")
            
            # Queue for real-time processing (non-blocking; drop if full to prevent backpressure)
            try:
                self.data_queue.put_nowait(data)
            except queue.Full:
                logger.warning("data_queue full — dropping oldest item")
                try:
                    self.data_queue.get_nowait()
                    self.data_queue.put_nowait(data)
                except Exception:
                    pass
            
        except Exception as e:
            logger.error(f"Error ingesting data: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def get_recent_metrics(self, agent_id: str, minutes: int = 60) -> List[Dict]:
        """Get recent metrics for an agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = (now_utc() - timedelta(minutes=minutes)).isoformat()
        
        cursor.execute('''
            SELECT * FROM metrics 
            WHERE agent_id = ? AND timestamp > ?
            ORDER BY timestamp DESC
        ''', (agent_id, cutoff_time))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_unprocessed_events(self) -> List[Dict]:
        """Get events that haven't been processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM events 
            WHERE processed = 0
            ORDER BY timestamp ASC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_http_health_summary(self, endpoint: str = None, minutes: int = 60) -> List[Dict]:
        """Get HTTP endpoint health summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = (now_utc() - timedelta(minutes=minutes)).isoformat()
        
        try:
            if endpoint:
                cursor.execute('''
                    SELECT 
                        endpoint,
                        COUNT(*) as total_requests,
                        SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) as success_count,
                        SUM(CASE WHEN is_success = 0 THEN 1 ELSE 0 END) as error_count,
                        AVG(response_time_ms) as avg_response_time,
                        ROUND(100.0 * SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as availability
                    FROM http_metrics
                    WHERE timestamp > ? AND endpoint = ?
                    GROUP BY endpoint
                ''', (cutoff_time, endpoint))
            else:
                cursor.execute('''
                    SELECT 
                        endpoint,
                        COUNT(*) as total_requests,
                        SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) as success_count,
                        SUM(CASE WHEN is_success = 0 THEN 1 ELSE 0 END) as error_count,
                        AVG(response_time_ms) as avg_response_time,
                        ROUND(100.0 * SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as availability
                    FROM http_metrics
                    WHERE timestamp > ?
                    GROUP BY endpoint
                ''', (cutoff_time,))
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"HTTP health query error: {e}")
            results = []
        
        conn.close()
        return results
    
    def get_http_errors(self, minutes: int = 60, limit: int = 100) -> List[Dict]:
        """Get recent HTTP errors"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = (now_utc() - timedelta(minutes=minutes)).isoformat()
        
        try:
            cursor.execute('''
                SELECT * FROM http_metrics
                WHERE timestamp > ? AND is_success = 0
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (cutoff_time, limit))
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"HTTP errors query error: {e}")
            results = []
        
        conn.close()
        return results
    
    def mark_events_processed(self, event_ids: List[int]):
        """Mark events as processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.executemany(
            'UPDATE events SET processed = 1 WHERE id = ?',
            [(eid,) for eid in event_ids]
        )
        
        conn.commit()
        conn.close()
    
    def create_incident(self, incident_data: Dict[str, Any]):
        """Create a new incident"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO incidents 
            (incident_id, start_time, status, severity, affected_servers,
             incident_type, root_cause, summary, solution, related_events)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            incident_data.get('incident_id'),
            incident_data.get('start_time'),
            incident_data.get('status', 'open'),
            incident_data.get('severity'),
            json.dumps(incident_data.get('affected_servers', [])),
            incident_data.get('incident_type'),
            incident_data.get('root_cause'),
            incident_data.get('summary'),
            incident_data.get('solution'),
            json.dumps(incident_data.get('related_events', []))
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created incident: {incident_data.get('incident_id')}")
    
    def save_prediction(self, prediction: Dict[str, Any]):
        """Save prediction from ML model"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions 
            (timestamp, agent_id, server_name, prediction_type, confidence,
             predicted_issue, time_to_failure_minutes, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prediction.get('timestamp'),
            prediction.get('agent_id'),
            prediction.get('server_name'),
            prediction.get('prediction_type'),
            prediction.get('confidence'),
            prediction.get('predicted_issue'),
            prediction.get('time_to_failure_minutes'),
            prediction.get('recommendation')
        ))
        
        conn.commit()
        conn.close()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall system health
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT server_name) as total_servers,
                AVG(cpu_percent) as avg_cpu,
                AVG(memory_percent) as avg_memory,
                AVG(disk_percent) as avg_disk
            FROM metrics
            WHERE timestamp > datetime('now', '-5 minutes')
        ''')
        health = cursor.fetchone()
        
        # Active incidents
        cursor.execute('''
            SELECT COUNT(*) FROM incidents WHERE status = 'open'
        ''')
        active_incidents = cursor.fetchone()[0]
        
        # Recent events by severity
        cursor.execute('''
            SELECT severity, COUNT(*) as count
            FROM events
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY severity
        ''')
        events_by_severity = dict(cursor.fetchall())
        
        # Recent predictions
        cursor.execute('''
            SELECT * FROM predictions
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY confidence DESC
            LIMIT 10
        ''')
        columns = [desc[0] for desc in cursor.description]
        recent_predictions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # HTTP endpoint health
        try:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) as success_count,
                    AVG(response_time_ms) as avg_response_time,
                    ROUND(100.0 * SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as availability
                FROM http_metrics
                WHERE timestamp > datetime('now', '-1 hour')
            ''')
            http_health = cursor.fetchone()
        except Exception:
            http_health = (0, 0, 0, 0)
        
        conn.close()
        
        return {
            'total_servers': health[0] if health[0] else 0,
            'avg_cpu_percent': round(health[1], 2) if health[1] else 0,
            'avg_memory_percent': round(health[2], 2) if health[2] else 0,
            'avg_disk_percent': round(health[3], 2) if health[3] else 0,
            'active_incidents': active_incidents,
            'events_by_severity': events_by_severity,
            'recent_predictions': recent_predictions,
            'http_total_requests': http_health[0] if http_health else 0,
            'http_success_count': http_health[1] if http_health else 0,
            'http_avg_response_time': round(http_health[2], 2) if http_health and http_health[2] else 0,
            'http_availability': http_health[3] if http_health else 0
        }


if __name__ == "__main__":
    collector = CentralCollector()
    logger.info("Backward compatible central collector started")
