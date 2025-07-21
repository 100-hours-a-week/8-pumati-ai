from google.cloud import storage
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import os, logging, requests, gc

load_dotenv()
BUCKET_NAME = os.getenv("BUCKET_NAME")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

#먼저 GCS에 이미지 파일이 있는지 확인하기
def gcs_blob_exists(blob_path: str) -> bool:
    """
    GCS에 해당 blob이 존재하면 True, 아니면 False를 반환
    """
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"teamImg/{blob_path}")

    exists = blob.exists()
    logger.info(f"GCS-1) {'파일이 존재합니다.' if exists else '파일이 존재하지 않습니다.'}: {blob_path}")
    return exists

#URL 반환 함수. 함수로 만든 이유는 URL을 가능한 숨기기 위해서이다.
# def get_gcs_url(blob_path: str) -> str:
#     """
#     GCS에 업로드된 파일의 public URL 반환
#     (퍼블릭 버킷일 경우에만 외부 접근 가능)
#     """
#     logger.info(f"GCS-2) URL: https://storage.googleapis.com/{BUCKET_NAME}/teamImg/{blob_path}")
#     return f"https://storage.googleapis.com/{BUCKET_NAME}/teamImg/{blob_path}"

# def load_image_from_gcs_url(gcs_url: str) -> Image.Image:
#     """
#     GCS public URL로부터 이미지를 다운로드하여 PIL Image로 반환
#     """
#     response = requests.get(gcs_url)
#     response.raise_for_status()  # 200 OK가 아닐 경우 예외 발생
#     return Image.open(BytesIO(response.content))

def load_image_from_gcs(blob_path: str) -> Image.Image:
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"teamImg/{blob_path}")
    image_data = blob.download_as_bytes()
    return Image.open(BytesIO(image_data))

#이미지 파일 업로드
def upload_pil_image_to_gcs(pil_img: Image.Image, blob_path: str) -> str:
    """
    PIL 이미지 객체를 GCS에 업로드합니다 (파일 저장 없이 BytesIO 사용)
    이미 해당 blob이 존재하면 업로드하지 않고 URL만 반환합니다.
    """

    # 1. GCS 준비
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"teamImg/{blob_path}")

    # 2. 존재하면 업로드 생략
    if blob.exists():
        logger.info(f"GCS-3) GCS에 이미 이미지가 존재하여 업로드 하지 않습니다.: {blob_path}")
        return f"https://storage.googleapis.com/{BUCKET_NAME}/teamImg/{blob_path}"
    
    crawling_path = f"{blob_path.split('/')[0]}/1_crawling.png"
    if blob_path != crawling_path:
        blob_cr = bucket.blob(f"teamImg/{crawling_path}")
        if not blob_cr.exists():
            logger.info(f"GCS-4) 크롤링 이미지가 없어, 이미지를 저장하지 않습니다.: {blob_path}")
            return f"https://storage.googleapis.com/{BUCKET_NAME}/teamImg/{blob_path}"

    # 3. PIL 이미지 → BytesIO 저장
    buffer = BytesIO()
    pil_img.save(buffer, format="PNG")
    buffer.seek(0)  # 포인터 맨 앞으로

    # 4. GCS 업로드
    blob.upload_from_file(buffer, content_type="image/png", rewind=True)
    logger.info(f"GCS-5) 업로드 완료: {blob_path}")

    del buffer, pil_img
    gc.collect()

    return f"https://storage.googleapis.com/{BUCKET_NAME}/teamImg/{blob_path}"

def mods_tag_name_mapping(mod_tags: str):
    logger.info(f"GCS-0) mod_tag: {mod_tags}에 해당하는 이름을 매핑합니다.")
    if mod_tags == "뉴스":
        return "4_news.png"

    elif mod_tags == "자연 풍경":
        return "5_nature.png"

    elif mod_tags == "우드":
        return "6_wood.png"

    elif mod_tags == "픽셀":
        return "6_pixel.png"

    elif mod_tags == "게임":
        return "7_game.png"
    
    else:
        return "3_original.png"