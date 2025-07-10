import plotly.graph_objects as go
from PIL import Image
from io import BytesIO
import numpy as np

import io, logging, requests, os
from dotenv import load_dotenv
load_dotenv()

BE_SERVER = os.getenv("BE_SERVER_URL")
#print("BE_SERVER", BE_SERVER)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 요일 순서 지정
def bar_graph(daily_stats):
    days_order = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    day_labels = {
        "MON": "월",
        "TUE": "화",
        "WED": "수",
        "THU": "목",
        "FRI": "금",
        "SAT": "토",
        "SUN": "일"
    }

    # 예시 데이터
    # daily_stats = [
    #     { "day": "THU", "givedPumatiCount": 4, "receivedPumatiCount": 4 },
    #     { "day": "FRI", "givedPumatiCount": 3, "receivedPumatiCount": 5 },
    #     { "day": "SAT", "givedPumatiCount": 2, "receivedPumatiCount": 6 },
    #     { "day": "SUN", "givedPumatiCount": 1, "receivedPumatiCount": 7 },
    #     { "day": "MON", "givedPumatiCount": 7, "receivedPumatiCount": 1 },
    #     { "day": "TUE", "givedPumatiCount": 6, "receivedPumatiCount": 2 },
    #     { "day": "WED", "givedPumatiCount": 5, "receivedPumatiCount": 3 }
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
        name='준 품앗이',
        marker_color= 'rgba(239, 136, 127, 0.5)', #'rgba(55, 128, 191, 0.7)'
        textfont=dict(size=30)
    ))

    fig.add_trace(go.Bar(
        x=x,
        y=received,
        name='받은 품앗이',
        marker_color='rgba(165, 196, 231, 0.3)',#'rgba(165, 196, 231, 0.7)' #'rgba(219, 64, 82, 0.7)'
        textfont=dict(size=30)
    ))

    fig.update_layout(
        title="금주 품앗이 횟수",
        #xaxis_title="요일",
        #yaxis_title="푸마티 개수",
        barmode='group',
        template=None,#'plotly_white',
        plot_bgcolor='rgb(254,243,223)',#'lightblue',
        bargap=0.8,
        font=dict(
        family="Nanum Gothic",  # 또는 "Nanum Gothic"
        size=35,
        color="black"
        )
    )
    #fig.write_image("output.png")
        #return fig

    buf_bargraph = io.BytesIO()
    fig.write_image(buf_bargraph, format='png', width=2000, height=1200, scale=3)  # 내부적으로 kaleido 사용
    buf_bargraph.seek(0)
    img_bargraph = Image.open(buf_bargraph)
    return img_bargraph
#fig.show()

def donut_graph(badgeStats):
    # badgeStats = [
    #     { "giverTerm": 2, "giverTeamNumber": 9, "badgeCount": 3 },
    #     { "giverTerm": 2, "giverTeamNumber": 10, "badgeCount": 4 }
    # ]

    # 총 뱃지 수
    total_badges = sum(item["badgeCount"] for item in badgeStats)
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

    num_teams = len(values)

    # 🥇🥈🥉 RGB 고정 색상
    rank_colors_rgb = [
        (242, 224, 52),   # 1등
        (192, 153, 78),   # 2등
        (121, 92, 47)     # 3등
    ]

    # 상위 3등 색상 변환
    rank_colors = [f'rgb({r},{g},{b})' for r, g, b in rank_colors_rgb[:num_teams]]

    # 나머지 팀 수
    remaining = num_teams - len(rank_colors)

    if remaining > 0:
        # 회색 그라데이션 생성
        gray_start = 200
        gray_end = 100
        gray_values = np.linspace(gray_start, gray_end, num=remaining).astype(int)
        gray_colors = [f'rgb({g},{g},{g})' for g in gray_values]
    else:
        gray_colors = []

    # 최종 색상 조합
    colors = rank_colors + gray_colors

    # 도넛 차트 생성
    pull = [0.15] + [0] * (num_teams - 1)

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        pull=pull,
        textinfo='label',
        sort=False,
        showlegend=True,
        direction='clockwise',
        textposition='outside',
        #textinfo='label+percent',
        textfont=dict(size=30),
        insidetextorientation='horizontal',  # ✅ 회전 없는 텍스트
        marker=dict(colors=colors),
        domain=dict(x=[0.0, 0.8]) #왼쪽으로 이동
    )])

    fig.update_layout(
        title="받은 뱃지 비율",
        template='none',
        #paper_bgcolor='rgb(236,235,233)',
        plot_bgcolor='rgb(236,235,233)',
        font=dict(
        family="Nanum Gothic",  # 또는 "Nanum Gothic"
        size=35,
        color="black"
        )
    )

    # 이미지로 변환
    buf_donutgraph = io.BytesIO()
    fig.write_image(buf_donutgraph, format='png',width=2000, height=1200,scale=3)
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
