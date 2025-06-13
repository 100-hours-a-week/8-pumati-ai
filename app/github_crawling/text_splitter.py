# app/github_crawling/text_splitter.py

from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_text(text: str):
    """
    text를 chunk_size와 chunk_overlap 기준으로 청크 분할
    반환: List[str]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""],  # 기본 separator들
    )

    return splitter.split_text(text)