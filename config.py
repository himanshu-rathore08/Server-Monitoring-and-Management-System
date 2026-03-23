"""
Configuration for Financial Enterprise Monitoring System
"""

import os

# Agent Configuration
AGENT_CONFIG = {
    'collection_interval_seconds': 30,
    'heartbeat_interval_seconds': 60,
    'retry_attempts': 3,
    'timeout_seconds': 10
}

# Log Configurations
LOG_CONFIGS = [
    {
        'name': 'IIS Access Logs',
        'type': 'iis',
        'paths': [
            '/var/log/iis/access.log',
            '/var/log/iis/W3SVC1/*.log',
            'C:\\inetpub\\logs\\LogFiles\\W3SVC1\\*.log'  # Windows
        ],
        'enabled': True
    },
    {
        'name': 'Tomcat Logs',
        'type': 'tomcat',
        'paths': [
            '/var/log/tomcat/catalina.out',
            '/var/log/tomcat/localhost*.log',
            '/opt/tomcat/logs/catalina.out'
        ],
        'enabled': True
    },
    {
        'name': 'System Logs',
        'type': 'system',
        'paths': [
            '/var/log/syslog',
            '/var/log/messages',
            '/var/log/kern.log'
        ],
        'enabled': True
    },
    {
        'name': 'Application Logs',
        'type': 'application',
        'paths': [
            '/var/log/app/*.log',
            '/opt/app/logs/*.log'
        ],
        'enabled': True
    }
]

# Central Collector Configuration
CENTRAL_CONFIG = {
    'host': '0.0.0.0',
    'port': 8080,
    'database_path': 'monitoring.db',
    'max_connections': 100,
    'buffer_size': 10000
}

# ML Model Configuration
ML_CONFIG = {
    'anomaly_detection': {
        'contamination': 0.1,  # Expected percentage of anomalies
        'n_estimators': 100,
        'training_window_hours': 24,
        'update_frequency_hours': 6
    },
    'prediction': {
        'lookback_window_minutes': 60,
        'prediction_horizon_minutes': 30,
        'confidence_threshold': 0.7
    },
    'event_correlation': {
        'time_window_minutes': 10,
        'min_events_for_incident': 2
    }
}

# Alerting Configuration
ALERT_CONFIG = {
    'channels': {
        'email': {
            'enabled': False,
            'smtp_server': 'smtp.company.com',
            'smtp_port': 587,
            'from_address': 'monitoring@company.com',
            'to_addresses': ['ops-team@company.com']
        },
        'slack': {
            'enabled': False,
            'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
            'channel': '#monitoring-alerts'
        },
        'pagerduty': {
            'enabled': False,
            'api_key': 'your-pagerduty-api-key',
            'service_id': 'your-service-id'
        }
    },
    'severity_levels': {
        'critical': {
            'notify_immediately': True,
            'escalation_timeout_minutes': 5
        },
        'error': {
            'notify_immediately': True,
            'escalation_timeout_minutes': 15
        },
        'warning': {
            'notify_immediately': False,
            'batch_interval_minutes': 30
        }
    }
}

# Thresholds for Anomaly Detection
THRESHOLDS = {
    'cpu_percent': {
        'warning': 80,
        'critical': 95
    },
    'memory_percent': {
        'warning': 85,
        'critical': 95
    },
    'disk_percent': {
        'warning': 90,
        'critical': 98
    },
    'network_connections': {
        'warning': 8000,
        'critical': 15000
    },
    'error_rate_per_minute': {
        'warning': 10,
        'critical': 50
    }
}

# Retention Policies
RETENTION_CONFIG = {
    'metrics': {
        'raw_data_days': 7,
        'aggregated_hourly_days': 30,
        'aggregated_daily_days': 365
    },
    'events': {
        'all_events_days': 30,
        'critical_events_days': 365
    },
    'incidents': {
        'closed_incidents_days': 365,
        'all_incidents_days': 1825  # 5 years
    }
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'refresh_interval_seconds': 30,
    'default_time_range_hours': 24,
    'max_events_display': 100
}

# Security Configuration
SECURITY_CONFIG = {
    'encryption_enabled': True,
    'api_key_required': True,
    'ssl_enabled': True,
    'allowed_ips': [],  # Empty = allow all
    'rate_limit_per_minute': 1000
}
