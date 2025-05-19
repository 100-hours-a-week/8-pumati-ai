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
            title="모아",
            introduction="JUST SWIPE! 카테부 사람들과 익명으로 재밌고 빠르게 소통해요",
            detailedDescription="### 모아(Moa) - 모두의 아젠다\n\n- 스와이프로 투표, AI가 지켜주는 투표 공간\n- 누구나 쉽게 만들고 투표하는, AI 로 더 쾌적한 투표 공간\n\n### 서비스 소개\n\n“에어컨을 켜자!”부터\n\n“이번 주 야근 하시는 분?”까지\n\n모아는 일상 속 모든 선택을 간편한 스와이프 한번으로 모아주는 투표 플랫폼입니다.\n\n- 스와이프로 빠른 투표 참여\n- AI 가 비속어, 스팸 자동 검열\n- 그룹 단위 투표 생성과 참여\n- 결과는 그룹별, 참여, 생성별로 한눈에\n\n복잡한 UI, 거친 표현, 공개된 게시판은 이제 그만,\n\n모아에서는 모든 투표가 부드럽고 안전하게 흐릅니다.\n\n---\n\n### 모아는 이런 분께!\n\n- 모임이나 동아리에서 빠르게 의견을 모을 때\n- 커뮤니티에서 건강한 의견 수렴 문화를 만들고 싶을 때\n- 팀 프로젝트 중 합리적 의사 결정을 내리고 싶을 때\n\n모든 아젠다를 위한,\n\n모두의 선택을 위한 공간, 모아",
            deploymentUrl="https://moagenda.com/",
            githubUrl="https://github.com/100-hours-a-week/4-bull4zo-wiki/wiki",
            tags=["카테부", "투표", "스와이프", "소통", "커뮤니티"],
            teamId=4
        )
    )

    start = time.time()
    for _ in range(4):
        comment = comment_generator_instance.generate_comment(dummy_data)
        logger.info("생성된 댓글: %s", comment)
        logger.info("실행 시간: %.2f초", time.time() - start)