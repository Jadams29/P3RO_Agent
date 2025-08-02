from typing import List, TypedDict
from pydantic import BaseModel, Field
from typing import List, TypedDict

from pydantic import BaseModel, Field


class DecomposedGoal(BaseModel):
    """Pydantic model for the output of the GoalDecomposer tool."""
    criteria: List[str] = Field(
        description="A list of specific, measurable, and actionable criteria derived from the user's goal.")


class ImprovementPlan(BaseModel):
    """Pydantic model for the output of the StrategyFormulator tool."""
    plan: str = Field(description="A high-level, ordered plan to improve the prompt.")


class GeneratedPrompt(BaseModel):
    """Pydantic model for the output of the PromptGenerator tool."""
    prompt_text: str = Field(description="The full text of the newly generated prompt.")
    reasoning: str = Field(description="The reasoning behind the specific changes made in this iteration.")


class CriterionScore(BaseModel):
    """Pydantic model for a single criterion's evaluation."""
    criterion: str = Field(description="The specific criterion being evaluated.")
    score: int = Field(description="A score from 1 (fails completely) to 10 (perfectly satisfies).")
    justification: str = Field(description="A brief justification for the score, citing evidence from the prompt.")


class EvaluationResult(BaseModel):
    """Pydantic model for the output of the PromptEvaluator tool."""
    scores: List[CriterionScore] = Field(description="A list of scores for each criterion.")
    qualitative_feedback: str = Field(description="A summary of the prompt's main strengths and weaknesses.")


class Reflection(BaseModel):
    """Pydantic model for the output of the ReflectionSynthesizer tool."""
    summary: str = Field(description="A concise, actionable insight synthesized from the evaluation report.")


class AgentState(TypedDict):
    """Defines the state of the agent, serving as its memory."""
    initial_prompt: str
    goal: str
    decomposed_criteria: List[str]
    high_level_plan: str
    prompt_history: List
    current_reflection: str
    final_prompt: str
    iteration_count: int
