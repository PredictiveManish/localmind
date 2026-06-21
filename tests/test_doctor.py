"""Tests for the doctor diagnostic."""
from localmind.doctor import generate_doctor_report

def test_generate_report():
    report = generate_doctor_report()
    assert report.hardware is not None
    assert report.classification is not None
    assert isinstance(report.warnings, list)
    assert isinstance(report.recommendations, list)