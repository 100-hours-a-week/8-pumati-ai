import plotly.graph_objects as go
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

import io, logging, requests, os

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
daily_stats = [
    { "day": "THU", "givedPumatiCount": 4, "receivedPumatiCount": 4 },
    { "day": "FRI", "givedPumatiCount": 3, "receivedPumatiCount": 5 },
    { "day": "SAT", "givedPumatiCount": 2, "receivedPumatiCount": 6 },
    { "day": "SUN", "givedPumatiCount": 1, "receivedPumatiCount": 7 },
    { "day": "MON", "givedPumatiCount": 7, "receivedPumatiCount": 1 },
    { "day": "TUE", "givedPumatiCount": 6, "receivedPumatiCount": 2 },
    { "day": "WED", "givedPumatiCount": 5, "receivedPumatiCount": 3 }
]

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
    marker_color= 'rgba(239, 136, 127, 0.5)' #'rgba(55, 128, 191, 0.7)'
))

fig.add_trace(go.Bar(
    x=x,
    y=received,
    name='받은 품앗이',
    marker_color='rgba(165, 196, 231, 0.3)'#'rgba(165, 196, 231, 0.7)' #'rgba(219, 64, 82, 0.7)'
))

fig.update_layout(
    title="금주 품앗이 횟수",
    #xaxis_title="요일",
    #yaxis_title="푸마티 개수",
    barmode='group',
    template=None,#'plotly_white',
    plot_bgcolor='rgb(254,243,223)',#'lightblue',
    bargap=0.8
)
#fig.write_image("output.png")
    #return fig

buf_bargraph = io.BytesIO()
fig.write_image(buf_bargraph, format='png')  # 내부적으로 kaleido 사용
buf_bargraph.seek(0)
img_bargraph = Image.open(buf_bargraph)


badgeStats = [
    { "giverTerm": 2, "giverTeamNumber": 9, "badgeCount": 3 },
    { "giverTerm": 2, "giverTeamNumber": 10, "badgeCount": 4 },
    { "giverTerm": 2, "giverTeamNumber": 11, "badgeCount": 2 },
    { "giverTerm": 2, "giverTeamNumber": 12, "badgeCount": 5 },
    { "giverTerm": 2, "giverTeamNumber": 13, "badgeCount": 1 },
    { "giverTerm": 2, "giverTeamNumber": 14, "badgeCount": 1 },
    { "giverTerm": 2, "giverTeamNumber": 15, "badgeCount": 1 },
]

import numpy as np
import plotly.graph_objects as go
from PIL import Image
import io
import matplotlib.pyplot as plt

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

# 회색 그라데이션 생성
# num_teams = len(values)
# gray_start = 200
# gray_end = 100
# gray_values = np.linspace(gray_start, gray_end, num=num_teams - 1).astype(int)
# gray_colors = [f'rgb({g},{g},{g})' for g in gray_values]
# colors = ['gold'] + gray_colors  # 1등 gold
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
    textfont=dict(size=13),
    insidetextorientation='horizontal',  # ✅ 회전 없는 텍스트
    marker=dict(colors=colors),
    domain=dict(x=[0.0, 0.8]) #왼쪽으로 이동
)])

fig.update_layout(
    title="받은 뱃지 비율",
    template='none',
    #paper_bgcolor='rgb(236,235,233)',
    plot_bgcolor='rgb(236,235,233)'
)

# 이미지로 변환
buf_donutgraph = io.BytesIO()
fig.write_image(buf_donutgraph, format='png')
buf_donutgraph.seek(0)
img_donutgraph = Image.open(buf_donutgraph)

plt.imshow(img_donutgraph)
plt.axis('off')
plt.show()

