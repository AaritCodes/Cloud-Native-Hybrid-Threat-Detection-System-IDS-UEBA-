import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import threading
import time
from collections import deque

# Email imports with fallback
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

# Import your existing engines
from src.ids_engine import IDSEngine
from src.ueba_engine import UEBAEngine
from src.threat_fusion_engine import combine_risks

class ThreatDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.setup_data_storage()
        self.setup_engines()
        self.setup_layout()
        self.setup_callbacks()
        self.start_monitoring()
        
    def setup_data_storage(self):
        """Initialize data storage for dashboard"""
        self.max_points = 100  # Keep last 100 data points
        self.data = {
            'timestamps': deque(maxlen=self.max_points),
            'network_in': deque(maxlen=self.max_points),
            'packets_in': deque(maxlen=self.max_points),
            'network_risk': deque(maxlen=self.max_points),
            'user_risk': deque(maxlen=self.max_points),
            'final_risk': deque(maxlen=self.max_points),
            'threat_level': deque(maxlen=self.max_points),
            'alerts': deque(maxlen=50)  # Keep last 50 alerts
        }
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'critical_alerts': 0,
            'high_alerts': 0,
            'medium_alerts': 0,
            'low_alerts': 0,
            'false_positives': 0,
            'uptime_start': datetime.now()
        }
        
    def setup_engines(self):
        """Initialize detection engines"""
        self.ids = IDSEngine("models/ddos_model.pkl")
        self.ueba = UEBAEngine("models/uba_model.pkl")
        
    def setup_layout(self):
        """Create dashboard layout"""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("🛡️ Hybrid Threat Detection Dashboard", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px'}),
                html.P("Real-time AWS CloudWatch + CloudTrail Security Monitoring",
                      style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '18px'})
            ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'marginBottom': '20px'}),
            
            # Status Cards Row
            html.Div([
                # System Status
                html.Div([
                    html.H3("🟢 System Status", style={'color': '#27ae60'}),
                    html.P(id="system-status", children="ACTIVE", style={'fontSize': '24px', 'fontWeight': 'bold'}),
                    html.P(id="uptime", children="", style={'color': '#7f8c8d'})
                ], className="status-card", style={'backgroundColor': '#d5f4e6', 'padding': '20px', 'borderRadius': '10px', 'textAlign': 'center'}),
                
                # Current Threat Level
                html.Div([
                    html.H3("⚠️ Threat Level", style={'color': '#e74c3c'}),
                    html.P(id="current-threat", children="LOW", style={'fontSize': '24px', 'fontWeight': 'bold'}),
                    html.P(id="risk-score", children="", style={'color': '#7f8c8d'})
                ], className="status-card", style={'backgroundColor': '#fadbd8', 'padding': '20px', 'borderRadius': '10px', 'textAlign': 'center'}),
                
                # Total Detections
                html.Div([
                    html.H3("🎯 Detections", style={'color': '#3498db'}),
                    html.P(id="total-detections", children="0", style={'fontSize': '24px', 'fontWeight': 'bold'}),
                    html.P("Total Threats Detected", style={'color': '#7f8c8d'})
                ], className="status-card", style={'backgroundColor': '#d6eaf8', 'padding': '20px', 'borderRadius': '10px', 'textAlign': 'center'}),
                
                # Alert Summary
                html.Div([
                    html.H3("🚨 Alerts", style={'color': '#f39c12'}),
                    html.P(id="alert-count", children="0", style={'fontSize': '24px', 'fontWeight': 'bold'}),
                    html.P("Active Alerts", style={'color': '#7f8c8d'})
                ], className="status-card", style={'backgroundColor': '#fdeaa7', 'padding': '20px', 'borderRadius': '10px', 'textAlign': 'center'})
            ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'}),
            
            # Charts Row 1
            html.Div([
                # Real-time Network Traffic
                html.Div([
                    dcc.Graph(id="network-traffic-chart")
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                # Risk Scores Over Time
                html.Div([
                    dcc.Graph(id="risk-scores-chart")
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            
            # Charts Row 2
            html.Div([
                # Threat Level Distribution
                html.Div([
                    dcc.Graph(id="threat-distribution-chart")
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                # Network vs User Risk Correlation
                html.Div([
                    dcc.Graph(id="risk-correlation-chart")
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            
            # Recent Alerts Table
            html.Div([
                html.H3("📋 Recent Alerts", style={'color': '#2c3e50'}),
                html.Div(id="alerts-table")
            ], style={'marginTop': '30px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px'}),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=5*1000,  # Update every 5 seconds
                n_intervals=0
            )
        ])
        
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output('system-status', 'children'),
             Output('uptime', 'children'),
             Output('current-threat', 'children'),
             Output('risk-score', 'children'),
             Output('total-detections', 'children'),
             Output('alert-count', 'children'),
             Output('network-traffic-chart', 'figure'),
             Output('risk-scores-chart', 'figure'),
             Output('threat-distribution-chart', 'figure'),
             Output('risk-correlation-chart', 'figure'),
             Output('alerts-table', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            return self.update_all_components()
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        def monitor():
            while True:
                try:
                    # Run detection cycle
                    network_results = self.ids.detect()
                    user_results = self.ueba.detect()
                    
                    # Process results
                    for net in network_results:
                        network_risk = net["network_risk"]
                        
                        # Find matching user
                        matched_user = next(
                            (u for u in user_results if u["ip"] == net["ip"]), 
                            None
                        )
                        user_risk = matched_user["user_risk"] if matched_user else 0.1
                        
                        # Combine risks
                        final_risk, threat_level = combine_risks(network_risk, user_risk)
                        
                        # Store data
                        timestamp = datetime.now()
                        self.data['timestamps'].append(timestamp)
                        self.data['network_in'].append(self.get_network_bytes())
                        self.data['packets_in'].append(self.get_network_packets())
                        self.data['network_risk'].append(network_risk)
                        self.data['user_risk'].append(user_risk)
                        self.data['final_risk'].append(final_risk)
                        self.data['threat_level'].append(threat_level)
                        
                        # Update statistics
                        self.stats['total_detections'] += 1
                        if threat_level == 'CRITICAL':
                            self.stats['critical_alerts'] += 1
                        elif threat_level == 'HIGH':
                            self.stats['high_alerts'] += 1
                        elif threat_level == 'MEDIUM':
                            self.stats['medium_alerts'] += 1
                        else:
                            self.stats['low_alerts'] += 1
                        
                        # Check for alerts
                        if final_risk > 0.4:  # MEDIUM or higher
                            self.create_alert(timestamp, threat_level, final_risk, network_risk, user_risk)
                    
                    time.sleep(10)  # Wait 10 seconds
                    
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    time.sleep(5)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def get_network_bytes(self):
        """Get current network bytes (from IDS engine)"""
        try:
            return self.ids.get_metric("NetworkIn")
        except:
            return 0
    
    def get_network_packets(self):
        """Get current network packets (from IDS engine)"""
        try:
            return self.ids.get_metric("NetworkPacketsIn")
        except:
            return 0
    
    def create_alert(self, timestamp, threat_level, final_risk, network_risk, user_risk):
        """Create and store alert"""
        alert = {
            'timestamp': timestamp,
            'level': threat_level,
            'final_risk': final_risk,
            'network_risk': network_risk,
            'user_risk': user_risk,
            'message': f"{threat_level} threat detected - Risk: {final_risk:.2f}"
        }
        self.data['alerts'].append(alert)
        
        # Send email alert for HIGH/CRITICAL
        if threat_level in ['HIGH', 'CRITICAL']:
            self.send_email_alert(alert)
    
    def send_email_alert(self, alert):
        """Send email alert (configure with your email settings)"""
        if not EMAIL_AVAILABLE:
            print("⚠️ Email functionality not available")
            return
            
        try:
            # Email configuration (update with your settings)
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "your-email@gmail.com"  # Update this
            sender_password = "your-app-password"   # Update this
            recipient_email = "admin@company.com"   # Update this
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"🚨 {alert['level']} Threat Alert - Hybrid Detection System"
            
            body = f"""
            THREAT ALERT DETECTED
            
            Timestamp: {alert['timestamp']}
            Threat Level: {alert['level']}
            Final Risk Score: {alert['final_risk']:.2f}
            Network Risk: {alert['network_risk']:.2f}
            User Risk: {alert['user_risk']:.2f}
            
            Message: {alert['message']}
            
            Please investigate immediately.
            
            - Hybrid Threat Detection System
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"Alert email sent for {alert['level']} threat")
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def update_all_components(self):
        """Update all dashboard components"""
        
        # System status
        uptime = datetime.now() - self.stats['uptime_start']
        uptime_str = f"Uptime: {str(uptime).split('.')[0]}"
        
        # Current threat level
        current_threat = self.data['threat_level'][-1] if self.data['threat_level'] else "LOW"
        current_risk = self.data['final_risk'][-1] if self.data['final_risk'] else 0.0
        risk_str = f"Risk Score: {current_risk:.2f}"
        
        # Alert count (active alerts in last hour)
        recent_alerts = [a for a in self.data['alerts'] 
                        if (datetime.now() - a['timestamp']).seconds < 3600]
        alert_count = len(recent_alerts)
        
        # Create charts
        network_chart = self.create_network_traffic_chart()
        risk_chart = self.create_risk_scores_chart()
        distribution_chart = self.create_threat_distribution_chart()
        correlation_chart = self.create_risk_correlation_chart()
        alerts_table = self.create_alerts_table()
        
        return (
            "ACTIVE",
            uptime_str,
            current_threat,
            risk_str,
            str(self.stats['total_detections']),
            str(alert_count),
            network_chart,
            risk_chart,
            distribution_chart,
            correlation_chart,
            alerts_table
        )
    
    def create_network_traffic_chart(self):
        """Create network traffic chart"""
        if not self.data['timestamps']:
            return go.Figure()
        
        fig = go.Figure()
        
        # Network bytes
        fig.add_trace(go.Scatter(
            x=list(self.data['timestamps']),
            y=list(self.data['network_in']),
            mode='lines+markers',
            name='Network In (bytes)',
            line=dict(color='#3498db', width=2)
        ))
        
        # Packets (secondary y-axis)
        fig.add_trace(go.Scatter(
            x=list(self.data['timestamps']),
            y=list(self.data['packets_in']),
            mode='lines+markers',
            name='Packets In',
            yaxis='y2',
            line=dict(color='#e74c3c', width=2)
        ))
        
        fig.update_layout(
            title="Real-time Network Traffic",
            xaxis_title="Time",
            yaxis=dict(title="Bytes", side="left"),
            yaxis2=dict(title="Packets", side="right", overlaying="y"),
            hovermode='x unified'
        )
        
        return fig
    
    def create_risk_scores_chart(self):
        """Create risk scores chart"""
        if not self.data['timestamps']:
            return go.Figure()
        
        fig = go.Figure()
        
        # Network risk
        fig.add_trace(go.Scatter(
            x=list(self.data['timestamps']),
            y=list(self.data['network_risk']),
            mode='lines+markers',
            name='Network Risk',
            line=dict(color='#e74c3c', width=2)
        ))
        
        # User risk
        fig.add_trace(go.Scatter(
            x=list(self.data['timestamps']),
            y=list(self.data['user_risk']),
            mode='lines+markers',
            name='User Risk',
            line=dict(color='#f39c12', width=2)
        ))
        
        # Final risk
        fig.add_trace(go.Scatter(
            x=list(self.data['timestamps']),
            y=list(self.data['final_risk']),
            mode='lines+markers',
            name='Final Risk',
            line=dict(color='#9b59b6', width=3)
        ))
        
        # Add threshold lines
        fig.add_hline(y=0.8, line_dash="dash", line_color="red", 
                     annotation_text="CRITICAL")
        fig.add_hline(y=0.6, line_dash="dash", line_color="orange", 
                     annotation_text="HIGH")
        fig.add_hline(y=0.4, line_dash="dash", line_color="yellow", 
                     annotation_text="MEDIUM")
        
        fig.update_layout(
            title="Risk Scores Over Time",
            xaxis_title="Time",
            yaxis_title="Risk Score (0-1)",
            yaxis=dict(range=[0, 1]),
            hovermode='x unified'
        )
        
        return fig
    
    def create_threat_distribution_chart(self):
        """Create threat level distribution pie chart"""
        levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        counts = [
            self.stats['critical_alerts'],
            self.stats['high_alerts'],
            self.stats['medium_alerts'],
            self.stats['low_alerts']
        ]
        colors = ['#e74c3c', '#f39c12', '#f1c40f', '#27ae60']
        
        fig = go.Figure(data=[go.Pie(
            labels=levels,
            values=counts,
            marker_colors=colors,
            hole=0.4
        )])
        
        fig.update_layout(
            title="Threat Level Distribution",
            annotations=[dict(text='Threats', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        return fig
    
    def create_risk_correlation_chart(self):
        """Create network vs user risk correlation scatter plot"""
        if not self.data['network_risk']:
            return go.Figure()
        
        fig = go.Figure()
        
        # Color by threat level
        colors = []
        for level in self.data['threat_level']:
            if level == 'CRITICAL':
                colors.append('#e74c3c')
            elif level == 'HIGH':
                colors.append('#f39c12')
            elif level == 'MEDIUM':
                colors.append('#f1c40f')
            else:
                colors.append('#27ae60')
        
        fig.add_trace(go.Scatter(
            x=list(self.data['network_risk']),
            y=list(self.data['user_risk']),
            mode='markers',
            marker=dict(
                color=colors,
                size=8,
                opacity=0.7
            ),
            text=[f"Final Risk: {r:.2f}" for r in self.data['final_risk']],
            hovertemplate="Network Risk: %{x}<br>User Risk: %{y}<br>%{text}<extra></extra>"
        ))
        
        fig.update_layout(
            title="Network vs User Risk Correlation",
            xaxis_title="Network Risk",
            yaxis_title="User Risk",
            xaxis=dict(range=[0, 1]),
            yaxis=dict(range=[0, 1])
        )
        
        return fig
    
    def create_alerts_table(self):
        """Create recent alerts table"""
        if not self.data['alerts']:
            return html.P("No recent alerts", style={'textAlign': 'center', 'color': '#7f8c8d'})
        
        # Get last 10 alerts
        recent_alerts = list(self.data['alerts'])[-10:]
        recent_alerts.reverse()  # Most recent first
        
        table_rows = []
        for alert in recent_alerts:
            # Color based on threat level
            if alert['level'] == 'CRITICAL':
                row_color = '#fadbd8'
            elif alert['level'] == 'HIGH':
                row_color = '#fdeaa7'
            elif alert['level'] == 'MEDIUM':
                row_color = '#fff3cd'
            else:
                row_color = '#d1ecf1'
            
            row = html.Tr([
                html.Td(alert['timestamp'].strftime('%H:%M:%S')),
                html.Td(alert['level'], style={'fontWeight': 'bold'}),
                html.Td(f"{alert['final_risk']:.2f}"),
                html.Td(f"{alert['network_risk']:.2f}"),
                html.Td(f"{alert['user_risk']:.2f}"),
                html.Td(alert['message'])
            ], style={'backgroundColor': row_color})
            
            table_rows.append(row)
        
        table = html.Table([
            html.Thead([
                html.Tr([
                    html.Th("Time"),
                    html.Th("Level"),
                    html.Th("Final Risk"),
                    html.Th("Network Risk"),
                    html.Th("User Risk"),
                    html.Th("Message")
                ])
            ]),
            html.Tbody(table_rows)
        ], style={'width': '100%', 'borderCollapse': 'collapse'})
        
        return table
    
    def run(self, debug=False, port=8050):
        """Run the dashboard"""
        print("Starting Hybrid Threat Detection Dashboard...")
        print(f"Dashboard will be available at: http://localhost:{port}")
        print("Auto-refresh every 5 seconds")
        print("Email alerts configured for HIGH/CRITICAL threats")
        self.app.run(debug=debug, port=port, host='0.0.0.0')

if __name__ == '__main__':
    dashboard = ThreatDashboard()
    dashboard.run(debug=True)