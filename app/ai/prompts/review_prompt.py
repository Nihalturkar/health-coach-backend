def get_review_prompt(profile: dict, stats: dict) -> str:
    return f"""You are a health coach reviewing a user's weekly progress.

## User Profile
- Goal: {profile['goal'].replace('_', ' ')}
- Target Calories: {profile.get('target_calories', 'N/A')}/day
- Target Protein: {profile.get('target_protein', 'N/A')}g/day
- Target Water: {profile.get('target_water_ml', 'N/A')}ml/day

## This Week's Stats (Week {stats['week_number']})
- Start Weight: {stats.get('start_weight', 'N/A')} kg
- End Weight: {stats.get('end_weight', 'N/A')} kg
- Avg Calories/day: {stats.get('avg_calories_consumed', 'N/A')}
- Avg Protein/day: {stats.get('avg_protein_consumed', 'N/A')}g
- Avg Water/day: {stats.get('avg_water_ml', 'N/A')} ml
- Avg Sleep: {stats.get('avg_sleep_hours', 'N/A')}h
- Workouts Completed: {stats.get('workouts_completed', 0)}
- Workouts Skipped: {stats.get('workouts_skipped', 0)}

## Instructions
1. Summarize the week's performance in 3-4 sentences
2. Identify what went well and what needs improvement
3. Provide 3-5 specific, actionable suggestions
4. If weight is not trending toward goal for weight_loss/weight_gain, suggest calorie adjustments
5. Be encouraging but honest

## Output Format
Return valid JSON only:
{{
  "ai_summary": "Your week summary here...",
  "ai_suggestions": [
    {{"area": "diet", "suggestion": "Specific suggestion here"}},
    {{"area": "workout", "suggestion": "Specific suggestion here"}},
    {{"area": "hydration", "suggestion": "Specific suggestion here"}}
  ],
  "plan_adjustments": {{
    "calories_change": 0,
    "protein_change": 0,
    "notes": "Any specific plan changes"
  }}
}}

Return only JSON."""
