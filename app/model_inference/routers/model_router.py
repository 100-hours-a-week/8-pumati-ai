import yaml
from app.context_construction.question_router import classify_question_type
from app.services.question_filter import is_project_related

class ModelRouter:
    def __init__(self, routing_config_path: str):
        with open(routing_config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def route(self, question: str, top_doc_score: float) -> str:
        question_type = classify_question_type(question)
        related = is_project_related(question)

        for rule in self.config.get("routes", []):
            condition = rule.get("if", "")
            if "question_type == 'summary'" in condition and question_type == "summary":
                return rule["model"]
            elif (
                "related_to == 'team'" in condition and
                "confidence > 0.6" in condition and
                related and top_doc_score > 0.6
            ):
                return rule["model"]

        return "core-llm"  # fallback