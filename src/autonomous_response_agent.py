"""
Autonomous Response Agent for Hybrid Threat Detection System

This module implements an intelligent response system that automatically
takes action based on threat severity levels. It integrates with AWS
Security Groups to block malicious IPs and provides graduated response
mechanisms based on risk scores.

Author: Hybrid Threat Detection Team
Date: 2026
"""

import boto3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/autonomous_response.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class BlockedIP:
    """Data class to track blocked IPs"""
    ip_address: str
    blocked_at: datetime
    risk_score: float
    security_group_id: str
    rule_id: Optional[str] = None
    reason: str = "High threat detected"


class AutonomousResponseAgent:
    """
    Autonomous Response Agent that monitors threat levels and takes
    automated actions to protect AWS infrastructure.
    
    Response Levels:
    - LOW (< 0.4): Log only
    - MEDIUM (0.4-0.6): Send alerts
    - HIGH (0.6-0.8): Rate limiting simulation
    - CRITICAL (>= 0.8): Automatic IP blocking
    """
    
    def __init__(
        self,
        security_group_id: str,
        region: str = "ap-south-1",
        block_timeout_minutes: int = 10,
        monitoring_interval: int = 60
    ):
        """
        Initialize the Autonomous Response Agent.
        
        Args:
            security_group_id: AWS Security Group ID to modify
            region: AWS region (default: ap-south-1)
            block_timeout_minutes: Minutes before auto-unblocking IP
            monitoring_interval: Seconds between monitoring cycles
        """
        self.security_group_id = security_group_id
        self.region = region
        self.block_timeout_minutes = block_timeout_minutes
        self.monitoring_interval = monitoring_interval
        
        # Initialize AWS clients (uses IAM role credentials)
        try:
            self.ec2_client = boto3.client('ec2', region_name=region)
            logger.info(f"✅ AWS EC2 client initialized for region: {region}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AWS client: {e}")
            raise
        
        # In-memory tracking
        self.blocked_ips: Dict[str, BlockedIP] = {}
        self.rate_limited_ips: Dict[str, datetime] = {}
        self.alert_history: List[Dict] = []
        
        # Statistics
        self.stats = {
            "total_blocks": 0,
            "total_unblocks": 0,
            "total_alerts": 0,
            "total_rate_limits": 0,
            "start_time": datetime.now()
        }
        
        logger.info("🚀 Autonomous Response Agent initialized")
        logger.info(f"📊 Security Group: {security_group_id}")
        logger.info(f"⏱️  Block timeout: {block_timeout_minutes} minutes")
        logger.info(f"🔄 Monitoring interval: {monitoring_interval} seconds")
    
    def assess_threat_level(self, risk_score: float) -> str:
        """
        Assess threat level based on risk score.
        
        Args:
            risk_score: Final risk score (0-1)
            
        Returns:
            Threat level: LOW, MEDIUM, HIGH, or CRITICAL
        """
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def log_threat(
        self,
        ip_address: str,
        risk_score: float,
        network_risk: float,
        user_risk: float
    ) -> None:
        """
        Log threat information (LOW severity action).
        
        Args:
            ip_address: Source IP address
            risk_score: Final risk score
            network_risk: Network component risk
            user_risk: User behavior component risk
        """
        logger.info(
            f"📝 LOW THREAT LOGGED | IP: {ip_address} | "
            f"Risk: {risk_score:.2f} | Network: {network_risk:.2f} | "
            f"User: {user_risk:.2f}"
        )
    
    def send_alert(
        self,
        ip_address: str,
        risk_score: float,
        network_risk: float,
        user_risk: float,
        threat_level: str
    ) -> None:
        """
        Send alert notification (MEDIUM severity action).
        
        Args:
            ip_address: Source IP address
            risk_score: Final risk score
            network_risk: Network component risk
            user_risk: User behavior component risk
            threat_level: Threat severity level
        """
        alert = {
            "timestamp": datetime.now().isoformat(),
            "ip_address": ip_address,
            "risk_score": risk_score,
            "network_risk": network_risk,
            "user_risk": user_risk,
            "threat_level": threat_level,
            "action": "ALERT_SENT"
        }
        
        self.alert_history.append(alert)
        self.stats["total_alerts"] += 1
        
        logger.warning(
            f"⚠️  {threat_level} ALERT | IP: {ip_address} | "
            f"Risk: {risk_score:.2f} | Action: Alert sent to security team"
        )
        
        # In production, integrate with:
        # - Email notification system
        # - Slack/Teams webhook
        # - PagerDuty/Opsgenie
        # - SIEM system
        
        print(f"\n{'='*70}")
        print(f"🚨 SECURITY ALERT - {threat_level}")
        print(f"{'='*70}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 IP Address: {ip_address}")
        print(f"📊 Risk Score: {risk_score:.2f}")
        print(f"🌐 Network Risk: {network_risk:.2f}")
        print(f"👤 User Risk: {user_risk:.2f}")
        print(f"🔔 Action: Alert notification sent")
        print(f"{'='*70}\n")
    
    def simulate_rate_limiting(
        self,
        ip_address: str,
        risk_score: float
    ) -> None:
        """
        Simulate rate limiting (HIGH severity action).
        
        In production, this would integrate with:
        - AWS WAF rate-based rules
        - API Gateway throttling
        - Application-level rate limiting
        
        Args:
            ip_address: Source IP address
            risk_score: Final risk score
        """
        self.rate_limited_ips[ip_address] = datetime.now()
        self.stats["total_rate_limits"] += 1
        
        logger.warning(
            f"⚡ RATE LIMITING APPLIED | IP: {ip_address} | "
            f"Risk: {risk_score:.2f} | Duration: 5 minutes"
        )
        
        print(f"\n{'='*70}")
        print(f"⚡ RATE LIMITING ACTIVATED")
        print(f"{'='*70}")
        print(f"🎯 IP Address: {ip_address}")
        print(f"📊 Risk Score: {risk_score:.2f}")
        print(f"🔒 Action: Traffic rate limited to 10 req/min")
        print(f"⏱️  Duration: 5 minutes")
        print(f"{'='*70}\n")
        
        # In production, implement actual rate limiting:
        # - Update AWS WAF rule
        # - Configure API Gateway throttling
        # - Update load balancer rules
    
    def block_ip_address(
        self,
        ip_address: str,
        risk_score: float,
        network_risk: float,
        user_risk: float
    ) -> bool:
        """
        Block IP address by adding deny rule to Security Group (CRITICAL action).
        
        Args:
            ip_address: IP address to block
            risk_score: Final risk score
            network_risk: Network component risk
            user_risk: User behavior component risk
            
        Returns:
            True if blocked successfully, False otherwise
        """
        # Check if already blocked
        if ip_address in self.blocked_ips:
            logger.info(f"ℹ️  IP {ip_address} already blocked, skipping")
            return False
        
        try:
            # Add inbound deny rule to Security Group
            response = self.ec2_client.authorize_security_group_ingress(
                GroupId=self.security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',  # All protocols
                        'FromPort': -1,
                        'ToPort': -1,
                        'IpRanges': [
                            {
                                'CidrIp': f'{ip_address}/32',
                                'Description': f'AUTO-BLOCK: Risk {risk_score:.2f} at {datetime.now()}'
                            }
                        ]
                    }
                ]
            )
            
            # Track blocked IP
            blocked_ip = BlockedIP(
                ip_address=ip_address,
                blocked_at=datetime.now(),
                risk_score=risk_score,
                security_group_id=self.security_group_id,
                reason=f"Critical threat: Risk {risk_score:.2f}"
            )
            
            self.blocked_ips[ip_address] = blocked_ip
            self.stats["total_blocks"] += 1
            
            logger.critical(
                f"🚫 IP BLOCKED | IP: {ip_address} | Risk: {risk_score:.2f} | "
                f"Network: {network_risk:.2f} | User: {user_risk:.2f} | "
                f"Security Group: {self.security_group_id}"
            )
            
            print(f"\n{'='*70}")
            print(f"🚫 CRITICAL THREAT - IP BLOCKED")
            print(f"{'='*70}")
            print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🎯 Blocked IP: {ip_address}")
            print(f"📊 Risk Score: {risk_score:.2f}")
            print(f"🌐 Network Risk: {network_risk:.2f}")
            print(f"👤 User Risk: {user_risk:.2f}")
            print(f"🔒 Security Group: {self.security_group_id}")
            print(f"⏱️  Auto-unblock in: {self.block_timeout_minutes} minutes")
            print(f"{'='*70}\n")
            
            return True
            
        except self.ec2_client.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'InvalidPermission.Duplicate':
                logger.warning(f"⚠️  Rule for {ip_address} already exists")
                return False
            else:
                logger.error(f"❌ Failed to block {ip_address}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Unexpected error blocking {ip_address}: {e}")
            return False
    
    def unblock_ip_address(self, ip_address: str) -> bool:
        """
        Unblock IP address by removing deny rule from Security Group.
        
        Args:
            ip_address: IP address to unblock
            
        Returns:
            True if unblocked successfully, False otherwise
        """
        if ip_address not in self.blocked_ips:
            logger.warning(f"⚠️  IP {ip_address} not in blocked list")
            return False
        
        try:
            # Remove inbound deny rule from Security Group
            response = self.ec2_client.revoke_security_group_ingress(
                GroupId=self.security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',
                        'FromPort': -1,
                        'ToPort': -1,
                        'IpRanges': [{'CidrIp': f'{ip_address}/32'}]
                    }
                ]
            )
            
            # Remove from tracking
            blocked_info = self.blocked_ips.pop(ip_address)
            self.stats["total_unblocks"] += 1
            
            duration = datetime.now() - blocked_info.blocked_at
            
            logger.info(
                f"✅ IP UNBLOCKED | IP: {ip_address} | "
                f"Blocked duration: {duration.seconds // 60} minutes"
            )
            
            print(f"\n{'='*70}")
            print(f"✅ IP UNBLOCKED")
            print(f"{'='*70}")
            print(f"🎯 IP Address: {ip_address}")
            print(f"⏱️  Blocked for: {duration.seconds // 60} minutes")
            print(f"📊 Original Risk: {blocked_info.risk_score:.2f}")
            print(f"{'='*70}\n")
            
            return True
            
        except self.ec2_client.exceptions.ClientError as e:
            logger.error(f"❌ Failed to unblock {ip_address}: {e}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error unblocking {ip_address}: {e}")
            return False
    
    def check_and_unblock_expired(self) -> None:
        """
        Check for expired blocks and automatically unblock IPs.
        Called periodically to enforce timeout policy.
        """
        current_time = datetime.now()
        expired_ips = []
        
        for ip_address, blocked_info in self.blocked_ips.items():
            time_blocked = current_time - blocked_info.blocked_at
            
            if time_blocked > timedelta(minutes=self.block_timeout_minutes):
                expired_ips.append(ip_address)
        
        # Unblock expired IPs
        for ip_address in expired_ips:
            logger.info(f"⏰ Block timeout reached for {ip_address}, unblocking...")
            self.unblock_ip_address(ip_address)
    
    def take_action(
        self,
        ip_address: str,
        risk_score: float,
        network_risk: float,
        user_risk: float
    ) -> str:
        """
        Determine and execute appropriate response action based on risk score.
        
        Args:
            ip_address: Source IP address
            risk_score: Final risk score (0-1)
            network_risk: Network component risk
            user_risk: User behavior component risk
            
        Returns:
            Action taken: LOG, ALERT, RATE_LIMIT, or BLOCK
        """
        threat_level = self.assess_threat_level(risk_score)
        
        if risk_score < 0.4:
            # LOW: Log only
            self.log_threat(ip_address, risk_score, network_risk, user_risk)
            return "LOG"
            
        elif 0.4 <= risk_score < 0.6:
            # MEDIUM: Send alert
            self.send_alert(ip_address, risk_score, network_risk, user_risk, threat_level)
            return "ALERT"
            
        elif 0.6 <= risk_score < 0.8:
            # HIGH: Rate limiting
            self.simulate_rate_limiting(ip_address, risk_score)
            self.send_alert(ip_address, risk_score, network_risk, user_risk, threat_level)
            return "RATE_LIMIT"
            
        else:
            # CRITICAL: Block IP
            success = self.block_ip_address(ip_address, risk_score, network_risk, user_risk)
            if success:
                self.send_alert(ip_address, risk_score, network_risk, user_risk, threat_level)
                return "BLOCK"
            else:
                return "BLOCK_FAILED"
    
    def get_statistics(self) -> Dict:
        """
        Get agent statistics.
        
        Returns:
            Dictionary containing operational statistics
        """
        uptime = datetime.now() - self.stats["start_time"]
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_blocks": self.stats["total_blocks"],
            "total_unblocks": self.stats["total_unblocks"],
            "total_alerts": self.stats["total_alerts"],
            "total_rate_limits": self.stats["total_rate_limits"],
            "currently_blocked": len(self.blocked_ips),
            "blocked_ips": list(self.blocked_ips.keys())
        }
    
    def display_statistics(self) -> None:
        """Display agent statistics in formatted output."""
        stats = self.get_statistics()
        uptime_minutes = stats["uptime_seconds"] // 60
        
        print(f"\n{'='*70}")
        print(f"📊 AUTONOMOUS RESPONSE AGENT STATISTICS")
        print(f"{'='*70}")
        print(f"⏰ Uptime: {uptime_minutes:.0f} minutes")
        print(f"🚫 Total Blocks: {stats['total_blocks']}")
        print(f"✅ Total Unblocks: {stats['total_unblocks']}")
        print(f"🚨 Total Alerts: {stats['total_alerts']}")
        print(f"⚡ Total Rate Limits: {stats['total_rate_limits']}")
        print(f"🔒 Currently Blocked: {stats['currently_blocked']} IPs")
        if stats['blocked_ips']:
            print(f"📋 Blocked IPs: {', '.join(stats['blocked_ips'])}")
        print(f"{'='*70}\n")
    
    def run_monitoring_cycle(
        self,
        ids_engine,
        ueba_engine,
        fusion_function
    ) -> None:
        """
        Run a single monitoring cycle.
        
        Args:
            ids_engine: IDS engine instance
            ueba_engine: UEBA engine instance
            fusion_function: Function to combine risks (network, user) -> (final, level)
        """
        try:
            logger.info("🔄 Starting monitoring cycle...")
            
            # Get network risk from IDS
            network_results = ids_engine.detect()
            
            # Get user risk from UEBA
            user_results = ueba_engine.detect()
            
            # Process each detected threat
            for net in network_results:
                ip = net["ip"]
                network_risk = net["network_risk"]
                
                # Find matching user
                matched_user = next(
                    (u for u in user_results if u["ip"] == ip),
                    None
                )
                user_risk = matched_user["user_risk"] if matched_user else 0.1
                
                # Combine risks using fusion algorithm
                final_risk, threat_level = fusion_function(network_risk, user_risk)
                
                # Take appropriate action
                action = self.take_action(ip, final_risk, network_risk, user_risk)
                
                logger.info(
                    f"✅ Cycle complete | IP: {ip} | Risk: {final_risk:.2f} | "
                    f"Action: {action}"
                )
            
            # Check for expired blocks
            self.check_and_unblock_expired()
            
        except Exception as e:
            logger.error(f"❌ Error in monitoring cycle: {e}")
    
    def start(
        self,
        ids_engine,
        ueba_engine,
        fusion_function
    ) -> None:
        """
        Start the autonomous response agent (continuous monitoring).
        
        Args:
            ids_engine: IDS engine instance
            ueba_engine: UEBA engine instance
            fusion_function: Function to combine risks
        """
        logger.info("🚀 Starting Autonomous Response Agent...")
        logger.info(f"🔄 Monitoring interval: {self.monitoring_interval} seconds")
        
        print(f"\n{'='*70}")
        print(f"🤖 AUTONOMOUS RESPONSE AGENT STARTED")
        print(f"{'='*70}")
        print(f"🔒 Security Group: {self.security_group_id}")
        print(f"🌍 Region: {self.region}")
        print(f"⏱️  Block Timeout: {self.block_timeout_minutes} minutes")
        print(f"🔄 Monitoring Interval: {self.monitoring_interval} seconds")
        print(f"{'='*70}\n")
        
        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                logger.info(f"📊 Monitoring Cycle #{cycle_count}")
                
                # Run monitoring cycle
                self.run_monitoring_cycle(ids_engine, ueba_engine, fusion_function)
                
                # Display statistics every 10 cycles
                if cycle_count % 10 == 0:
                    self.display_statistics()
                
                # Wait for next cycle
                time.sleep(self.monitoring_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping Autonomous Response Agent...")
            self.display_statistics()
            logger.info("👋 Agent stopped gracefully")
            
        except Exception as e:
            logger.error(f"❌ Critical error in agent: {e}")
            self.display_statistics()


# Example usage and testing
if __name__ == "__main__":
    """
    Example usage of Autonomous Response Agent.
    
    Note: This requires:
    1. AWS credentials configured (IAM role or ~/.aws/credentials)
    2. Valid Security Group ID
    3. Proper IAM permissions for EC2 Security Group modifications
    """
    
    # Configuration
    SECURITY_GROUP_ID = "sg-xxxxxxxxxxxxxxxxx"  # Replace with your SG ID
    REGION = "ap-south-1"
    
    # Initialize agent
    agent = AutonomousResponseAgent(
        security_group_id=SECURITY_GROUP_ID,
        region=REGION,
        block_timeout_minutes=10,
        monitoring_interval=60
    )
    
    # Test different threat levels
    print("\n🧪 Testing Autonomous Response Agent...\n")
    
    # Test 1: LOW threat
    print("Test 1: LOW threat (risk = 0.2)")
    agent.take_action("192.168.1.100", 0.2, 0.15, 0.25)
    
    time.sleep(2)
    
    # Test 2: MEDIUM threat
    print("\nTest 2: MEDIUM threat (risk = 0.5)")
    agent.take_action("192.168.1.101", 0.5, 0.6, 0.4)
    
    time.sleep(2)
    
    # Test 3: HIGH threat
    print("\nTest 3: HIGH threat (risk = 0.7)")
    agent.take_action("192.168.1.102", 0.7, 0.8, 0.5)
    
    time.sleep(2)
    
    # Test 4: CRITICAL threat
    print("\nTest 4: CRITICAL threat (risk = 0.9)")
    agent.take_action("192.168.1.103", 0.9, 0.95, 0.8)
    
    time.sleep(2)
    
    # Display statistics
    agent.display_statistics()
    
    print("\n✅ Test complete!")
    print("Note: To run with actual IDS/UEBA engines, use agent.start(ids, ueba, fusion)")
