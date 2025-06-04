from fast_api.schemas.badge_schemas import BadgeRequest

from deep_translator import GoogleTranslator

class BadgePrompt:
    def __init__(self, data: BadgeRequest):
        self.data = data

    ##########
    #추후 수정 필요
    #프롬프팅 자동화(BLIP모델 도입 검토)
    ##########
    def build_badge_prompt(self, team_number: int) -> str:
        return f"""Design a round enamel badge with a soft gradient background, blending sky blue and pastel purple. In the center, place a cute cartoon-style dolphin holding a golden location pin in its fin, smiling. The dolphin should look intelligent and friendly, symbolizing AI guidance. Surround it with small floating icons like stars, hearts, and tiny maps, evoking the theme of emotional journeys and personalized recommendations. Add the number "{team_number}" in elegant gold beneath the dolphin. Style should be soft 3D clay or polished enamel with gentle lighting and a dreamy atmosphere."""

    # 아래는 한국어 -> 영어로 변환.
    def translate_korean_to_english(self, korean_prompt: str) -> str:
        return GoogleTranslator(source='ko', target='en').translate(korean_prompt)
