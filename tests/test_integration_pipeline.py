"""
Unit tests for the N8N / LangChain RAG / LangFuse integration modules.

These tests run entirely offline (no N8N, no ChromaDB, no LangFuse cloud)
by mocking external calls.  They validate:

    1. N8NClient – payload structure, disabled mode, error resilience
    2. ThreatIntelRAG – disabled gracefully when LangChain not installed
    3. LangFuseObserver – disabled gracefully when LangFuse not installed
    4. IntegrationPipeline – end-to-end wiring with all integrations mocked
"""

import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

# Ensure src/ is importable when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────────────────────────────────────
# N8N CLIENT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestN8NClient(unittest.TestCase):

    def _make_client(self, url="http://n8n.example.com/webhook/test"):
        from src.n8n_integration import N8NClient
        return N8NClient(webhook_url=url)

    def test_disabled_when_no_url(self):
        from src.n8n_integration import N8NClient
        client = N8NClient(webhook_url="")
        self.assertFalse(client.enabled)

    def test_disabled_flag(self):
        from src.n8n_integration import N8NClient
        client = N8NClient(webhook_url="http://example.com/wh", enabled=False)
        self.assertFalse(client.enabled)

    def test_send_returns_false_when_disabled(self):
        from src.n8n_integration import N8NClient
        client = N8NClient(webhook_url="", enabled=False)
        result = client.send_threat_alert(
            threat_level="HIGH", final_risk=0.7,
            network_risk=0.8, user_risk=0.4,
        )
        self.assertFalse(result)

    @patch("src.n8n_integration.requests.post")
    def test_send_threat_alert_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = self._make_client()
        result = client.send_threat_alert(
            threat_level="CRITICAL",
            final_risk=0.92,
            network_risk=0.95,
            user_risk=0.85,
            ip_address="10.0.0.1",
            network_bytes=5_000_000,
            network_packets=60_000,
            extra_context={"source": "test"},
        )

        self.assertTrue(result)
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]

        self.assertEqual(payload["event_type"], "threat_alert")
        self.assertEqual(payload["threat_level"], "CRITICAL")
        self.assertAlmostEqual(payload["final_risk"], 0.92, places=3)
        self.assertIn("timestamp", payload)
        self.assertEqual(payload["context"]["source"], "test")

    @patch("src.n8n_integration.requests.post")
    def test_send_threat_alert_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        client = self._make_client()
        result = client.send_threat_alert(
            threat_level="HIGH", final_risk=0.7,
            network_risk=0.8, user_risk=0.4,
        )
        self.assertFalse(result)

    @patch("src.n8n_integration.requests.post",
           side_effect=Exception("connection refused"))
    def test_send_does_not_raise_on_error(self, _mock_post):
        client = self._make_client()
        # Must not raise
        result = client.send_threat_alert(
            threat_level="HIGH", final_risk=0.7,
            network_risk=0.8, user_risk=0.4,
        )
        self.assertFalse(result)

    @patch("src.n8n_integration.requests.post")
    def test_send_response_action_block(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = self._make_client()
        result = client.send_response_action(
            action="BLOCK",
            ip_address="203.0.113.42",
            risk_score=0.91,
            reasoning="DDoS detected",
            duration_minutes=60,
        )

        self.assertTrue(result)
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["event_type"], "block_ip")
        self.assertEqual(payload["action"], "BLOCK")

    @patch("src.n8n_integration.requests.post")
    def test_send_response_action_rate_limit(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = self._make_client()
        client.send_response_action(
            action="RATE_LIMIT",
            ip_address="203.0.113.42",
            risk_score=0.70,
        )
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["event_type"], "rate_limit")

    @patch("src.n8n_integration.requests.post")
    def test_send_system_event(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = self._make_client()
        client.send_system_event("system_start", metadata={"version": "1.0"})
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["event_type"], "system_start")
        self.assertEqual(payload["metadata"]["version"], "1.0")


# ─────────────────────────────────────────────────────────────────────────────
# RAG THREAT INTEL TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestThreatIntelRAG(unittest.TestCase):

    def test_disabled_gracefully_when_langchain_missing(self):
        """When LangChain is not installed, RAG must degrade to no-op."""
        from src.rag_threat_intel import ThreatIntelRAG
        # Force _LANGCHAIN_AVAILABLE = False for this test
        import src.rag_threat_intel as rag_module
        original = rag_module._LANGCHAIN_AVAILABLE
        rag_module._LANGCHAIN_AVAILABLE = False
        try:
            rag = ThreatIntelRAG()
            self.assertFalse(rag.enabled)
            result = rag.enrich(threat_level="HIGH", network_risk=0.8, user_risk=0.4)
            self.assertEqual(result, "")
        finally:
            rag_module._LANGCHAIN_AVAILABLE = original

    def test_build_query_high_network(self):
        """Query builder should mention DDoS for high network risk."""
        from src.rag_threat_intel import ThreatIntelRAG
        query = ThreatIntelRAG._build_query("HIGH", 0.85, 0.20, "1.2.3.4")
        self.assertIn("DDoS", query)

    def test_build_query_high_user(self):
        """Query builder should mention insider threat for high user risk."""
        from src.rag_threat_intel import ThreatIntelRAG
        query = ThreatIntelRAG._build_query("HIGH", 0.20, 0.85, "1.2.3.4")
        self.assertIn("insider", query.lower())

    def test_build_query_low_risks(self):
        """Query should still return a non-empty string for low risks."""
        from src.rag_threat_intel import ThreatIntelRAG
        query = ThreatIntelRAG._build_query("LOW", 0.1, 0.1, "")
        self.assertIn("LOW", query)

    def test_enrich_returns_empty_when_disabled(self):
        from src.rag_threat_intel import ThreatIntelRAG
        import src.rag_threat_intel as rag_module
        original = rag_module._LANGCHAIN_AVAILABLE
        rag_module._LANGCHAIN_AVAILABLE = False
        try:
            rag = ThreatIntelRAG()
            self.assertEqual(rag.enrich(), "")
        finally:
            rag_module._LANGCHAIN_AVAILABLE = original

    def test_enrich_with_mock_vectorstore(self):
        """When vectorstore is available, enrich should return context."""
        from src.rag_threat_intel import ThreatIntelRAG
        rag = ThreatIntelRAG.__new__(ThreatIntelRAG)
        rag.persist_dir = "/tmp/test_chroma"
        rag.top_k = 2
        rag.enabled = True

        mock_doc = MagicMock()
        mock_doc.page_content = "DDoS mitigation: block the source IP at the perimeter."
        mock_vs = MagicMock()
        mock_vs.similarity_search.return_value = [mock_doc]
        rag._vectorstore = mock_vs

        result = rag.enrich(
            threat_level="HIGH", network_risk=0.85,
            user_risk=0.3, ip_address="1.2.3.4",
        )
        self.assertIn("DDoS mitigation", result)
        self.assertIn("Threat Intelligence Context", result)


# ─────────────────────────────────────────────────────────────────────────────
# LANGFUSE OBSERVER TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestLangFuseObserver(unittest.TestCase):

    def test_disabled_when_no_keys(self):
        from src.langfuse_observer import LangFuseObserver
        obs = LangFuseObserver(public_key="", secret_key="")
        self.assertFalse(obs.enabled)

    def test_start_llm_trace_returns_uuids_when_disabled(self):
        from src.langfuse_observer import LangFuseObserver
        obs = LangFuseObserver(public_key="", secret_key="")
        trace_id, gen_id = obs.start_llm_trace(
            name="test", prompt="hello", model="phi3"
        )
        self.assertTrue(len(trace_id) > 0)
        self.assertTrue(len(gen_id) > 0)

    def test_end_llm_trace_no_op_when_disabled(self):
        from src.langfuse_observer import LangFuseObserver
        obs = LangFuseObserver(public_key="", secret_key="")
        # Should not raise
        obs.end_llm_trace("fake-id", "fake-gen", "response text", latency_ms=100)

    def test_score_decision_no_op_when_disabled(self):
        from src.langfuse_observer import LangFuseObserver
        obs = LangFuseObserver(public_key="", secret_key="")
        obs.score_decision("fake-id", "true_positive", 1.0)

    def test_observe_llm_call_context_manager(self):
        """Context manager must call start/end even when disabled."""
        from src.langfuse_observer import LangFuseObserver
        obs = LangFuseObserver(public_key="", secret_key="")
        with obs.observe_llm_call("test", "prompt") as ctx:
            ctx.set_output("Action: LOG")
        # No exception means success
        self.assertTrue(True)

    def test_flush_no_op_when_disabled(self):
        from src.langfuse_observer import LangFuseObserver
        obs = LangFuseObserver(public_key="", secret_key="")
        obs.flush()  # Must not raise

    def test_start_detection_cycle_returns_uuid(self):
        from src.langfuse_observer import LangFuseObserver
        obs = LangFuseObserver(public_key="", secret_key="")
        trace_id = obs.start_detection_cycle(cycle_number=1)
        self.assertTrue(len(trace_id) > 0)

    def test_end_detection_cycle_no_op_when_disabled(self):
        from src.langfuse_observer import LangFuseObserver
        obs = LangFuseObserver(public_key="", secret_key="")
        obs.end_detection_cycle("fake-trace-id", threats_detected=2)


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION PIPELINE TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegrationPipeline(unittest.TestCase):

    def _make_pipeline(self):
        """Return a pipeline with all external calls mocked."""
        from src.integration_pipeline import IntegrationPipeline
        pipeline = IntegrationPipeline.__new__(IntegrationPipeline)

        # Mock sub-components
        pipeline.enabled = True
        pipeline._cycle_counter = 0
        pipeline._ollama_agent = None
        pipeline._ollama_model = "qwen2.5:0.5b"

        # N8N – always succeeds
        pipeline.n8n = MagicMock()
        pipeline.n8n.enabled = True
        pipeline.n8n.send_threat_alert.return_value = True
        pipeline.n8n.send_response_action.return_value = True
        pipeline.n8n.send_system_event.return_value = True

        # RAG – returns a context string
        pipeline.rag = MagicMock()
        pipeline.rag.enabled = True
        pipeline.rag.enrich.return_value = "Block source IP for DDoS."

        # LangFuse – disabled (no keys)
        from src.langfuse_observer import LangFuseObserver
        pipeline.langfuse = LangFuseObserver(public_key="", secret_key="")

        return pipeline

    def test_start_cycle_returns_trace_id(self):
        pipeline = self._make_pipeline()
        trace_id = pipeline.start_cycle()
        self.assertIsInstance(trace_id, str)
        self.assertTrue(len(trace_id) > 0)

    def test_process_threat_returns_expected_keys(self):
        pipeline = self._make_pipeline()
        result = pipeline.process_threat(
            threat_level="HIGH",
            final_risk=0.72,
            network_risk=0.80,
            user_risk=0.40,
        )
        for key in ("action", "confidence", "reasoning", "rag_context",
                    "trace_id", "n8n_sent", "elapsed_ms"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_process_threat_uses_rag(self):
        pipeline = self._make_pipeline()
        result = pipeline.process_threat(
            threat_level="HIGH", final_risk=0.72,
            network_risk=0.80, user_risk=0.40,
        )
        self.assertEqual(result["rag_context"], "Block source IP for DDoS.")
        pipeline.rag.enrich.assert_called_once()

    def test_process_threat_sends_n8n_alert(self):
        pipeline = self._make_pipeline()
        pipeline.process_threat(
            threat_level="CRITICAL", final_risk=0.92,
            network_risk=0.95, user_risk=0.85,
        )
        pipeline.n8n.send_threat_alert.assert_called_once()

    def test_process_threat_fallback_when_no_ollama(self):
        """When Ollama is unavailable, rule-based fallback must be used."""
        pipeline = self._make_pipeline()
        pipeline._ollama_agent = None  # ensure no Ollama

        # Patch _get_ollama_agent to always return None
        pipeline._get_ollama_agent = lambda: None

        result = pipeline.process_threat(
            threat_level="CRITICAL", final_risk=0.91,
            network_risk=0.95, user_risk=0.85,
        )
        self.assertEqual(result["action"], "BLOCK")
        self.assertIn("Critical", result["reasoning"])

    def test_rule_based_fallback_levels(self):
        from src.integration_pipeline import _rule_based_decision
        self.assertEqual(_rule_based_decision(0.9)["action"], "BLOCK")
        self.assertEqual(_rule_based_decision(0.7)["action"], "RATE_LIMIT")
        self.assertEqual(_rule_based_decision(0.5)["action"], "ALERT")
        self.assertEqual(_rule_based_decision(0.2)["action"], "LOG")

    def test_end_cycle_sends_system_event(self):
        pipeline = self._make_pipeline()
        trace_id = pipeline.start_cycle()
        pipeline.end_cycle(trace_id, threats_detected=3)
        pipeline.n8n.send_system_event.assert_called_once()
        call_args = pipeline.n8n.send_system_event.call_args
        self.assertEqual(call_args[0][0], "detection_cycle")
        self.assertEqual(call_args[1]["metadata"]["threats_detected"], 3)

    def test_record_outcome_delegates_to_langfuse(self):
        pipeline = self._make_pipeline()
        pipeline.langfuse = MagicMock()
        pipeline.record_outcome("trace-1", "true_positive", 1.0, "Confirmed")
        pipeline.langfuse.score_decision.assert_called_once_with(
            "trace-1", "true_positive", 1.0, "Confirmed"
        )

    def test_shutdown_calls_flush(self):
        pipeline = self._make_pipeline()
        pipeline.langfuse = MagicMock()
        pipeline.shutdown()
        pipeline.langfuse.flush.assert_called_once()

    def test_rag_augmented_prompt_contains_context(self):
        from src.integration_pipeline import _build_rag_augmented_prompt
        prompt = _build_rag_augmented_prompt(
            "HIGH", 0.72, 0.80, 0.40, "1.2.3.4",
            "DDoS mitigation: block source."
        )
        self.assertIn("DDoS mitigation", prompt)
        self.assertIn("HIGH", prompt)
        self.assertIn("0.72", prompt)

    def test_rag_augmented_prompt_without_context(self):
        from src.integration_pipeline import _build_rag_augmented_prompt
        prompt = _build_rag_augmented_prompt(
            "LOW", 0.2, 0.1, 0.3, "1.2.3.4", ""
        )
        self.assertNotIn("RAG", prompt)
        self.assertIn("LOG", prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
