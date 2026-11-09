"""Tests for the VRAM estimator.

The estimator used to divide by an extra 1000, so every model appeared to need
roughly 0.7 GB: FP16 and Q2_K came out within 0.02 GB of each other and every
model "fitted" every machine. These tests pin the arithmetic to numbers that
can be checked by hand, so that class of error cannot come back.
"""

import pytest

from localmind.vram import (
    QUANT_MULTIPLIERS,
    _extract_params,
    estimate_vram,
    get_best_quant,
)


def by_quant(model_name):
    """Estimates for one model, keyed by quantization."""
    return {e.quantization: e for e in estimate_vram(model_name)}


def test_weights_scale_with_parameters_and_bytes_per_parameter():
    """llama3:8b at Q4_0 is 8 x 0.55 = 4.4 GB of weights, plus KV overhead."""
    est = by_quant("llama3:8b")["Q4_0"]
    expected = 8 * QUANT_MULTIPLIERS["Q4_0"] + 0.8
    assert est.size_gb == pytest.approx(expected, abs=0.05)


def test_precision_actually_changes_the_estimate():
    """The regression guard: FP16 must be far larger than Q4_0, not equal."""
    est = by_quant("llama3:8b")
    assert est["FP16"].size_gb - est["Q4_0"].size_gb > 10
    assert est["FP16"].size_gb > 2.5 * est["Q4_0"].size_gb


def test_known_models_match_their_published_sizes():
    assert by_quant("mistral:7b")["FP16"].size_gb == pytest.approx(14.7, abs=0.1)
    assert by_quant("llama3:70b")["FP16"].size_gb == pytest.approx(140.8, abs=0.2)


def test_quantizations_are_sorted_smallest_first():
    estimates = estimate_vram("mistral:7b")
    sizes = [e.size_gb for e in estimates]
    assert sizes == sorted(sizes)
    assert estimates[0].quantization == "Q2_K"
    assert estimates[-1].quantization == "FP16"


def test_moe_parameter_totals_come_from_the_table_not_the_tag():
    """8x7B is 46.7B total parameters, not 8 x 7 = 56B."""
    assert _extract_params("mixtral:8x7b") == 46.7
    assert _extract_params("mistral:8x22b") == 141.0


def test_explicit_size_tag_is_read():
    assert _extract_params("llama3:8b") == 8.0
    assert _extract_params("qwen:0.5b") == 0.5


def test_unknown_model_produces_no_estimate():
    """Better to say nothing than to invent a plausible 0.7 GB."""
    assert estimate_vram("not-a-real-model") == []
    assert get_best_quant("not-a-real-model", 8.0, 32.0) is None


def test_fit_flags_follow_available_memory():
    est = by_quant("llama3:8b")
    fits = {
        e.quantization: e
        for e in estimate_vram(
            "llama3:8b", available_vram_gb=8.0, available_ram_gb=32.0
        )
    }
    assert fits["Q4_K_M"].fits_in_vram is True
    assert fits["FP16"].fits_in_vram is False
    # No GPU information at all means "unknown", not "fits"
    assert est["Q4_K_M"].fits_in_vram is False


def test_best_quant_returns_something_that_actually_fits():
    best = get_best_quant("llama3:8b", available_vram_gb=8.0, available_ram_gb=32.0)
    assert best is not None
    assert best.vram_gb <= 8.0 * 0.9
    assert best.quantization in QUANT_MULTIPLIERS


def test_nothing_fits_returns_none():
    assert get_best_quant("llama3:70b", available_vram_gb=1.0, available_ram_gb=2.0) is None
