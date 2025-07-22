import yaml
from app.context_construction.question_router import classify_question_type
from app.services.question_filter import is_project_related

class ModelRouter:
    def __init__(self, routing_config_path: str):
        with open(routing_config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def route(self, question: str, top_doc_score: float, docs: list[str]) -> str:
        question_type = classify_question_type(question)
        related = is_project_related(question, docs)

        valid_types = {"summary", "project", "function"}
        for rule in self.config.get("routes", []):
            condition = rule.get("if", "")
            if "question_type ==" in condition:
                qtype = condition.split("==")[-1].strip().strip("'\"")
                if qtype not in valid_types:
                    print(f"[🚨 Warning] Unknown question_type '{qtype}' in routing rule → skipped")
                    continue

        print(f"[질문 분석]")
        print(f"• 질문: {question}")
        print(f"• question_type: {question_type}")
        print(f"• related_to_team: {related}")
        print(f"• top_doc_score: {top_doc_score}")

        for rule in self.config.get("routes", []):
            condition = rule.get("if", "")
            if "question_type == 'summary'" in condition and question_type == "summary":
                print(f"[Routing Rule] {condition} → {rule['model']}")
                return rule["model"]
            elif "question_type == 'project'" in condition and question_type == "project":
                print(f"[Routing Rule] {condition} → {rule['model']}")
                return rule["model"]
            elif "question_type == 'function'" in condition and question_type == "function":
                print(f"[Routing Rule] {condition} → {rule['model']}")
                return rule["model"]
            elif (
                "related_to == 'team'" in condition and
                "confidence > 0.6" in condition and
                related and top_doc_score > 0.6
            ):
                print(f"[Routing Rule] {condition} → {rule['model']}")
                return rule["model"]

        print("[⚠️ Fallback] No matched rule → core-llm")
        return "core-llm"
