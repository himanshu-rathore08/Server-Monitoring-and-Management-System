# -*- coding: utf-8 -*-
"""
Enhanced ML-based Anomaly Detection and Predictive Model
- Detects anomalies in metrics and logs
- Predicts potential issues before they occur
- INCLUDES API/Web attack predictions
- Uses Isolation Forest, statistical analysis, and pattern matching
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import Counter, defaultdict
import joblib
from datetime import datetime, timedelta
from time_utils import now_utc
from typing import Dict, List, Any, Tuple
import logging
import sqlite3
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """ML-based anomaly detection for system metrics"""
    
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, metrics_data: pd.DataFrame) -> np.ndarray:
        """Prepare features from metrics data"""
        features = metrics_data[[
            'cpu_percent', 'memory_percent', 'disk_percent',
            'network_connections', 'process_count'
        ]].values
        
        return features
    
    def train(self, metrics_data: pd.DataFrame):
        """Train anomaly detection model"""
        features = self.prepare_features(metrics_data)
        # Guard: replace zero-variance columns with tiny noise to prevent scaler issues
        import numpy as np
        stds = features.std(axis=0)
        for i, std in enumerate(stds):
            if std == 0:
                features[:, i] += np.random.normal(0, 1e-6, size=features.shape[0])
        features_scaled = self.scaler.fit_transform(features)
        
        self.model.fit(features_scaled)
        self.is_trained = True
        
        logger.info("Anomaly detection model trained")
    
    def detect_anomalies(self, metrics_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Detect anomalies in metrics data"""
        if not self.is_trained:
            logger.warning("Model not trained, training on current data")
            self.train(metrics_data)
        
        features = self.prepare_features(metrics_data)
        features_scaled = self.scaler.transform(features)
        
        # -1 for anomalies, 1 for normal
        predictions = self.model.predict(features_scaled)
        
        # Get anomaly scores
        scores = self.model.score_samples(features_scaled)
        
        return predictions, scores
    
    def save_model(self, path: str):
        """Save trained model"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }, path)
    
    def load_model(self, path: str):
        """Load trained model"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.is_trained = data['is_trained']


class EnhancedPredictiveModel:
    """Enhanced predictive model with API/Web attack prediction"""
    
    def __init__(self):
        # System resource failure patterns (original)
        self.resource_failure_patterns = {
            'memory_leak': {
                'indicators': ['increasing_memory', 'stable_processes'],
                'threshold': 0.85,
                'time_window_minutes': 30
            },
            'cpu_spike': {
                'indicators': ['increasing_cpu', 'increasing_processes'],
                'threshold': 0.90,
                'time_window_minutes': 15
            },
            'disk_full': {
                'indicators': ['increasing_disk'],
                'threshold': 0.95,
                'time_window_minutes': 60
            },
            'network_saturation': {
                'indicators': ['increasing_network', 'increasing_connections'],
                'threshold': 0.80,
                'time_window_minutes': 20
            },
            'process_exhaustion': {
                'indicators': ['increasing_processes', 'increasing_memory'],
                'threshold': 0.85,
                'time_window_minutes': 25
            }
        }
        
        # NEW: API/Web attack prediction patterns
        self.api_attack_patterns = {
            'api_500_surge_imminent': {
                'lookback_minutes': 15,
                'threshold_rate': 2,  # errors per minute
                'prediction_confidence_min': 0.6
            },
            '404_brute_force_imminent': {
                'lookback_minutes': 5,
                'threshold_rate': 3,  # 404s per minute
                'prediction_confidence_min': 0.5
            },
            'slow_endpoint_degradation': {
                'lookback_minutes': 10,
                'threshold_ms': 800,  # approaching 1000ms threshold
                'prediction_confidence_min': 0.6
            },
            'authentication_attack_imminent': {
                'lookback_minutes': 5,
                'threshold_rate': 1.5,  # 401s per minute
                'prediction_confidence_min': 0.5
            }
        }
    
    def analyze_system_trends(self, metrics_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in system metrics to predict resource issues"""
        trends = {}
        
        # Memory trend
        if len(metrics_df) >= 3:
            memory_values = metrics_df['memory_percent'].values
            memory_trend = np.polyfit(range(len(memory_values)), memory_values, 1)[0]
            trends['increasing_memory'] = memory_trend > 0.5
            trends['memory_rate'] = memory_trend
            
            # CPU trend
            cpu_values = metrics_df['cpu_percent'].values
            cpu_trend = np.polyfit(range(len(cpu_values)), cpu_values, 1)[0]
            trends['increasing_cpu'] = cpu_trend > 1.0
            trends['cpu_rate'] = cpu_trend
            
            # Disk trend
            disk_values = metrics_df['disk_percent'].values
            disk_trend = np.polyfit(range(len(disk_values)), disk_values, 1)[0]
            trends['increasing_disk'] = disk_trend > 0.1
            trends['disk_rate'] = disk_trend
            
            # Network trend
            network_values = metrics_df['network_connections'].values
            network_trend = np.polyfit(range(len(network_values)), network_values, 1)[0]
            trends['increasing_network'] = network_trend > 5
            trends['network_rate'] = network_trend
            
            # Process trend
            process_values = metrics_df['process_count'].values
            process_trend = np.polyfit(range(len(process_values)), process_values, 1)[0]
            trends['increasing_processes'] = process_trend > 2
            trends['process_rate'] = process_trend
            
            # Stable processes (indicator for memory leak)
            process_std = np.std(process_values)
            trends['stable_processes'] = process_std < 10
            
            # Increasing connections
            conn_std = np.std(network_values)
            trends['increasing_connections'] = conn_std > 50
        
        return trends
    
    def predict_api_issues(self, db_conn: sqlite3.Connection, server_name: str) -> List[Dict[str, Any]]:
        """
        NEW: Predict API/Web issues based on event patterns
        Analyzes recent events to predict imminent attacks/outages
        """
        predictions = []
        
        try:
            # Get recent events (last 30 minutes)
            query = '''
                SELECT timestamp, severity, message, source
                FROM events
                WHERE server_name = ?
                AND timestamp > datetime('now', '-30 minutes')
                ORDER BY timestamp DESC
            '''
            
            events_df = pd.read_sql_query(query, db_conn, params=(server_name,))
            
            if len(events_df) == 0:
                return predictions
            
            # Convert timestamp
            events_df['timestamp'] = pd.to_datetime(events_df['timestamp'], utc=True)
            
            # Extract status codes from messages
            events_df['status_code'] = events_df['message'].str.extract(r'Status (\d{3})')
            events_df['status_code'] = pd.to_numeric(events_df['status_code'], errors='coerce')
            
            # 1. Predict API 500 Surge
            prediction = self._predict_500_surge(events_df, server_name)
            if prediction:
                predictions.append(prediction)
            
            # 2. Predict 404 Brute Force
            prediction = self._predict_404_brute_force(events_df, server_name)
            if prediction:
                predictions.append(prediction)
            
            # 3. Predict Slow Endpoint Degradation
            prediction = self._predict_slow_endpoint(db_conn, server_name)
            if prediction:
                predictions.append(prediction)
            
            # 4. Predict Authentication Attack
            prediction = self._predict_auth_attack(events_df, server_name)
            if prediction:
                predictions.append(prediction)
                
        except Exception as e:
            logger.error(f"Error predicting API issues: {e}")
        
        return predictions
    
    def _predict_500_surge(self, events_df: pd.DataFrame, server_name: str) -> Dict[str, Any]:
        """Predict imminent 500 error surge based on increasing error rate"""
        pattern = self.api_attack_patterns['api_500_surge_imminent']
        lookback = timedelta(minutes=pattern['lookback_minutes'])
        cutoff_time = now_utc() - lookback
        
        # Filter to lookback window
        recent_df = events_df[events_df['timestamp'] > cutoff_time]
        
        # Count 5xx errors
        errors_5xx = recent_df[recent_df['status_code'] >= 500]
        
        if len(errors_5xx) < 5:
            return None
        
        # Calculate error rate (errors per minute)
        time_span_minutes = (recent_df['timestamp'].max() - recent_df['timestamp'].min()).total_seconds() / 60
        if time_span_minutes < 1:
            time_span_minutes = 1
        
        error_rate = len(errors_5xx) / time_span_minutes
        
        # Check if rate is increasing
        if error_rate > pattern['threshold_rate']:
            # Calculate trend
            errors_5xx['minute'] = errors_5xx['timestamp'].dt.floor('min')
            errors_by_minute = errors_5xx.groupby('minute').size()
            
            if len(errors_by_minute) >= 3:
                trend = np.polyfit(range(len(errors_by_minute)), errors_by_minute.values, 1)[0]
                
                if trend > 0.5:  # Increasing trend
                    confidence = min(0.9, error_rate / 10)  # Cap at 90%
                    
                    # Estimate time to surge (threshold: 10 errors/min)
                    if trend > 0:
                        time_to_surge = (10 - error_rate) / trend
                        time_to_surge_minutes = max(5, min(int(time_to_surge), 30))
                    else:
                        time_to_surge_minutes = 15
                    
                    return {
                        'timestamp': now_utc().isoformat(),
                        'server_name': server_name,
                        'agent_id': None,
                        'prediction_type': 'api_500_surge',
                        'confidence': round(confidence, 2),
                        'predicted_issue': f'API 500 error surge predicted - current rate: {error_rate:.1f} errors/min',
                        'time_to_failure_minutes': time_to_surge_minutes,
                        'current_value': round(error_rate, 2),
                        'threshold': 10.0,
                        'recommendation': 'Check application logs immediately. Review recent deployments. Verify backend service health. Scale infrastructure if needed.'
                    }
        
        return None
    
    def _predict_404_brute_force(self, events_df: pd.DataFrame, server_name: str) -> Dict[str, Any]:
        """Predict imminent 404 brute force attack"""
        pattern = self.api_attack_patterns['404_brute_force_imminent']
        lookback = timedelta(minutes=pattern['lookback_minutes'])
        cutoff_time = now_utc() - lookback
        
        recent_df = events_df[events_df['timestamp'] > cutoff_time]
        
        # Count 404 errors
        errors_404 = recent_df[recent_df['status_code'] == 404]
        
        if len(errors_404) < 10:
            return None
        
        # Calculate 404 rate
        time_span_minutes = (recent_df['timestamp'].max() - recent_df['timestamp'].min()).total_seconds() / 60
        if time_span_minutes < 1:
            time_span_minutes = 1
        
        error_404_rate = len(errors_404) / time_span_minutes
        
        if error_404_rate > pattern['threshold_rate']:
            # Check if rate is accelerating
            errors_404['minute'] = errors_404['timestamp'].dt.floor('min')
            errors_by_minute = errors_404.groupby('minute').size()
            
            if len(errors_by_minute) >= 2:
                trend = np.polyfit(range(len(errors_by_minute)), errors_by_minute.values, 1)[0]
                
                if trend > 0.3:  # Accelerating
                    confidence = min(0.85, error_404_rate / 15)
                    
                    # Estimate time to full brute force (threshold: 20/min)
                    if trend > 0:
                        time_to_attack = (20 - error_404_rate) / trend
                        time_to_attack_minutes = max(2, min(int(time_to_attack), 15))
                    else:
                        time_to_attack_minutes = 5
                    
                    return {
                        'timestamp': now_utc().isoformat(),
                        'server_name': server_name,
                        'agent_id': None,
                        'prediction_type': '404_brute_force',
                        'confidence': round(confidence, 2),
                        'predicted_issue': f'404 brute force attack imminent - current rate: {error_404_rate:.1f} per minute',
                        'time_to_failure_minutes': time_to_attack_minutes,
                        'current_value': round(error_404_rate, 2),
                        'threshold': 20.0,
                        'recommendation': 'Enable rate limiting immediately. Block suspicious IPs. Activate WAF rules. Monitor for escalation.'
                    }
        
        return None
    
    def _predict_slow_endpoint(self, db_conn: sqlite3.Connection, server_name: str) -> Dict[str, Any]:
        """Predict endpoint performance degradation"""
        pattern = self.api_attack_patterns['slow_endpoint_degradation']
        
        # Query events with response time data
        query = '''
            SELECT timestamp, message
            FROM events
            WHERE server_name = ?
            AND timestamp > datetime('now', '-{} minutes')
            AND message LIKE '%time_taken_ms%'
            ORDER BY timestamp DESC
        '''.format(pattern['lookback_minutes'])
        
        try:
            events_df = pd.read_sql_query(query, db_conn, params=(server_name,))
            
            if len(events_df) < 5:
                return None
            
            # Extract response times from message
            # Assuming format: "... time_taken_ms: 1234"
            events_df['response_time'] = events_df['message'].str.extract(r'(\d+)ms')
            events_df['response_time'] = pd.to_numeric(events_df['response_time'], errors='coerce')
            events_df = events_df.dropna(subset=['response_time'])
            
            if len(events_df) >= 5:
                recent_times = events_df['response_time'].values
                avg_response_time = np.mean(recent_times)
                
                # Check if approaching slow threshold (1000ms)
                if avg_response_time > pattern['threshold_ms']:
                    # Calculate trend
                    trend = np.polyfit(range(len(recent_times)), recent_times, 1)[0]
                    
                    if trend > 10:  # Increasing by 10ms per request
                        confidence = min(0.8, avg_response_time / 1000)
                        
                        # Estimate time to critical slowness (1000ms)
                        time_to_critical = (1000 - avg_response_time) / trend
                        time_to_critical_minutes = max(3, min(int(time_to_critical / 10), 20))
                        
                        return {
                            'timestamp': now_utc().isoformat(),
                            'server_name': server_name,
                            'agent_id': None,
                            'prediction_type': 'slow_endpoint',
                            'confidence': round(confidence, 2),
                            'predicted_issue': f'Endpoint performance degrading - avg response time: {avg_response_time:.0f}ms',
                            'time_to_failure_minutes': time_to_critical_minutes,
                            'current_value': round(avg_response_time, 2),
                            'threshold': 1000.0,
                            'recommendation': 'Check database query performance. Review application logs. Add caching. Optimize slow queries.'
                        }
        except Exception as e:
            logger.debug(f"Error analyzing response times: {e}")
        
        return None
    
    def _predict_auth_attack(self, events_df: pd.DataFrame, server_name: str) -> Dict[str, Any]:
        """Predict authentication brute force attack"""
        pattern = self.api_attack_patterns['authentication_attack_imminent']
        lookback = timedelta(minutes=pattern['lookback_minutes'])
        cutoff_time = now_utc() - lookback
        
        recent_df = events_df[events_df['timestamp'] > cutoff_time]
        
        # Count 401 errors
        errors_401 = recent_df[recent_df['status_code'] == 401]
        
        if len(errors_401) < 5:
            return None
        
        # Calculate 401 rate
        time_span_minutes = (recent_df['timestamp'].max() - recent_df['timestamp'].min()).total_seconds() / 60
        if time_span_minutes < 1:
            time_span_minutes = 1
        
        auth_fail_rate = len(errors_401) / time_span_minutes
        
        if auth_fail_rate > pattern['threshold_rate']:
            errors_401['minute'] = errors_401['timestamp'].dt.floor('min')
            errors_by_minute = errors_401.groupby('minute').size()
            
            if len(errors_by_minute) >= 2:
                trend = np.polyfit(range(len(errors_by_minute)), errors_by_minute.values, 1)[0]
                
                if trend > 0.2:
                    confidence = min(0.75, auth_fail_rate / 10)
                    
                    time_to_attack = (10 - auth_fail_rate) / max(trend, 0.5)
                    time_to_attack_minutes = max(3, min(int(time_to_attack), 15))
                    
                    return {
                        'timestamp': now_utc().isoformat(),
                        'server_name': server_name,
                        'agent_id': None,
                        'prediction_type': 'authentication_attack',
                        'confidence': round(confidence, 2),
                        'predicted_issue': f'Authentication brute force attack predicted - rate: {auth_fail_rate:.1f}/min',
                        'time_to_failure_minutes': time_to_attack_minutes,
                        'current_value': round(auth_fail_rate, 2),
                        'threshold': 10.0,
                        'recommendation': 'Enable account lockout. Add CAPTCHA. Implement MFA. Monitor for credential stuffing.'
                    }
        
        return None
    
    def predict_resource_failures(self, metrics_df: pd.DataFrame, server_name: str) -> List[Dict[str, Any]]:
        """Predict system resource failures (original functionality)"""
        predictions = []
        
        if len(metrics_df) < 3:
            return predictions
        
        trends = self.analyze_system_trends(metrics_df)
        latest_metrics = metrics_df.iloc[-1]
        
        # Check each failure pattern
        for failure_type, pattern in self.resource_failure_patterns.items():
            indicators_met = sum([
                trends.get(indicator, False) 
                for indicator in pattern['indicators']
            ])
            
            required_indicators = len(pattern['indicators'])
            confidence = indicators_met / required_indicators
            
            # Check if current metric is approaching threshold
            metric_key = failure_type.split('_')[0] + '_percent'
            if metric_key in latest_metrics:
                current_value = latest_metrics[metric_key]
                threshold = pattern['threshold'] * 100
                
                proximity_to_threshold = current_value / threshold
                
                if proximity_to_threshold > 0.7 and confidence > 0.5:
                    # Calculate time to failure based on trend
                    rate_key = failure_type.split('_')[0] + '_rate'
                    if rate_key in trends and trends[rate_key] > 0:
                        remaining = threshold - current_value
                        time_to_failure = remaining / trends[rate_key]
                        time_to_failure_minutes = min(int(time_to_failure), 
                                                     pattern['time_window_minutes'])
                    else:
                        time_to_failure_minutes = pattern['time_window_minutes']
                    
                    prediction = {
                        'timestamp': now_utc().isoformat(),
                        'server_name': server_name,
                        'agent_id': latest_metrics.get('agent_id'),
                        'prediction_type': failure_type,
                        'confidence': round(confidence * proximity_to_threshold, 2),
                        'predicted_issue': self._get_issue_description(failure_type),
                        'time_to_failure_minutes': time_to_failure_minutes,
                        'current_value': round(current_value, 2),
                        'threshold': round(threshold, 2),
                        'recommendation': self._get_recommendation(failure_type)
                    }
                    
                    predictions.append(prediction)
        
        return predictions
    
    def _get_issue_description(self, failure_type: str) -> str:
        """Get human-readable issue description"""
        descriptions = {
            'memory_leak': 'Memory leak detected - continuous memory growth without deallocation',
            'cpu_spike': 'CPU spike imminent - processing load increasing rapidly',
            'disk_full': 'Disk space exhaustion - storage approaching capacity',
            'network_saturation': 'Network saturation - connection limits being approached',
            'process_exhaustion': 'Process exhaustion - too many processes consuming resources'
        }
        return descriptions.get(failure_type, 'Unknown issue')
    
    def _get_recommendation(self, failure_type: str) -> str:
        """Get recommended action"""
        recommendations = {
            'memory_leak': 'Investigate application memory usage. Check for unclosed connections or objects. Consider restarting affected services.',
            'cpu_spike': 'Review running processes. Check for infinite loops or resource-intensive operations. Consider load balancing.',
            'disk_full': 'Clean up temporary files and logs. Archive old data. Increase storage capacity.',
            'network_saturation': 'Review active connections. Check for DDoS or unusual traffic. Scale network resources.',
            'process_exhaustion': 'Kill zombie processes. Review process spawning logic. Increase process limits if legitimate.'
        }
        return recommendations.get(failure_type, 'Monitor the situation and investigate root cause')


class EventCorrelator:
    """Correlate events to identify incidents"""
    
    def __init__(self, time_window_minutes: int = 10):
        self.time_window_minutes = time_window_minutes
        
    def correlate_events(self, events: List[Dict]) -> List[List[Dict]]:
        """Group related events into incident clusters"""
        if not events:
            return []
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(events)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', utc=True)
        df = df.sort_values('timestamp')
        
        clusters = []
        current_cluster = [events[0]]
        
        for i in range(1, len(events)):
            time_diff = (df.iloc[i]['timestamp'] - df.iloc[i-1]['timestamp']).total_seconds() / 60
            
            # Same server and within time window
            if (time_diff <= self.time_window_minutes and 
                events[i]['server_name'] == events[i-1]['server_name']):
                current_cluster.append(events[i])
            else:
                if len(current_cluster) >= 2:  # Only keep clusters with multiple events
                    clusters.append(current_cluster)
                current_cluster = [events[i]]
        
        if len(current_cluster) >= 2:
            clusters.append(current_cluster)
        
        return clusters


if __name__ == "__main__":
    logger.info("Enhanced ML Predictor with API/Web Attack Detection")
