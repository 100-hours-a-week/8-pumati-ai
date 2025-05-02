from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from huggingface_hub import login
from faker import Faker
import os
import re


from app.context_construction.query_rewriter import GemmaPrompt
from app.fast_api.schemas.comment_schemas import CommentRequest

import time


# JSON 데이터 모델 정의
class GemmaModel:
    def __init__(self, data: CommentRequest):
        load_dotenv()
        login(token=os.getenv("HF_AUTH_TOKEN"))

        self.model_name = "google/gemma-3-1b-it"
        self.device = torch.device("cpu")
        
        self.tokenizer = None
        self.model = None
        self.pipe = None

        self.data = data

    def load_gemma(self): #처음에 서버를 띄울 때(get요청)으로 모델 실행시킬 예정.
        if self.pipe is None:  # 이미 로드한 경우 다시 로딩 안 하게 -> 서버 안정성을 높이기 위함.
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)
            self.pipe = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, device=-1)



    # 일기 생성
    def model_inference(self):
        prompt_builder = GemmaPrompt(self.data)
        prompt = prompt_builder.generate_prompt()
        output = self.pipe(prompt, max_new_tokens=200)[0]["generated_text"]
        comment_string = output[len(prompt):].strip()

        #생성된 댓글 중 JSON 안에 있는 댓글만 가져오기.
        try:
            find_comment = re.findall(r'{.*?}', comment_string, re.DOTALL)
            generated_comment = find_comment[0].strip()
        except:
            generated_comment = '{\n           "content": "좋습니다." \n}'
    
        return generated_comment
    

if __name__ == "__main__":

    dummy_data = CommentRequest(
        comment_type="칭찬",
        team_projectName="AI 이력서 생성기",
        team_shortIntro="LLM 기반 이력서 자동 생성",
        team_deployedUrl="https://resume.site",
        team_githubUrl="https://github.com/example",
        team_description="FastAPI + React 기반 프로젝트",
        team_tags=["AI", "LLM", "FastAPI"])

    
    start = time.time()
    print("start")
    gemma = GemmaModel(dummy_data)
    gemma.load_gemma()
    comment = gemma.model_inference()
    print(f"생성된 댓글: {comment}")
    print(time.time() - start)