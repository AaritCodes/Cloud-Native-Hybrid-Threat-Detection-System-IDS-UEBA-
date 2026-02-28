try:
    from src.ids_engine import IDSEngine
    from src.ueba_engine import UEBAEngine
    from src.threat_fusion_engine import combine_risks
    from src.alert_system import AlertSystem
except ModuleNotFoundError:
    from ids_engine import IDSEngine
    from ueba_engine import UEBAEngine
    from threat_fusion_engine import combine_risks
    from alert_system import AlertSystem
import time
import warnings
import json
from datetime import datetime

warnings.filterwarnings("ignore")

class EnhancedThreatDetectionSystem:
    def __init__(self):
        print("🚀 Initializing Enhanced Hybrid Threat Detection System...")
        
        # Initialize engines
        self.ids = IDSEngine("models/ddos_model.pkl")
        self.ueba = UEBAEngine("models/uba_model.pkl")
        
        # Initialize alert system
        self.alert_system = AlertSystem()
        
        # Statistics tracking
        self.stats = {
            "total_cycles": 0,
            "threats_detected": 0,
            "start_time": datetime.now()
        }
        
        print("✅ System initialized successfully!")
        print("📧 Email alerts configured for HIGH/CRITICAL threats")
        print("📊 Dashboard available at: http://localhost:8050 (run dashboard.py)")
        print("🔄 Starting detection cycles...\n")
    
    def run_detection_cycle(self):
        """Run a single detection cycle"""
        try:
            print("===== Hybrid Threat Detection Cycle =====")
            
            # Run IDS
            print("Running IDS...")
            network_results = self.ids.detect()
            print("IDS Done")
            
            # Run UEBA
            print("Running UEBA...")
            user_results = self.ueba.detect()
            print("UEBA Done")
            
            # Process results
            print("Network Results:", network_results)
            print("User Results:", len(user_results), "user activities detected")
            
            for net in network_results:
                ip = net["ip"]
                network_risk = net["network_risk"]
                
                # Find matching user
                matched_user = next(
                    (u for u in user_results if u["ip"] == ip),
                    None
                )
                user_risk = matched_user["user_risk"] if matched_user else 0.1
                
                # Combine risks
                final_risk, level = combine_risks(network_risk, user_risk)
                
                # Get network metrics for alert
                network_bytes = self.ids.get_metric("NetworkIn")
                network_packets = self.ids.get_metric("NetworkPacketsIn")
                
                # Display results
                print(f"""
IP: {ip}
Network Risk: {network_risk:.2f}
User Risk: {user_risk:.2f}
Final Risk: {final_risk:.2f}
Threat Level: {level}
Network Traffic: {network_bytes:,.0f} bytes, {network_packets:,.0f} packets
""")
                
                # Create alert if threat detected
                if final_risk > 0.3:  # Alert for MEDIUM and above
                    self.alert_system.create_alert(
                        threat_level=level,
                        final_risk=final_risk,
                        network_risk=network_risk,
                        user_risk=user_risk,
                        network_bytes=network_bytes,
                        network_packets=network_packets
                    )
                    self.stats["threats_detected"] += 1
            
            # Update statistics
            self.stats["total_cycles"] += 1
            
            # Show periodic statistics
            if self.stats["total_cycles"] % 10 == 0:
                self.show_statistics()
                
        except Exception as e:
            print(f"❌ Error in detection cycle: {e}")
    
    def show_statistics(self):
        """Show system statistics"""
        uptime = datetime.now() - self.stats["start_time"]
        alert_stats = self.alert_system.get_alert_statistics()
        
        print(f"\n📊 SYSTEM STATISTICS")
        print(f"{'='*50}")
        print(f"⏰ Uptime: {str(uptime).split('.')[0]}")
        print(f"🔄 Detection Cycles: {self.stats['total_cycles']}")
        print(f"🎯 Threats Detected: {self.stats['threats_detected']}")
        print(f"🚨 Total Alerts: {alert_stats['total']}")
        print(f"   - CRITICAL: {alert_stats.get('critical', 0)}")
        print(f"   - HIGH: {alert_stats.get('high', 0)}")
        print(f"   - MEDIUM: {alert_stats.get('medium', 0)}")
        print(f"   - LOW: {alert_stats.get('low', 0)}")
        print(f"{'='*50}\n")
    
    def run(self):
        """Main detection loop"""
        try:
            while True:
                self.run_detection_cycle()
                time.sleep(10)  # Wait 10 seconds between cycles
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping Hybrid Threat Detection System...")
            self.show_statistics()
            print("👋 System stopped gracefully.")
        except Exception as e:
            print(f"❌ Critical error: {e}")
            self.show_statistics()

if __name__ == "__main__":
    system = EnhancedThreatDetectionSystem()
    system.run()