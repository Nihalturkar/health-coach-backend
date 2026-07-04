"""
Health Assessment Workflow — LangGraph multi-step pipeline.

Flow: BMI → BMR → TDEE → Macros → Water → Ideal Weight → AI Summary
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from app.ai.mcp_servers.health_mcp import (
    calculate_bmi, calculate_bmr, calculate_tdee,
    calculate_macros, calculate_water, get_ideal_weight,
)
from app.ai.agent import call_groq


class AssessmentState(TypedDict):
    # Input
    weight_kg: float
    height_cm: float
    age: int
    gender: str
    activity_level: str
    goal: str
    medical_conditions: list
    # Computed (filled by nodes)
    bmi: Optional[float]
    bmi_category: Optional[str]
    bmr: Optional[float]
    tdee: Optional[float]
    target_calories: Optional[int]
    target_protein: Optional[int]
    target_carbs: Optional[int]
    target_fats: Optional[int]
    target_water_ml: Optional[int]
    ideal_weight_kg: Optional[float]
    summary: Optional[str]


def node_bmi(state: AssessmentState) -> dict:
    result = calculate_bmi(state["weight_kg"], state["height_cm"])
    return {"bmi": result["bmi"], "bmi_category": result["category"]}


def node_bmr(state: AssessmentState) -> dict:
    bmr = calculate_bmr(state["weight_kg"], state["height_cm"], state["age"], state["gender"])
    return {"bmr": bmr}


def node_tdee(state: AssessmentState) -> dict:
    tdee = calculate_tdee(state["bmr"], state["activity_level"])
    return {"tdee": tdee}


def node_macros(state: AssessmentState) -> dict:
    macros = calculate_macros(
        state["tdee"], state["goal"], state["weight_kg"], state["medical_conditions"]
    )
    return macros


def node_water(state: AssessmentState) -> dict:
    water = calculate_water(state["weight_kg"], state["activity_level"])
    return {"target_water_ml": water}


def node_ideal_weight(state: AssessmentState) -> dict:
    ideal = get_ideal_weight(state["height_cm"], state["gender"])
    return {"ideal_weight_kg": ideal}


def node_ai_summary(state: AssessmentState) -> dict:
    """Generate human-readable summary using Groq LLM."""
    try:
        prompt = (
            f"Summarize this health assessment in 2-3 encouraging paragraphs for the user:\n"
            f"BMI: {state['bmi']} ({state['bmi_category']})\n"
            f"BMR: {state['bmr']} cal\n"
            f"TDEE: {state['tdee']} cal\n"
            f"Goal: {state['goal'].replace('_', ' ')}\n"
            f"Target: {state['target_calories']} cal, {state['target_protein']}g protein\n"
            f"Ideal weight: {state['ideal_weight_kg']} kg, Current: {state['weight_kg']} kg\n"
            f"Medical conditions: {', '.join(state['medical_conditions'] or ['none'])}\n"
            f"Keep it short, practical, and motivating. No markdown."
        )
        summary = call_groq(
            system_prompt="You are a health coach. Give a brief, friendly assessment summary.",
            user_prompt=prompt,
            temperature=0.7,
            max_tokens=500,
        )
        return {"summary": summary}
    except Exception:
        # Fallback if LLM fails
        diff = round(abs(state["weight_kg"] - state["ideal_weight_kg"]), 1)
        direction = "lose" if state["weight_kg"] > state["ideal_weight_kg"] else "gain"
        return {
            "summary": (
                f"Your BMI is {state['bmi']} ({state['bmi_category']}). "
                f"Your ideal weight is {state['ideal_weight_kg']} kg — "
                f"you need to {direction} approximately {diff} kg. "
                f"Daily target: {state['target_calories']} calories, {state['target_protein']}g protein."
            )
        }


def build_assessment_workflow():
    """Build and compile the LangGraph assessment workflow."""
    workflow = StateGraph(AssessmentState)

    workflow.add_node("calc_bmi", node_bmi)
    workflow.add_node("calc_bmr", node_bmr)
    workflow.add_node("calc_tdee", node_tdee)
    workflow.add_node("calc_macros", node_macros)
    workflow.add_node("calc_water", node_water)
    workflow.add_node("calc_ideal_weight", node_ideal_weight)
    workflow.add_node("gen_summary", node_ai_summary)

    workflow.set_entry_point("calc_bmi")
    workflow.add_edge("calc_bmi", "calc_bmr")
    workflow.add_edge("calc_bmr", "calc_tdee")
    workflow.add_edge("calc_tdee", "calc_macros")
    workflow.add_edge("calc_macros", "calc_water")
    workflow.add_edge("calc_water", "calc_ideal_weight")
    workflow.add_edge("calc_ideal_weight", "gen_summary")
    workflow.add_edge("gen_summary", END)

    return workflow.compile()


# Pre-compiled workflow instance
assessment_workflow = build_assessment_workflow()


def run_assessment(
    weight_kg: float, height_cm: float, age: int, gender: str,
    activity_level: str, goal: str, medical_conditions: list = None,
) -> dict:
    """Run the full assessment workflow and return results."""
    input_state = {
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "age": age,
        "gender": gender,
        "activity_level": activity_level,
        "goal": goal,
        "medical_conditions": medical_conditions or [],
    }
    result = assessment_workflow.invoke(input_state)
    return result
