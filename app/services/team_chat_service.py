# app/services/team_chat_service.py

import torch
from app.model_inference.loaders.hyperclova_loader import HyperClovaLoader
import warnings
# from app.context_construction.prompts.chat_prompt import build_prompt_chatbot, is_function_summary_question
from app.github_crawling.vector_store_no_llm import collection
from app.github_crawling.embedding import get_embedding as embed_with_transformers

MODEL_NAME = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"
MAX_NEW_TOKENS = 150
TEMPERATURE = 0.3
TOP_P = 0.7

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.pytorch_utils")

class TeamChatService:
    def __init__(self):
        loader = HyperClovaLoader(MODEL_NAME)
        self.tokenizer, self.model, self.device = loader.load()

    def generate_answer(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                top_p=None,
                temperature=None,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        return self.tokenizer.decode(output[0], skip_special_tokens=True).strip()
    
    # def generate_team_response(self, question: str, project_id: int, top_k: int = 10) -> str:
    #     # 1. 질문 임베딩
    #     embedding = embed_with_transformers(question)

    #     # 2. 관련 문서 검색
    #     results = collection.query(
    #         query_embeddings=[embedding],
    #         n_results=top_k,
    #         where={"project_id": project_id},
    #         include=["documents", "metadatas"]
    #     )
    #     documents = results.get("documents", [])
    #     summary_mode = is_function_summary_question(question)

    #     # 3. 프롬프트 생성
    #     prompt = build_prompt_chatbot(question, documents, summary_mode)

    #     # 4. LLM 응답 생성
    #     return self.generate_answer(prompt)
