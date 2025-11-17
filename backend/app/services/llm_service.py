from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from typing import Dict, List, Optional
import json
import logging

from app.config import settings
from app.models.event_storm import EventStormResult

logger = logging.getLogger(__name__)

EVENT_STORM_SYSTEM_PROMPT = """당신은 도메인 주도 설계(DDD)와 이벤트 스토밍 전문가입니다.
사용자의 비즈니스 설명을 분석하여 다음을 추출하세요:

## 분석 요소
1. **Aggregates**: 트랜잭션 일관성 경계
2. **Commands**: 사용자 의도 (명령형)
3. **Events**: 일어난 사실 (과거형)
4. **Policies**: "~발생 시, ~수행" 규칙
5. **State**: Aggregate의 상태 필드

## 규칙
- Aggregate명: UpperCamelCase (Order, Payment)
- Command명: 명령형 (PlaceOrder, ProcessPayment)
- Event명: 과거형 (OrderPlaced, PaymentProcessed)
- Policy명: 설명적 (send_notification_on_order)

## 출력 형식 (JSON)
{
  "aggregates": [
    {
      "name": "Order",
      "commands": [{"name": "PlaceOrder", "parameters": [...]}],
      "events": [{"name": "OrderPlaced", "data": {...}}],
      "state": {"status": "enum", "total": "number"},
      "invariants": ["total >= 0", "paid orders cannot be cancelled"]
    }
  ],
  "policies": [
    {
      "name": "start_shipment_on_payment",
      "trigger_event": "PaymentCompleted",
      "actions": ["CreateShipment"]
    }
  ]
}
"""

class LLMService:
    def __init__(self):
        self.provider = settings.llm_provider
        
        if self.provider == "openai":
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.llm_model
        else:
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.model = "claude-3-sonnet-20240229"
    
    async def analyze_business(
        self,
        description: str,
        examples: Optional[List[Dict]] = None
    ) -> EventStormResult:
        """비즈니스 설명 → 이벤트 스토밍 결과"""
        
        prompt = self._build_prompt(description, examples)
        
        try:
            if self.provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": EVENT_STORM_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=settings.llm_temperature
                )
                raw_json = response.choices[0].message.content
            else:
                # Anthropic Claude
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=settings.llm_temperature,
                    system=EVENT_STORM_SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                raw_json = response.content[0].text
            
            # JSON 파싱 및 Pydantic 검증
            parsed = json.loads(raw_json)
            result = EventStormResult.model_validate(parsed)
            
            logger.info(f"이벤트 스토밍 성공: {len(result.aggregates)}개 Aggregate")
            return result
            
        except Exception as e:
            logger.error(f"LLM 분석 실패: {e}")
            raise
    
    def _build_prompt(
        self,
        description: str,
        examples: Optional[List[Dict]] = None
    ) -> str:
        """프롬프트 구성"""
        prompt = f"## 비즈니스 설명\n{description}\n\n"
        
        if examples:
            prompt += "## 참고 예제\n"
            for ex in examples:
                prompt += f"입력: {ex['input']}\n"
                prompt += f"출력: {json.dumps(ex['output'], ensure_ascii=False, indent=2)}\n\n"
        
        prompt += "위 형식으로 JSON을 출력하세요:"
        return prompt
    
    async def refine_result(
        self,
        current_result: EventStormResult,
        feedback: str
    ) -> EventStormResult:
        """사용자 피드백으로 결과 개선"""
        
        prompt = f"""
현재 분석 결과:
{current_result.model_dump_json(indent=2, exclude_none=True)}

사용자 피드백:
{feedback}

피드백을 반영하여 수정된 전체 결과를 JSON으로 출력하세요:
"""
        
        if self.provider == "openai":
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EVENT_STORM_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=settings.llm_temperature
            )
            raw_json = response.choices[0].message.content
        else:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=settings.llm_temperature,
                system=EVENT_STORM_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            raw_json = response.content[0].text
        
        parsed = json.loads(raw_json)
        return EventStormResult.model_validate(parsed)
