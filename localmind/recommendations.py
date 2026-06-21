"""Recommendation logic – general and task-specific."""
from .models import HardwareReport, MachineClass, ModelRecommendation
from .classifier import classify_machine
from .constants import TASK_RECOMMENDATIONS, TIER_PARAM_RANGES


def general_recommendation(hw: HardwareReport) -> MachineClass:
    """
    Analyse hardware and return the machine class with
    a recommended parameter size range.
    """
    return classify_machine(hw)


def task_recommendations(hw: HardwareReport, task: str) -> list[ModelRecommendation]:
    """
    Return a list of recommended models for a given task (coding/writing/reasoning)
    based on the machine's tier.
    """
    mc = classify_machine(hw)
    tier = mc.tier
    task_map = TASK_RECOMMENDATIONS.get(task, {})
    model_names = task_map.get(tier, [])
    recommendations = []
    for name in model_names:
        # Simple heuristic: derive parameter size from name if possible, else unknown.
        param_size = "unknown"
        for part in name.split(":"):
            if "b" in part.lower():
                param_size = part.upper()
                break
        recommendations.append(
            ModelRecommendation(name=name, parameter_size=param_size, notes=f"Good for {task}")
        )
    if not recommendations:
        recommendations.append(
            ModelRecommendation(name="No model found", parameter_size="N/A", notes="Check Ollama library.")
        )
    return recommendations