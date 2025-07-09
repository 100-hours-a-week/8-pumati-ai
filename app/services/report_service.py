import plotly.graph_objects as go
from PIL import Image
from io import BytesIO

import io, logging, requests, os
from dotenv import load_dotenv
load_dotenv()

BE_SERVER = os.getenv("BE_SERVER_URL")
#print("BE_SERVER", BE_SERVER)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 요일 순서 지정
def bar_graph(daily_stats):
    days_order = ["MON", "TUE", "WED", "THU", "FRI"]
    day_labels = {
        "MON": "월",
        "TUE": "화",
        "WED": "수",
        "THU": "목",
        "FRI": "금"
    }

    # 예시 데이터
    # daily_stats = [
    #     { "day": "THU", "givedPumatiCount": 7, "receivedPumatiCount": 1 },
    #     { "day": "FRI", "givedPumatiCount": 6, "receivedPumatiCount": 2 },
    #     { "day": "SAT", "givedPumatiCount": 5, "receivedPumatiCount": 3 },
    #     { "day": "SUN", "givedPumatiCount": 4, "receivedPumatiCount": 4 },
    #     { "day": "MON", "givedPumatiCount": 3, "receivedPumatiCount": 5 },
    #     { "day": "TUE", "givedPumatiCount": 2, "receivedPumatiCount": 6 },
    #     { "day": "WED", "givedPumatiCount": 1, "receivedPumatiCount": 7 }
    # ]

    # 월~금 필터링 및 정렬
    filtered = [d for d in daily_stats if d["day"] in days_order]
    filtered.sort(key=lambda x: days_order.index(x["day"]))

    x = [day_labels[d["day"]] for d in filtered]
    gived = [d["givedPumatiCount"] for d in filtered]
    received = [d["receivedPumatiCount"] for d in filtered]

    # Plotly 그래프
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x,
        y=gived,
        name='준 푸마티',
        marker_color='rgba(55, 128, 191, 0.7)'
    ))

    fig.add_trace(go.Bar(
        x=x,
        y=received,
        name='받은 푸마티',
        marker_color='rgba(219, 64, 82, 0.7)'
    ))

    fig.update_layout(
        title="요일별 푸마티 활동",
        xaxis_title="요일",
        yaxis_title="푸마티 개수",
        barmode='group',
        template='plotly_white'
    )
    #fig.write_image("output.png")
        #return fig

    buf_bargraph = io.BytesIO()
    fig.write_image(buf_bargraph, format='png')  # 내부적으로 kaleido 사용
    buf_bargraph.seek(0)
    img_bargraph = Image.open(buf_bargraph)
    return img_bargraph
#fig.show()

def donut_graph(badgeStats):
    badgeStats = [
        { "giverTerm": 2, "giverTeamNumber": 9, "badgeCount": 3 },
        { "giverTerm": 2, "giverTeamNumber": 10, "badgeCount": 4 }
    ]

    # 총 뱃지 수
    total_badges = sum(item["badgeCount"] for item in badgeStats)

    # 뱃지 수 기준 정렬
    badgeStats.sort(key=lambda x: x["badgeCount"], reverse=True)

    labels = []
    values = []

    for i, item in enumerate(badgeStats):
        team_number = item["giverTeamNumber"]
        count = item["badgeCount"]
        percent = count / total_badges * 100
        label = f"{'👑 ' if i == 0 else ''}{team_number}팀<br>{count}회 ({percent:.1f}%)"
        labels.append(label)
        values.append(count)

    # 시각 강조 설정
    pull = [0.15] + [0] * (len(values) - 1)  # 1등만 튀어나옴
    colors = ['gold'] + ['lightgray'] * (len(values) - 1)

    # 도넛 차트
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        pull=pull,
        textinfo='label',
        marker=dict(colors=colors, line=dict(color='black', width=1.5))
    )])

    fig.update_layout(
        title="팀별 받은 뱃지 수",
        template='plotly_white'
    )
    #fig.write_image("output_donut.png")
    buf_donutgraph = io.BytesIO()
    fig.write_image(buf_donutgraph, format='png')  # 내부적으로 kaleido 사용
    buf_donutgraph.seek(0)
    img_donutgraph = Image.open(buf_donutgraph)
    return img_donutgraph
#fig.show()

def concat_images_horizontally(img1: Image.Image, img2: Image.Image) -> Image.Image:
    # 두 이미지의 높이를 기준으로 정렬 (가장 높은 걸 기준으로)
    max_height = max(img1.height, img2.height)
    total_width = img1.width + img2.width

    # 새 흰색 배경 이미지 생성 (RGB or RGBA)
    new_img = Image.new("RGB", (total_width, max_height), (255, 255, 255))
    
    # 왼쪽에 img1 붙이기
    new_img.paste(img1, (0, 0))
    # 오른쪽에 img2 붙이기
    new_img.paste(img2, (img1.width, 0))
    
    return new_img

def create_graph_url(image_bytes: BytesIO, team_number: int) -> str:
    # 0) 변수 정의
    file_name = f"badge_image_{team_number}.png"
    content_type = "image/png"

    # 1) Pre-signed URL 요청
    logger.info("7-2) Presigned URL 요청")
    logger.info(f"7-3) {BE_SERVER}/api/pre-signed-url으로 post요청중...")
    response = requests.post(f"{BE_SERVER}/api/pre-signed-url", json={
        "fileName": file_name,
        "contentType": content_type
    })

    # 1-1) 예외처리
    if response.status_code != 201:
        raise Exception(f"Pre-signed URL 발급 실패: {response.text}")

    logger.info("7-4) S3에 이미지 업로드 중...")
    upload_data = response.json()["data"]
    upload_url = upload_data["uploadUrl"]
    public_url = upload_data["publicUrl"]

    # 2. S3에 PUT으로 이미지 업로드
    logger.info(f"7-5) {upload_url}에 put요청.")
    upload_response = requests.put(
        upload_url,
        data=image_bytes.getvalue(),
        headers={
            "Content-Type": content_type,
            "x-amz-acl": "public-read"
        }
    )

    # 2-1) 예외처리
    if upload_response.status_code != 200:
        raise Exception(f"S3 업로드 실패: {upload_response.text}")

    logger.info(f"7-6) S3에 업로드 성공")
    return public_url 