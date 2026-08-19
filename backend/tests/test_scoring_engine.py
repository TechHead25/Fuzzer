"""
Tests for the Target Discovery scoring engine.
Tests use only synthetic, clearly fake data – no real SumatraPDF functions.
"""

import pytest
from app.analysis.types import DiscoveredTarget, EvidenceKind
from app.analysis.scorer import TargetScorer, INDICATOR_WEIGHTS


@pytest.fixture
def scorer():
    return TargetScorer()


def _make_target(**indicators) -> DiscoveredTarget:
    return DiscoveredTarget(
        function_name="test_func",
        module="test_module",
        raw_indicators=indicators,
    )


class TestScorerIndicators:
    def test_empty_indicators_gives_zero_score(self, scorer):
        t = scorer.score(_make_target())
        assert t.risk_score == 0.0
        assert t.confidence == 0.0
        assert t.reasons == []

    def test_single_observed_indicator(self, scorer):
        t = scorer.score(_make_target(memcpy_call="memcpy(dst, src, len)"))
        assert t.risk_score == pytest.approx(INDICATOR_WEIGHTS["memcpy_call"]["weight"])
        assert len(t.reasons) == 1
        assert t.reasons[0].indicator == "memcpy_call"
        assert t.reasons[0].evidence_kind == EvidenceKind.OBSERVED

    def test_attacker_controlled_param_is_inferred(self, scorer):
        # attacker_controlled_param is NOT in _OBSERVABLE_INDICATORS
        t = scorer.score(_make_target(attacker_controlled_param="param 'buf'"))
        assert len(t.reasons) == 1
        assert t.reasons[0].evidence_kind == EvidenceKind.INFERRED

    def test_score_capped_at_10(self, scorer):
        # Activate every indicator simultaneously
        all_indicators = {k: f"found at line {i}" for i, k in enumerate(INDICATOR_WEIGHTS)}
        t = scorer.score(_make_target(**all_indicators))
        assert t.risk_score <= 10.0
        assert t.risk_score > 0.0

    def test_high_risk_function(self, scorer):
        # A function with attacker buffer, memcpy, length arithmetic, and decompression
        t = scorer.score(_make_target(
            attacker_controlled_param="buf parameter",
            memcpy_call="memcpy(dst, buf, len)",
            length_arithmetic="len + offset",
            decompression_call="inflate(stream)",
        ))
        expected = (
            INDICATOR_WEIGHTS["attacker_controlled_param"]["weight"]
            + INDICATOR_WEIGHTS["memcpy_call"]["weight"]
            + INDICATOR_WEIGHTS["length_arithmetic"]["weight"]
            + INDICATOR_WEIGHTS["decompression_call"]["weight"]
        )
        assert t.risk_score == pytest.approx(min(expected, 10.0))
        assert len(t.reasons) == 4

    def test_confidence_all_observed(self, scorer):
        # memcpy_call and buffer_write are both OBSERVED
        t = scorer.score(_make_target(
            memcpy_call="memcpy(dst, src, n)",
            buffer_write="buf[i] = x",
        ))
        # Both observed → confidence should be 1.0
        assert t.confidence == pytest.approx(1.0)

    def test_confidence_mixed(self, scorer):
        # parser_routine is INFERRED, memcpy_call is OBSERVED
        t = scorer.score(_make_target(
            parser_routine="function name 'ParsePdf'",
            memcpy_call="memcpy(...)",
        ))
        # 1 observed out of 2 total → 0.5
        assert t.confidence == pytest.approx(0.5)

    def test_harness_type_file_reader_default(self, scorer):
        from app.analysis.types import HarnessType
        t = scorer.score(_make_target(buffer_write="buf[i] = x"))
        assert t.suggested_harness_type == HarnessType.FILE_READER

    def test_harness_type_network_hint(self, scorer):
        from app.analysis.types import HarnessType
        t = scorer.score(_make_target(network_recv="recv(sock, buf, len, 0)"))
        assert t.suggested_harness_type == HarnessType.NETWORK_STUB

    def test_reasons_have_descriptions(self, scorer):
        t = scorer.score(_make_target(
            memcpy_call="memcpy(d,s,n)",
            length_arithmetic="len + 4",
        ))
        for reason in t.reasons:
            assert reason.description
            assert reason.indicator in INDICATOR_WEIGHTS

    def test_unknown_indicator_ignored(self, scorer):
        t = scorer.score(_make_target(fake_indicator_xyz="value"))
        assert t.risk_score == 0.0
        assert t.reasons == []

    def test_false_value_indicator_skipped(self, scorer):
        t = scorer.score(_make_target(memcpy_call=False, buffer_write=None, buffer_read=""))
        # All falsy values → no reasons
        assert t.risk_score == 0.0

    def test_source_ref_stored(self, scorer):
        t = scorer.score(_make_target(memcpy_call="memcpy(dst, src, len)"))
        assert t.reasons[0].source_ref is not None
        assert "memcpy" in t.reasons[0].source_ref


class TestIndicatorCatalogue:
    def test_all_indicators_have_weight(self):
        for name, spec in INDICATOR_WEIGHTS.items():
            assert "weight" in spec, f"{name} missing weight"
            assert 0.0 < spec["weight"] <= 3.0, f"{name} weight out of range"

    def test_all_indicators_have_description(self):
        for name, spec in INDICATOR_WEIGHTS.items():
            assert "description" in spec and spec["description"]

    def test_all_indicators_have_harness_hint(self):
        from app.analysis.types import HarnessType
        for name, spec in INDICATOR_WEIGHTS.items():
            assert "harness_hint" in spec
            assert isinstance(spec["harness_hint"], HarnessType)
