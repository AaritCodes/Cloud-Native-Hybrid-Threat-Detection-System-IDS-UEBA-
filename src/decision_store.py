"""
Persistent Decision Store using SQLite

Stores all agent decisions, outcomes, and threat history.
Enables learning from past decisions and long-term pattern analysis.

Author: Aarit Haldar
Date: March 2026
"""

import sqlite3
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "decisions.db")


class DecisionStore:
    """
    SQLite-backed persistent store for agent decisions.
    
    Features:
    - Stores every decision with full context
    - Records outcomes (true_positive, false_positive, missed_attack)
    - Queries for similar past threats
    - Computes accuracy statistics for adaptive thresholds
    - IP reputation history
    """

    def __init__(self, db_path: str = DB_PATH):
        """
        Initialize the decision store.
        
        Args:
            db_path: Path to SQLite database file
        """
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()
        logger.info(f"DecisionStore initialized at {db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        """Get a new connection (SQLite connections are not thread-safe)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    network_risk REAL NOT NULL,
                    user_risk REAL NOT NULL,
                    final_risk REAL NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL,
                    reasoning TEXT,
                    risk_assessment TEXT,
                    ai_model TEXT,
                    context_json TEXT,
                    outcome TEXT DEFAULT NULL,
                    outcome_notes TEXT DEFAULT NULL,
                    outcome_timestamp TEXT DEFAULT NULL
                );

                CREATE TABLE IF NOT EXISTS ip_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    total_events INTEGER DEFAULT 1,
                    total_blocks INTEGER DEFAULT 0,
                    total_alerts INTEGER DEFAULT 0,
                    avg_risk REAL DEFAULT 0.0,
                    max_risk REAL DEFAULT 0.0,
                    reputation_score REAL DEFAULT 0.5,
                    tags TEXT DEFAULT '[]',
                    UNIQUE(ip_address)
                );

                CREATE TABLE IF NOT EXISTS threat_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    description TEXT,
                    indicators_json TEXT,
                    first_detected TEXT,
                    last_detected TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    severity TEXT DEFAULT 'MEDIUM'
                );

                CREATE INDEX IF NOT EXISTS idx_decisions_ip ON decisions(ip_address);
                CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp);
                CREATE INDEX IF NOT EXISTS idx_decisions_action ON decisions(action);
                CREATE INDEX IF NOT EXISTS idx_decisions_outcome ON decisions(outcome);
                CREATE INDEX IF NOT EXISTS idx_ip_history_ip ON ip_history(ip_address);
            """)
            conn.commit()
        finally:
            conn.close()

    # ── Decision CRUD ──────────────────────────────────────────────

    def store_decision(
        self,
        ip_address: str,
        network_risk: float,
        user_risk: float,
        final_risk: float,
        action: str,
        confidence: float = 0.0,
        reasoning: str = "",
        risk_assessment: str = "",
        ai_model: str = "rule-based",
        context: Optional[Dict] = None,
    ) -> int:
        """
        Store a new decision.

        Returns:
            The row id of the inserted decision.
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """INSERT INTO decisions
                   (timestamp, ip_address, network_risk, user_risk, final_risk,
                    action, confidence, reasoning, risk_assessment, ai_model, context_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(),
                    ip_address,
                    network_risk,
                    user_risk,
                    final_risk,
                    action,
                    confidence,
                    reasoning,
                    risk_assessment,
                    ai_model,
                    json.dumps(context or {}),
                ),
            )
            decision_id = cursor.lastrowid
            conn.commit()

            # Update IP history
            self._update_ip_history(conn, ip_address, final_risk, action)
            conn.commit()

            logger.info(f"Decision #{decision_id} stored: {action} for {ip_address}")
            return decision_id
        finally:
            conn.close()

    def record_outcome(
        self,
        decision_id: int,
        outcome: str,
        notes: str = "",
    ) -> bool:
        """
        Record the outcome of a past decision.

        Args:
            decision_id: ID from store_decision
            outcome: 'true_positive' | 'false_positive' | 'missed_attack' | 'benign'
            notes: Optional explanation

        Returns:
            True if updated successfully
        """
        valid_outcomes = {"true_positive", "false_positive", "missed_attack", "benign"}
        if outcome not in valid_outcomes:
            logger.warning(f"Invalid outcome '{outcome}'. Must be one of {valid_outcomes}")
            return False

        conn = self._get_conn()
        try:
            conn.execute(
                """UPDATE decisions
                   SET outcome = ?, outcome_notes = ?, outcome_timestamp = ?
                   WHERE id = ?""",
                (outcome, notes, datetime.now().isoformat(), decision_id),
            )
            conn.commit()

            # Update IP reputation based on outcome
            row = conn.execute(
                "SELECT ip_address FROM decisions WHERE id = ?", (decision_id,)
            ).fetchone()
            if row:
                self._adjust_ip_reputation(conn, row["ip_address"], outcome)
                conn.commit()

            logger.info(f"Outcome '{outcome}' recorded for decision #{decision_id}")
            return True
        finally:
            conn.close()

    # ── Query helpers ──────────────────────────────────────────────

    def get_similar_decisions(
        self,
        network_risk: float,
        user_risk: float,
        tolerance: float = 0.15,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Find past decisions with similar risk scores.

        Args:
            network_risk: Current network risk score
            user_risk: Current user risk score
            tolerance: How close scores must be (default ±0.15)
            limit: Max results

        Returns:
            List of similar past decisions (most recent first)
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT * FROM decisions
                   WHERE ABS(network_risk - ?) < ? AND ABS(user_risk - ?) < ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (network_risk, tolerance, user_risk, tolerance, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_ip_decisions(self, ip_address: str, limit: int = 20) -> List[Dict]:
        """Get all past decisions for a specific IP."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT * FROM decisions
                   WHERE ip_address = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (ip_address, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_ip_reputation(self, ip_address: str) -> Dict:
        """
        Get the reputation profile for an IP address.

        Returns:
            Dict with reputation data, or empty dict if IP not seen before.
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM ip_history WHERE ip_address = ?", (ip_address,)
            ).fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    def get_recent_decisions(self, hours: int = 1, limit: int = 50) -> List[Dict]:
        """Get decisions from the last N hours."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT * FROM decisions
                   WHERE timestamp > ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (cutoff, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_accuracy_stats(self) -> Dict:
        """
        Compute accuracy statistics from recorded outcomes.

        Returns:
            Dict with accuracy metrics.
        """
        conn = self._get_conn()
        try:
            total = conn.execute(
                "SELECT COUNT(*) as c FROM decisions WHERE outcome IS NOT NULL"
            ).fetchone()["c"]

            if total == 0:
                return {"total_evaluated": 0, "accuracy": None, "message": "No outcomes recorded yet"}

            tp = conn.execute(
                "SELECT COUNT(*) as c FROM decisions WHERE outcome = 'true_positive'"
            ).fetchone()["c"]
            fp = conn.execute(
                "SELECT COUNT(*) as c FROM decisions WHERE outcome = 'false_positive'"
            ).fetchone()["c"]
            missed = conn.execute(
                "SELECT COUNT(*) as c FROM decisions WHERE outcome = 'missed_attack'"
            ).fetchone()["c"]
            benign = conn.execute(
                "SELECT COUNT(*) as c FROM decisions WHERE outcome = 'benign'"
            ).fetchone()["c"]

            accuracy = (tp + benign) / total if total > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + missed) if (tp + missed) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            return {
                "total_evaluated": total,
                "true_positives": tp,
                "false_positives": fp,
                "missed_attacks": missed,
                "benign": benign,
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
            }
        finally:
            conn.close()

    def get_adaptive_thresholds(self) -> Dict:
        """
        Suggest adjusted thresholds based on past outcomes.

        If there are many false positives, raise thresholds.
        If there are missed attacks, lower thresholds.

        Returns:
            Dict with suggested threshold adjustments
        """
        stats = self.get_accuracy_stats()
        if stats.get("total_evaluated", 0) < 10:
            return {
                "status": "insufficient_data",
                "message": "Need at least 10 evaluated outcomes to suggest thresholds",
                "current_thresholds": {"LOG": 0.0, "ALERT": 0.4, "RATE_LIMIT": 0.6, "BLOCK": 0.8},
            }

        fp_rate = stats["false_positives"] / stats["total_evaluated"]
        miss_rate = stats["missed_attacks"] / stats["total_evaluated"]

        # Start with defaults
        thresholds = {"LOG": 0.0, "ALERT": 0.4, "RATE_LIMIT": 0.6, "BLOCK": 0.8}

        adjustment = 0.0
        reason = "No adjustment needed"

        if fp_rate > 0.2:
            # Too many false positives → raise thresholds (be less aggressive)
            adjustment = min(fp_rate * 0.1, 0.1)
            reason = f"High false positive rate ({fp_rate:.0%}), raising thresholds"
        elif miss_rate > 0.1:
            # Missing attacks → lower thresholds (be more aggressive)
            adjustment = -min(miss_rate * 0.1, 0.1)
            reason = f"Missed attack rate ({miss_rate:.0%}), lowering thresholds"

        thresholds["ALERT"] = round(max(0.2, min(0.5, thresholds["ALERT"] + adjustment)), 2)
        thresholds["RATE_LIMIT"] = round(max(0.4, min(0.7, thresholds["RATE_LIMIT"] + adjustment)), 2)
        thresholds["BLOCK"] = round(max(0.6, min(0.9, thresholds["BLOCK"] + adjustment)), 2)

        return {
            "status": "adjusted",
            "reason": reason,
            "fp_rate": round(fp_rate, 4),
            "miss_rate": round(miss_rate, 4),
            "suggested_thresholds": thresholds,
        }

    # ── Internal helpers ───────────────────────────────────────────

    def _update_ip_history(self, conn: sqlite3.Connection, ip_address: str, risk: float, action: str):
        """Update IP history record (insert or update)."""
        existing = conn.execute(
            "SELECT * FROM ip_history WHERE ip_address = ?", (ip_address,)
        ).fetchone()

        now = datetime.now().isoformat()

        if existing:
            new_total = existing["total_events"] + 1
            new_avg = (existing["avg_risk"] * existing["total_events"] + risk) / new_total
            new_max = max(existing["max_risk"], risk)
            new_blocks = existing["total_blocks"] + (1 if action == "BLOCK" else 0)
            new_alerts = existing["total_alerts"] + (1 if action in ("ALERT", "RATE_LIMIT", "BLOCK") else 0)

            conn.execute(
                """UPDATE ip_history
                   SET last_seen = ?, total_events = ?, total_blocks = ?,
                       total_alerts = ?, avg_risk = ?, max_risk = ?
                   WHERE ip_address = ?""",
                (now, new_total, new_blocks, new_alerts, round(new_avg, 4), round(new_max, 4), ip_address),
            )
        else:
            conn.execute(
                """INSERT INTO ip_history
                   (ip_address, first_seen, last_seen, total_events,
                    total_blocks, total_alerts, avg_risk, max_risk, reputation_score, tags)
                   VALUES (?, ?, ?, 1, ?, ?, ?, ?, 0.5, '[]')""",
                (
                    ip_address, now, now,
                    1 if action == "BLOCK" else 0,
                    1 if action in ("ALERT", "RATE_LIMIT", "BLOCK") else 0,
                    round(risk, 4),
                    round(risk, 4),
                ),
            )

    def _adjust_ip_reputation(self, conn: sqlite3.Connection, ip_address: str, outcome: str):
        """
        Adjust IP reputation score based on outcome.

        reputation_score: 0.0 = definitely malicious, 1.0 = definitely benign
        """
        existing = conn.execute(
            "SELECT reputation_score FROM ip_history WHERE ip_address = ?", (ip_address,)
        ).fetchone()

        if not existing:
            return

        rep = existing["reputation_score"]

        if outcome == "true_positive":
            rep = max(0.0, rep - 0.15)  # Confirmed malicious → lower reputation
        elif outcome == "false_positive":
            rep = min(1.0, rep + 0.10)  # Was actually benign → raise reputation
        elif outcome == "missed_attack":
            rep = max(0.0, rep - 0.20)  # Missed a real attack → much lower
        elif outcome == "benign":
            rep = min(1.0, rep + 0.05)  # Confirmed benign → slight raise

        conn.execute(
            "UPDATE ip_history SET reputation_score = ? WHERE ip_address = ?",
            (round(rep, 4), ip_address),
        )

    def get_total_decisions(self) -> int:
        """Get total number of stored decisions."""
        conn = self._get_conn()
        try:
            return conn.execute("SELECT COUNT(*) as c FROM decisions").fetchone()["c"]
        finally:
            conn.close()

    def get_known_ips(self) -> List[Dict]:
        """Get all known IPs with their history."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM ip_history ORDER BY last_seen DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


# Quick test
if __name__ == "__main__":
    store = DecisionStore()
    print(f"Database at: {store.db_path}")
    print(f"Total decisions: {store.get_total_decisions()}")

    # Store a test decision
    did = store.store_decision(
        ip_address="203.0.113.42",
        network_risk=0.85,
        user_risk=0.30,
        final_risk=0.63,
        action="RATE_LIMIT",
        confidence=0.85,
        reasoning="High network traffic with moderate user anomaly",
        risk_assessment="HIGH",
        ai_model="ollama/qwen2.5:0.5b",
    )
    print(f"Stored decision #{did}")

    # Record outcome
    store.record_outcome(did, "true_positive", "Confirmed DDoS attempt")
    print("Outcome recorded")

    # Check stats
    print(f"Accuracy stats: {store.get_accuracy_stats()}")
    print(f"IP reputation: {store.get_ip_reputation('203.0.113.42')}")
    print(f"Adaptive thresholds: {store.get_adaptive_thresholds()}")
