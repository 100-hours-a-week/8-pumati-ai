from fastapi import APIRouter
from app.fast_api.schemas.report_schemas import ProjectStatsPayload, TeamInfo, BadgeStat, DailyPumatiStat
from app.services.report_service import bar_graph, donut_graph, concat_images_horizontally, create_graph_url
from io import BytesIO

import logging, time


app_report = APIRouter()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@app_report.post("/api/reports/image")
async def receive_report_request(report_body: ProjectStatsPayload):
    '''
    동기 처리.
    '''
    logger.info(f"1-1) 리포트 생성 요청 수신. 수신된 데이터: {report_body}")
    #1. start time
    start = time.perf_counter()

    #2. 데이터 receive
    logger.info(f"1-2) 리포트 생성 수신된 데이터를 전처리 합니다.")
    team_Info = report_body.team.model_dump() #사실 이후 쓰일 지 모르겠는 team_info
    Badge_Stat = [stat.model_dump() for stat in report_body.badgeStats] #도넛 그래프
    Daily_Pumati_Stat = [stat.model_dump() for stat in report_body.dailyPumatiStats] #막대 그래프

    #2. 막대그래프 그리기
    logger.info(f"2-1) {Daily_Pumati_Stat} \n 을 바탕으로 막대그래프를 생성합니다.")
    img_bar = bar_graph(Daily_Pumati_Stat)
   #pil_img.save("my_plot.png")

    #3. 도넛그래프 그리기
    logger.info(f"3-1) {Badge_Stat} \n 을 바탕으로 도넛그래프를 생성합니다.")
    img_donut = donut_graph(Badge_Stat)

    #4. 두 그래프를 하나의 이미지로 생성하기
    logger.info(f"4-1) 생성된 막대그래프와 도넛그래프를 하나의 그래프로 합칩니다.")
    result_graph = concat_images_horizontally(img_bar, img_donut)

    #5. presignedURL에 등록하기
    with BytesIO() as image_bytes:
        result_graph.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        # 4) S3에 저장 후 url 반환받기
        public_url = create_graph_url(image_bytes, team_Info["number"])

    #6. 이미지 url 전송하기
    response = {
        "reportImageUrl" : public_url
    }

    end = time.perf_counter() - start
    logger.info(f"1-1) 리포트 생성 요청 수신. 수신된 데이터: {report_body}")

    return response