# from pydantic import BaseModel
# from typing import List, Optional

# class TeamMember(BaseModel):
#     name: str
#     skills: List[str]
#     email: str
#     working_hours_per_week: int
#     hourly_wage: float

# class ProjectCreateRequest(BaseModel):
#     project_name: str
#     description: str
#     team_members: List[TeamMember]
#     stakeholders: List[str]
#     start_date:str
#     deadline: str  # YYYY-MM-DD
#     buffer_days: int
#     budget: float
#     budget_used: float
#     tech_stack: List[str]
#     current_stage: str  # e.g., Initial, Not started yet, Some progress
#     additional_info: Optional[str] = ""


# class TimelinePhase(BaseModel):
#     phase: str
#     duration_days: int
#     milestones: List[str]

# class WeeklyTaskAssignmentRequest(BaseModel):
#     project_data: ProjectCreateRequest
#     timeline: List[TimelinePhase]
