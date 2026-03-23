"""
Demo Script - Simulates the complete monitoring system
Generates sample data and demonstrates all features
"""

import json
import random
import time
from datetime import datetime, timedelta
import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from central_collector import CentralCollector
from ml_predictor_enhanced import AnomalyDetector, EnhancedPredictiveModel
from rca_engine_enhanced import EnhancedRCAEngine as RCAEngine
import pandas as pd
import numpy as np


class DemoDataGenerator:
    """Generate realistic demo data"""
    
    def __init__(self):
        self.servers = [
            'PROD-APP-SERVER-01',
            'PROD-APP-SERVER-02',
            'PROD-DB-SERVER-01',
            'PROD-WEB-SERVER-01'
        ]
        self.base_cpu = {server: random.uniform(20, 40) for server in self.servers}
        self.base_memory = {server: random.uniform(50, 70) for server in self.servers}
        
    def generate_normal_metrics(self, server_name: str, agent_id: str) -> dict:
        """Generate normal system metrics"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'agent_id': agent_id,
            'metrics': {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': agent_id,
                'server_name': server_name,
                'hostname': server_name.lower(),
                'ip_address': f'10.0.{random.randint(1, 255)}.{random.randint(1, 255)}',
                'cpu': {
                    'percent_total': self.base_cpu[server_name] + random.uniform(-10, 10),
                    'count': 8
                },
                'memory': {
                    'total_mb': 16384,
                    'used_mb': (self.base_memory[server_name] / 100) * 16384 + random.uniform(-1000, 1000),
                    'percent': self.base_memory[server_name] + random.uniform(-5, 5)
                },
                'disk': {
                    'total_gb': 500,
                    'used_gb': 300 + random.uniform(-10, 10),
                    'percent': 60 + random.uniform(-5, 5)
                },
                'network': {
                    'bytes_sent': random.randint(1000000, 5000000),
                    'bytes_recv': random.randint(1000000, 5000000),
                    'connections': random.randint(100, 500)
                },
                'processes': {
                    'total_count': random.randint(200, 300)
                }
            },
            'log_events': []
        }
    
    def generate_memory_leak_scenario(self, server_name: str, agent_id: str, step: int) -> dict:
        """Simulate memory leak scenario"""
        data = self.generate_normal_metrics(server_name, agent_id)
        
        # Memory increases over time
        memory_percent = 60 + (step * 3)  # 3% increase per step
        if memory_percent > 95:
            memory_percent = 95
        
        data['metrics']['memory']['percent'] = memory_percent
        data['metrics']['memory']['used_mb'] = (memory_percent / 100) * 16384
        
        # Add error events when memory is high
        if memory_percent > 85:
            data['log_events'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'server': server_name,
                'source': 'tomcat',
                'severity': 'error',
                'message': f'WARNING: High memory usage detected: {memory_percent:.1f}%',
                'log_file': '/var/log/tomcat/catalina.out'
            })
        
        if memory_percent > 90:
            data['log_events'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'server': server_name,
                'source': 'tomcat',
                'severity': 'critical',
                'message': 'java.lang.OutOfMemoryError: Java heap space',
                'log_file': '/var/log/tomcat/catalina.out',
                'stack_trace': [
                    'at com.company.app.DataProcessor.process(DataProcessor.java:125)',
                    'at com.company.app.Controller.handleRequest(Controller.java:89)'
                ]
            })
        
        return data
    
    def generate_cpu_spike_scenario(self, server_name: str, agent_id: str, step: int) -> dict:
        """Simulate CPU spike scenario"""
        data = self.generate_normal_metrics(server_name, agent_id)
        
        # CPU spikes suddenly
        if step < 3:
            cpu_percent = 30 + random.uniform(-5, 5)
        else:
            cpu_percent = 95 + random.uniform(-3, 3)
        
        data['metrics']['cpu']['percent_total'] = cpu_percent
        
        if cpu_percent > 90:
            data['log_events'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'server': server_name,
                'source': 'system',
                'severity': 'critical',
                'message': f'CPU usage critical: {cpu_percent:.1f}%',
                'log_file': '/var/log/syslog'
            })
        
        return data
    
    def generate_disk_full_scenario(self, server_name: str, agent_id: str, step: int) -> dict:
        """Simulate disk full scenario"""
        data = self.generate_normal_metrics(server_name, agent_id)
        
        # Disk usage increases
        disk_percent = 80 + (step * 2)
        if disk_percent > 98:
            disk_percent = 98
        
        data['metrics']['disk']['percent'] = disk_percent
        data['metrics']['disk']['used_gb'] = (disk_percent / 100) * 500
        
        if disk_percent > 95:
            data['log_events'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'server': server_name,
                'source': 'system',
                'severity': 'critical',
                'message': f'Disk space critical: {disk_percent:.1f}% used. No space left on device.',
                'log_file': '/var/log/syslog'
            })
        
        return data


def run_demo():
    """Run complete demo of the monitoring system"""
    
    print("\n" + "="*80)
    print("FINANCIAL ENTERPRISE MONITORING SYSTEM - DEMO")
    print("="*80 + "\n")
    
    # Initialize components
    print("Initializing system components...")
    collector = CentralCollector("demo_monitoring.db")
    anomaly_detector = AnomalyDetector()
    predictive_model = EnhancedPredictiveModel()
    rca_engine = RCAEngine("demo_monitoring.db")
    
    generator = DemoDataGenerator()
    
    print("✓ System initialized\n")
    
    # Scenario 1: Normal Operations
    print("\n" + "-"*80)
    print("SCENARIO 1: Normal Operations (30 seconds)")
    print("-"*80)
    
    for i in range(10):
        for idx, server in enumerate(generator.servers):
            agent_id = f"AGENT-{idx+1:03d}"
            data = generator.generate_normal_metrics(server, agent_id)
            collector.ingest_data(data)
        
        print(f"  Collecting normal metrics... ({i+1}/10)")
        time.sleep(0.5)
    
    print("✓ Normal data collected\n")
    
    # Train anomaly detector on normal data
    print("Training ML models on normal data...")
    conn = sqlite3.connect("demo_monitoring.db")
    metrics_df = pd.read_sql_query("SELECT * FROM metrics", conn)
    
    if len(metrics_df) > 0:
        numeric_cols = ['cpu_percent', 'memory_percent', 'disk_percent', 
                       'network_connections', 'process_count']
        for col in numeric_cols:
            metrics_df[col] = pd.to_numeric(metrics_df[col], errors='coerce').fillna(0)
        
        anomaly_detector.train(metrics_df)
        print("✓ ML models trained\n")
    
    conn.close()
    
    # Scenario 2: Memory Leak Detection
    print("\n" + "-"*80)
    print("SCENARIO 2: Memory Leak Simulation")
    print("-"*80)
    
    target_server = 'PROD-APP-SERVER-01'
    agent_id = 'AGENT-001'
    
    print(f"Simulating memory leak on {target_server}...")
    
    for step in range(12):
        data = generator.generate_memory_leak_scenario(target_server, agent_id, step)
        collector.ingest_data(data)
        
        memory_percent = data['metrics']['memory']['percent']
        print(f"  Step {step+1}: Memory at {memory_percent:.1f}%")
        
        time.sleep(0.5)
        
        # Run prediction every few steps
        if step % 3 == 0 and step > 0:
            conn = sqlite3.connect("demo_monitoring.db")
            server_metrics = pd.read_sql_query(
                f"SELECT * FROM metrics WHERE server_name = '{target_server}' ORDER BY timestamp",
                conn
            )
            
            if len(server_metrics) >= 3:
                numeric_cols = ['cpu_percent', 'memory_percent', 'disk_percent', 
                               'network_connections', 'process_count']
                for col in numeric_cols:
                    server_metrics[col] = pd.to_numeric(server_metrics[col], errors='coerce').fillna(0)
                
                predictions = predictive_model.predict_resource_failures(server_metrics, target_server)
                
                for pred in predictions:
                    print(f"\n  🔮 PREDICTION DETECTED:")
                    print(f"     Issue: {pred['predicted_issue']}")
                    print(f"     Confidence: {pred['confidence']:.0%}")
                    print(f"     Time to Failure: {pred['time_to_failure_minutes']} minutes")
                    print(f"     Recommendation: {pred['recommendation'][:100]}...")
                    
                    collector.save_prediction(pred)
            
            conn.close()
    
    print("\n✓ Memory leak scenario completed\n")
    
    # Run RCA on the incident
    print("Running Root Cause Analysis...")
    
    conn = sqlite3.connect("demo_monitoring.db")
    events = pd.read_sql_query(
        f"SELECT * FROM events WHERE server_name = '{target_server}' ORDER BY timestamp",
        conn
    ).to_dict('records')
    
    metrics = pd.read_sql_query(
        f"SELECT * FROM metrics WHERE server_name = '{target_server}' ORDER BY timestamp",
        conn
    ).to_dict('records')
    
    conn.close()
    
    if events:
        rca_result = rca_engine.analyze_incident(events, metrics)
        rca_engine.save_incident(rca_result)
        
        print("\n" + "="*80)
        print(f"🚨 INCIDENT REPORT: {rca_result['incident_id']}")
        print("="*80)
        print(f"\nSeverity: {rca_result['severity'].upper()}")
        print(f"Type: {rca_result['incident_type']}")
        print(f"Affected Servers: {', '.join(rca_result['affected_servers'])}")
        print(f"\nRoot Cause:\n{rca_result['root_cause']}")
        print(f"\n{rca_result['summary']}")
        print(f"\n{rca_result['solution']}")
        print("="*80 + "\n")
    
    # Display Dashboard
    print("\n" + "="*80)
    print("📊 FINAL DASHBOARD")
    print("="*80)
    
    dashboard = collector.get_dashboard_data()
    
    print(f"\nTotal Servers Monitored: {dashboard['total_servers']}")
    print(f"Average CPU Usage: {dashboard['avg_cpu_percent']:.1f}%")
    print(f"Average Memory Usage: {dashboard['avg_memory_percent']:.1f}%")
    print(f"Average Disk Usage: {dashboard['avg_disk_percent']:.1f}%")
    print(f"\nActive Incidents: {dashboard['active_incidents']}")
    print(f"Events by Severity: {dashboard['events_by_severity']}")
    print(f"Recent Predictions: {len(dashboard['recent_predictions'])}")
    
    if dashboard['recent_predictions']:
        print("\nTop Predictions:")
        for pred in dashboard['recent_predictions'][:3]:
            print(f"  - {pred['server_name']}: {pred['prediction_type']} "
                  f"(confidence: {pred.get('confidence', 0):.0%})")
    
    print("\n" + "="*80)
    print("Demo completed successfully!")
    print("Database saved as: demo_monitoring.db")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_demo()
