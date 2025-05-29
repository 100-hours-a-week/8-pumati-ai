import os
from icrawler.builtin import BingImageCrawler

search_terms = [
    "enamel pin badge",
    "kawaii badge design",
    "pastel enamel pin",
    "modern cute badge",
    "trendy enamel pin with characters",
    "cute mascot badge design",
    "soft pastel enamel pin"
]

download_path = "./app/model_inference/fine_tuning_data/P_badges"
os.makedirs(download_path, exist_ok=True)

max_images_per_term = 50

for term in search_terms:
    crawler = BingImageCrawler(storage={"root_dir": download_path})
    crawler.crawl(keyword=term, max_num=max_images_per_term)