# app/context_construction/prompts/chat_prompt.py

from langchain.prompts import PromptTemplate

# HyperCLOVA에 최적화된 단순 프롬프트
SIMPLE_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["question", "context"],
    template="""
    You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Question: {question} 
    Context: {context} 
    Answer:
"""
)