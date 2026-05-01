"""
Enhanced Hybrid Threat Detection System with Autonomous Response Agent

This module integrates the IDS, UEBA, Threat Fusion, Alert System,
and Autonomous Response Agent into a complete security solution.

Author: Hybrid Threat Detection Team
Date: 2026
"""

import sys
import os

# Fix Windows console encoding for emoji/unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

try:
    from src.ids_engine import IDSEngine
    from src.ueba_engine import UEBAEngine
    from src.threat_fusion_engine import combine_risks
    from src.alert_system import AlertSystem
    from src.autonomous_response_agent import AutonomousResponseAgent
except ModuleNotFoundError:
    from ids_engine import IDSEngine
    from ueba_engine import UEBAEngine
    from threat_fusion_engine import combine_risks
    from alert_system import AlertSystem
    from autonomous_response_agent import AutonomousResponseAgent

import time
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")


class EnhancedThreatDetectionSystemWithAgent:
    """
    Complete threat detection and response system with autonomous capabilities.
    
    Components:
    1. IDS Engine - Network monitoring
    2. UEBA Engine - User behavior analytics
    3. Threat Fusion - Risk correlation
    4. Alert System - Multi-channel notifications
    5. Autonomous Response Agent - Automated threat response
    """
    
    def __init__(
        self,
        security_group_id: str,
        enable_autonomous_response: bool = True
    ):
        """
        Initialize the enhanced threat detection system.
        
        Args:
            security_group_id: AWS Security Group ID for IP blocking
            enable_autonomous_response: Enable/disable autonomous actions
        """
        print("🚀 Initializing Enhanced Hybrid Threat Detection System with Autonomous Response...")
        
        # Initialize detection engines
        self.ids = IDSEngine("models/ddos_model.pkl")
        self.ueba = UEBAEngine("models/uba_model.pkl")
        
        # Initialize alert system
        self.alert_system = AlertSystem()
        
        # Initialize autonomous response agent
        self.enable_autonomous_response = enable_autonomous_response
        if enable_autonomous_response:
            self.response_agent = AutonomousResponseAgent(
                security_group_id=security_group_id,
                region="ap-south-1",
                block_timeout_minutes=10,
                monitoring_interval=60,  # Check every 60 seconds as per requirements
                waf_ip_set_name="AgenticRateLimitIPSet",
                waf_ip_set_id="7ef55e05-d14d-4315-a6e3-7d98b6869b89",
                waf_scope="REGIONAL"
            )
            print("✅ Autonomous Response Agent enabled")
        else:
            self.response_agent = None
            print("⚠️  Autonomous Response Agent disabled (manual mode)")
        
        # Statistics tracking and Dashboard State
        import json
        from collections import deque
        
        self.stats = {
            "total_cycles": 0,
            "threats_detected": 0,
            "autonomous_actions": 0,
            "start_time": datetime.now()
        }
        
        # State object strictly for the Thin client Web Dashboard
        self.web_state = {
            "timestamps": deque(maxlen=50),
            "network_risk": deque(maxlen=50),
            "user_risk": deque(maxlen=50),
            "final_risk": deque(maxlen=50),
            "actions": deque(maxlen=50),
            "events": deque(maxlen=20),
            "stats": {
                "total_cycles": 0,
                "log_count": 0,
                "alert_count": 0,
                "rate_limit_count": 0,
                "block_count": 0,
                "ai_available": self.enable_autonomous_response,
                "model": "agentic-response-ai",
                "start_time": datetime.now().isoformat(),
            },
            "latest": {
                "network_risk": 0,
                "user_risk": 0,
                "final_risk": 0,
                "action": "LOG",
                "reasoning": "Waiting for detections...",
                "confidence": 0,
                "threat_level": "LOW",
                "tools_used": [],
            },
        }
        
        print("✅ System initialized successfully!")
        print("📧 Email alerts configured for HIGH/CRITICAL threats")
        print("🤖 Autonomous response ready for CRITICAL threats")
        print("🔄 Starting detection cycles...\n")
    
    def run_detection_cycle(self):
        """Run a single detection cycle with autonomous response."""
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
                
                # Use network metrics already fetched by detect()
                network_bytes = net.get("network_bytes", 0)
                network_packets = net.get("network_packets", 0)
                
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
                
                action_taken = "LOG"
                # Autonomous response (if enabled)
                if self.enable_autonomous_response and self.response_agent:
                    print("\n🤖 Autonomous Response Agent evaluating threat...")
                    
                    action = self.response_agent.take_action(
                        ip_address=ip,
                        risk_score=final_risk,
                        network_risk=network_risk,
                        user_risk=user_risk
                    )
                    action_taken = action
                    
                    if action in ["ALERT", "RATE_LIMIT", "BLOCK"]:
                        self.stats["autonomous_actions"] += 1
                        self.web_state["stats"][f"{action.lower()}_count"] += 1
                    else:
                        self.web_state["stats"]["log_count"] += 1
                    
                    print(f"✅ Autonomous action taken: {action}")
                    
                    # Check for expired blocks
                    self.response_agent.check_and_unblock_expired()
                
                # Update web state
                now = datetime.now()
                self.web_state["timestamps"].append(now.isoformat())
                self.web_state["network_risk"].append(float(network_risk))
                self.web_state["user_risk"].append(float(user_risk))
                self.web_state["final_risk"].append(float(final_risk))
                self.web_state["actions"].append(action_taken)
                
                self.web_state["stats"]["total_cycles"] += 1
                
                self.web_state["latest"] = {
                    "network_risk": float(network_risk),
                    "user_risk": float(user_risk),
                    "final_risk": float(final_risk),
                    "action": action_taken,
                    "reasoning": f"Enhanced Engine decided action: {action_taken}. (See terminal for complete Live AI Reasoning process)",
                    "confidence": 0.85,
                    "threat_level": level,
                    "tools_used": ["ids_engine", "ueba_engine", "response_agent"] if self.enable_autonomous_response else ["ids_engine", "ueba_engine"],
                }
                
                self.web_state["events"].append({
                    "time": now.strftime("%H:%M:%S"),
                    "action": action_taken,
                    "msg": f"IP: {ip} | Net: {network_risk:.2f} User: {user_risk:.2f} → Risk {final_risk:.2f} ({level})",
                })
                
                # Write to json file
                try:
                    state_to_save = {
                        "timestamps": list(self.web_state["timestamps"]),
                        "network_risk": list(self.web_state["network_risk"]),
                        "user_risk": list(self.web_state["user_risk"]),
                        "final_risk": list(self.web_state["final_risk"]),
                        "actions": list(self.web_state["actions"]),
                        "events": list(self.web_state["events"]),
                        "stats": self.web_state["stats"],
                        "latest": self.web_state["latest"],
                    }
                    import json
                    with open("web_state.json", "w") as f:
                        json.dump(state_to_save, f)
                except Exception as e:
                    print(f"Failed to write dashboard state: {e}")
            
            # Update statistics
            self.stats["total_cycles"] += 1
            
            # Show periodic statistics
            if self.stats["total_cycles"] % 10 == 0:
                self.show_statistics()
                
        except Exception as e:
            print(f"❌ Error in detection cycle: {e}")
    
    def show_statistics(self):
        """Show system statistics including autonomous response and AI accuracy metrics."""
        uptime = datetime.now() - self.stats["start_time"]
        alert_stats = self.alert_system.get_alert_statistics()
        
        print(f"\n📊 SYSTEM STATISTICS")
        print(f"{'='*50}")
        print(f"⏰ Uptime: {str(uptime).split('.')[0]}")
        print(f"🔄 Detection Cycles: {self.stats['total_cycles']}")
        print(f"🎯 Threats Detected: {self.stats['threats_detected']}")
        print(f"🤖 Autonomous Actions: {self.stats['autonomous_actions']}")
        print(f"🚨 Total Alerts: {alert_stats['total']}")
        print(f"   - CRITICAL: {alert_stats.get('critical', 0)}")
        print(f"   - HIGH: {alert_stats.get('high', 0)}")
        print(f"   - MEDIUM: {alert_stats.get('medium', 0)}")
        print(f"   - LOW: {alert_stats.get('low', 0)}")
        
        if self.enable_autonomous_response and self.response_agent:
            agent_stats = self.response_agent.get_statistics()
            print(f"\n🤖 AUTONOMOUS RESPONSE STATISTICS")
            print(f"   - IPs Blocked: {agent_stats['total_blocks']}")
            print(f"   - IPs Unblocked: {agent_stats['total_unblocks']}")
            print(f"   - Currently Blocked: {agent_stats['currently_blocked']}")
            print(f"   - Rate Limits Applied: {agent_stats['total_rate_limits']}")
            
            # Show AI learning metrics
            if "ai_agent" in agent_stats:
                ai = agent_stats["ai_agent"]
                print(f"\n🧠 AGENTIC AI LEARNING METRICS")
                print(f"   - Agent Type: {ai.get('agent_type', 'unknown')}")
                print(f"   - Model: {ai.get('model', 'unknown')}")
                print(f"   - Total Decisions in Memory: {ai.get('total_decisions', 0)}")
                accuracy = ai.get("accuracy", {})
                if accuracy.get("total_evaluated", 0) > 0:
                    print(f"   - Accuracy: {accuracy.get('accuracy', 0):.1%}")
                    print(f"   - Precision: {accuracy.get('precision', 0):.1%}")
                    print(f"   - Recall: {accuracy.get('recall', 0):.1%}")
                    print(f"   - F1 Score: {accuracy.get('f1_score', 0):.1%}")
                thresholds = ai.get("adaptive_thresholds", {})
                if thresholds.get("status") == "adjusted":
                    print(f"   - Threshold Adjustment: {thresholds.get('reason', 'none')}")
        
        print(f"{'='*50}\n")
    
    def run(self):
        """Main detection loop with autonomous response."""
        try:
            while True:
                self.run_detection_cycle()
                time.sleep(15)  # Wait 15 seconds between cycles for faster detection
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping Hybrid Threat Detection System...")
            self.show_statistics()
            
            if self.enable_autonomous_response and self.response_agent:
                print("\n🤖 Autonomous Response Agent Statistics:")
                self.response_agent.display_statistics()
            
            print("👋 System stopped gracefully.")
            
        except Exception as e:
            print(f"❌ Critical error: {e}")
            self.show_statistics()


if __name__ == "__main__":
    """
    Main entry point for the enhanced threat detection system.
    
    Configuration:
    1. Set your AWS Security Group ID below
    2. Ensure AWS credentials are configured (IAM role or ~/.aws/credentials)
    3. Verify IAM permissions for EC2 Security Group modifications
    """
    
    # ========== CONFIGURATION ==========
    
    # Your AWS Security Group ID (replace with actual ID)
    SECURITY_GROUP_ID = "sg-096157899840a1547"  # Your EC2 Security Group (ap-south-1)
    
    # Enable/disable autonomous response
    ENABLE_AUTONOMOUS_RESPONSE = True  # Set to False for monitoring only
    
    # ===================================
    
    print(f"\n{'='*70}")
    print(f"🛡️  Hybrid Threat Detection System with Autonomous Response")
    print(f"{'='*70}")
    print(f"🔒 Security Group: {SECURITY_GROUP_ID}")
    print(f"🤖 Autonomous Response: {'ENABLED' if ENABLE_AUTONOMOUS_RESPONSE else 'DISABLED'}")
    print(f"{'='*70}\n")
    
    # Initialize and start system
    system = EnhancedThreatDetectionSystemWithAgent(
        security_group_id=SECURITY_GROUP_ID,
        enable_autonomous_response=ENABLE_AUTONOMOUS_RESPONSE
    )
    
    system.run()
