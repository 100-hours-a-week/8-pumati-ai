# app/github_crawling/text_splitter.py

def split_text(text):
    import re
    return re.split(r'\.\s+', text.strip())
