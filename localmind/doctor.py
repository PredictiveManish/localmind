"""Generate a full diagnostic report."""
from .models import HardwareReport, DoctorReport, MachineClass, ModelRecommendation
from .hardware import get_full_report
from .classifier import classify_machine
from .utils import generate_warnings


def generate_doctor_report() -> DoctorReport:
    """Run all checks and produce a DoctorReport."""
    hw = get_full_report()
    classification = classify_machine(hw)
    warnings = generate_warnings(hw)
    # For the report, we can include a few general recommendations.
    # For simplicity, reuse the general recommendation as a placeholder.
    rec = ModelRecommendation(
        name="General recommendation",
        parameter_size=classification.recommended_param_range,
        notes="Based on your hardware, try models of this size."
    )
    return DoctorReport(
        hardware=hw,
        classification=classification,
        warnings=warnings,
        recommendations=[rec],
    )