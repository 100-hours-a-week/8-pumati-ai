import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO

query = "badge design"
download_path = "./badges"
os.makedirs(download_path, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0"
}

url = f"https://dribbble.com/search/{query.replace(' ', '%20')}"

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")
img_tags = soup.find_all("img")

for i, img in enumerate(img_tags):
    img_url = img.get("src")
    if not img_url or not img_url.startswith("http"):
        continue
    try:
        img_data = requests.get(img_url, timeout=5).content
        image = Image.open(BytesIO(img_data)).convert("RGB")
        image.save(os.path.join(download_path, f"badge_{i}.jpg"))
    except:
        continue

print("다운로드 완료!")
