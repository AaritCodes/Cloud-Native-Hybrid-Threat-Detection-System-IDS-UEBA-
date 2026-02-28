#!/usr/bin/env python3
"""
Hybrid Threat Detection System - Main Runner
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_main import EnhancedThreatDetectionSystem

if __name__ == "__main__":
    print("="*60)
    print("🛡️  Hybrid Threat Detection System")
    print("="*60)
    
    system = EnhancedThreatDetectionSystem()
    system.run()
