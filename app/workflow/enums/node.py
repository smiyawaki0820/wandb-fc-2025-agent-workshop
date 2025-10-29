from app.domain.enums import BaseEnum


class Node(BaseEnum):
    FEEDBACK_REQUIREMENTS = "FeedbackRequirementsNode"
    GATHER_REQUIREMENTS = "GatherRequirementsNode"
    BUILD_RESEARCH_PLAN = "BuildResearchPlanNode"
    EXECUTE_TASK = "ExecuteTaskNode"
    GENERATE_REPORT = "GenerateReportNode"
