import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict
import logging

# Email imports
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
EMAIL_AVAILABLE = True

@dataclass
class Alert:
    timestamp: datetime
    threat_level: str
    final_risk: float
    network_risk: float
    user_risk: float
    network_bytes: float
    network_packets: float
    message: str
    ip_address: str = "EC2_INSTANCE"

class AlertSystem:
    def __init__(self, config_file="config/alert_config.json"):
        self.config_file = config_file
        self.load_config()
        self.setup_logging()
        self.alert_history = []
        
    def load_config(self):
        """Load alert configuration"""
        default_config = {
            "email": {
                "enabled": True,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your-email@gmail.com",
                "sender_password": "your-app-password",
                "recipients": ["admin@company.com", "security@company.com"]
            },
            "thresholds": {
                "critical": 0.8,
                "high": 0.6,
                "medium": 0.4,
                "email_threshold": 0.6  # Send email for HIGH and CRITICAL
            },
            "rate_limiting": {
                "max_emails_per_hour": 10,
                "cooldown_minutes": 5
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_logging(self):
        """Setup logging for alerts"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('threat_alerts.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_alert(self, threat_level: str, final_risk: float, 
                    network_risk: float, user_risk: float,
                    network_bytes: float = 0, network_packets: float = 0) -> Alert:
        """Create a new alert"""
        
        # Generate alert message
        if threat_level == "CRITICAL":
            message = f"🚨 CRITICAL THREAT DETECTED! Immediate action required."
        elif threat_level == "HIGH":
            message = f"⚠️ HIGH THREAT detected. Investigation needed."
        elif threat_level == "MEDIUM":
            message = f"⚡ MEDIUM threat detected. Monitor closely."
        else:
            message = f"ℹ️ LOW threat level. Normal monitoring."
        
        alert = Alert(
            timestamp=datetime.now(),
            threat_level=threat_level,
            final_risk=final_risk,
            network_risk=network_risk,
            user_risk=user_risk,
            network_bytes=network_bytes,
            network_packets=network_packets,
            message=message
        )
        
        # Store alert
        self.alert_history.append(alert)
        
        # Log alert
        self.logger.info(f"ALERT: {threat_level} - Risk: {final_risk:.2f} - {message}")
        
        # Process alert
        self.process_alert(alert)
        
        return alert
    
    def process_alert(self, alert: Alert):
        """Process alert based on configuration"""
        
        # Console notification
        self.console_notification(alert)
        
        # Email notification
        if (alert.final_risk >= self.config["thresholds"]["email_threshold"] and 
            self.config["email"]["enabled"]):
            self.send_email_alert(alert)
        
        # Save to file
        self.save_alert_to_file(alert)
        
        # Could add more notification methods here:
        # - Slack webhook
        # - SMS via Twilio
        # - Push notifications
        # - SIEM integration
    
    def console_notification(self, alert: Alert):
        """Display alert in console with colors"""
        colors = {
            "CRITICAL": "\033[91m",  # Red
            "HIGH": "\033[93m",      # Yellow
            "MEDIUM": "\033[94m",    # Blue
            "LOW": "\033[92m",       # Green
            "RESET": "\033[0m"       # Reset
        }
        
        color = colors.get(alert.threat_level, colors["RESET"])
        
        print(f"\n{color}{'='*60}")
        print(f"🚨 THREAT ALERT - {alert.threat_level}")
        print(f"{'='*60}{colors['RESET']}")
        print(f"⏰ Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 IP: {alert.ip_address}")
        print(f"📊 Final Risk: {alert.final_risk:.2f}")
        print(f"🌐 Network Risk: {alert.network_risk:.2f}")
        print(f"👤 User Risk: {alert.user_risk:.2f}")
        print(f"📈 Network Traffic: {alert.network_bytes:,.0f} bytes, {alert.network_packets:,.0f} packets")
        print(f"💬 Message: {alert.message}")
        print(f"{color}{'='*60}{colors['RESET']}\n")
    
    def send_email_alert(self, alert: Alert):
        """Send email alert"""
        if not EMAIL_AVAILABLE:
            self.logger.warning("Email functionality not available. Skipping email alert.")
            return
            
        try:
            # Check rate limiting
            if not self.check_rate_limit():
                self.logger.warning("Email rate limit exceeded. Skipping email alert.")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config["email"]["sender_email"]
            msg['To'] = ", ".join(self.config["email"]["recipients"])
            msg['Subject'] = f"🚨 {alert.threat_level} Threat Alert - Hybrid Detection System"
            
            # Email body
            body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert-header {{ background-color: {'#e74c3c' if alert.threat_level in ['CRITICAL', 'HIGH'] else '#f39c12'}; 
                        color: white; padding: 20px; text-align: center; }}
        .alert-content {{ padding: 20px; }}
        .metric {{ margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #007bff; }}
        .critical {{ border-left-color: #e74c3c; }}
        .high {{ border-left-color: #f39c12; }}
        .medium {{ border-left-color: #f1c40f; }}
        .low {{ border-left-color: #27ae60; }}
    </style>
</head>
<body>
    <div class="alert-header">
        <h1>🚨 {alert.threat_level} THREAT DETECTED</h1>
        <p>Hybrid Threat Detection System Alert</p>
    </div>
    
    <div class="alert-content">
        <h2>Alert Details</h2>
        
        <div class="metric {alert.threat_level.lower()}">
            <strong>⏰ Timestamp:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        
        <div class="metric">
            <strong>🎯 Target IP:</strong> {alert.ip_address}
        </div>
        
        <div class="metric">
            <strong>📊 Final Risk Score:</strong> {alert.final_risk:.2f} / 1.00
        </div>
        
        <div class="metric">
            <strong>🌐 Network Risk:</strong> {alert.network_risk:.2f} / 1.00
        </div>
        
        <div class="metric">
            <strong>👤 User Risk:</strong> {alert.user_risk:.2f} / 1.00
        </div>
        
        <div class="metric">
            <strong>📈 Network Traffic:</strong> {alert.network_bytes:,.0f} bytes, {alert.network_packets:,.0f} packets
        </div>
        
        <div class="metric">
            <strong>💬 Alert Message:</strong> {alert.message}
        </div>
        
        <h2>Recommended Actions</h2>
        <ul>
            {"<li>🔴 <strong>IMMEDIATE INVESTIGATION REQUIRED</strong> - Potential active attack</li>" if alert.threat_level == "CRITICAL" else ""}
            {"<li>🟡 Investigate network traffic patterns and user activities</li>" if alert.threat_level in ["HIGH", "CRITICAL"] else ""}
            <li>📊 Review CloudWatch metrics and CloudTrail logs</li>
            <li>🔍 Check for additional indicators of compromise</li>
            <li>📞 Contact security team if threat persists</li>
        </ul>
        
        <hr>
        <p><small>This alert was generated by the Hybrid Threat Detection System.<br>
        For support, contact your security team.</small></p>
    </div>
</body>
</html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.config["email"]["smtp_server"], 
                                self.config["email"]["smtp_port"])
            server.starttls()
            server.login(self.config["email"]["sender_email"], 
                        self.config["email"]["sender_password"])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent for {alert.threat_level} threat")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def check_rate_limit(self) -> bool:
        """Check if we can send another email (rate limiting)"""
        now = datetime.now()
        hour_ago = now.replace(minute=0, second=0, microsecond=0)
        
        # Count emails sent in the last hour
        recent_emails = [a for a in self.alert_history 
                        if a.timestamp >= hour_ago and 
                        a.final_risk >= self.config["thresholds"]["email_threshold"]]
        
        return len(recent_emails) < self.config["rate_limiting"]["max_emails_per_hour"]
    
    def save_alert_to_file(self, alert: Alert):
        """Save alert to JSON file"""
        try:
            alert_data = {
                "timestamp": alert.timestamp.isoformat(),
                "threat_level": alert.threat_level,
                "final_risk": alert.final_risk,
                "network_risk": alert.network_risk,
                "user_risk": alert.user_risk,
                "network_bytes": alert.network_bytes,
                "network_packets": alert.network_packets,
                "message": alert.message,
                "ip_address": alert.ip_address
            }
            
            # Append to alerts file
            alerts_file = "threat_alerts.json"
            alerts = []
            
            if os.path.exists(alerts_file):
                try:
                    with open(alerts_file, 'r') as f:
                        alerts = json.load(f)
                except:
                    alerts = []
            
            alerts.append(alert_data)
            
            # Keep only last 1000 alerts
            if len(alerts) > 1000:
                alerts = alerts[-1000:]
            
            with open(alerts_file, 'w') as f:
                json.dump(alerts, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save alert to file: {e}")
    
    def get_alert_statistics(self) -> Dict:
        """Get alert statistics"""
        if not self.alert_history:
            return {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
        
        stats = {"total": len(self.alert_history)}
        
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            stats[level.lower()] = len([a for a in self.alert_history 
                                       if a.threat_level == level])
        
        return stats
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from the last N hours"""
        cutoff = datetime.now().replace(hour=datetime.now().hour - hours)
        return [a for a in self.alert_history if a.timestamp >= cutoff]

# Example usage and testing
if __name__ == "__main__":
    # Create alert system
    alert_system = AlertSystem()
    
    # Test different alert levels
    print("🧪 Testing Alert System...")
    
    # LOW alert
    alert_system.create_alert("LOW", 0.2, 0.1, 0.3, 1000, 50)
    
    # MEDIUM alert
    alert_system.create_alert("MEDIUM", 0.5, 0.6, 0.2, 50000, 500)
    
    # HIGH alert
    alert_system.create_alert("HIGH", 0.7, 0.8, 0.3, 500000, 5000)
    
    # CRITICAL alert
    alert_system.create_alert("CRITICAL", 0.9, 0.95, 0.8, 2000000, 25000)
    
    # Show statistics
    stats = alert_system.get_alert_statistics()
    print(f"\n📊 Alert Statistics: {stats}")
    
    print("\n✅ Alert system test completed!")
    print("📧 Check your email for HIGH/CRITICAL alerts (if configured)")
    print("📄 Check 'threat_alerts.log' and 'threat_alerts.json' for saved alerts")