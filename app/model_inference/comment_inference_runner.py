from services.comment_service import GenerateComment

# 싱글턴 인스턴스 (다른 곳에서 import해서 사용)
comment_generator_instance = GenerateComment()


if __name__ == "__main__":
    import time
    from fast_api.schemas.comment_schemas import ProjectSummary, CommentRequest
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    dummy_data = CommentRequest(
        commentType="칭찬",
        projectSummary=ProjectSummary(
            title="품앗이",
            introduction="카카오테크 부트캠프를 위한 트래픽 품앗이 플랫폼",
            detailedDescription="품앗이(Pumati)는 카카오테크 부트캠프를 위한 트래픽 품앗이 플랫폼입니다.\n\n서로의 프로젝트를 사용해주는 선순환을 통해 성공적인 트래픽 시나리오를 만들어 함께 성장하는 것이 우리의 목표입니다.\n\n품앗이(Pumati)의 주요 기능이에요!\n- 프로젝트 홍보 게시판: 우리 팀의 프로젝트를 홍보하고, 다른 팀의 프로젝트도 사용해볼까?\n- 트래픽 품앗이 기능: 다른 팀의 프로젝트를 사용할수록 우리 팀의 홍보 게시글 순위가 상승!\n- 후기 작성: 서로의 프로젝트를 리뷰하며 함께 성장해요~\n- 출석 체크 기능: 출석만 하면 품앗이 포인트가 올라간다고?\n\n흩어진 파이널 프로젝트들의 정보를 매번 찾아보기 어렵고, 트래픽 하나하나가 소중한 카카오테크 부트캠프 교육생들에게\n\n디스콰이엇(disquiet)과 달리 '트래픽 품앗이'와 '크레딧' 개념을 활용하여 실시간으로 프로젝트 홍보 게시글의 순위가 변동된다는 차별점이 있고,\n\n외부인들이 프로젝트에 쉽게 접근할 수 있도록 돕고, 나아가 교육생들끼리 서로의 프로젝트를 방문하고 응원함으로써(품앗이) 모두의 성공적인 프로젝트 경험을 함께 만들어 가는 기능을 제공합니다.",
            deploymentUrl="https://tebutebu.com/",
            githubUrl="https://github.com/orgs/100-hours-a-week/teams/8/repositories",
            tags=["품앗이"],
            teamId=4
        )
    )


    start = time.time()
    for _ in range(4):
        comment = comment_generator_instance.generate_comment(dummy_data)
        logger.info("생성된 댓글: %s", comment)
        logger.info("실행 시간: %.2f초", time.time() - start)