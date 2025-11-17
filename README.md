# Business OS - Event-Driven Ontology System

**LLM 기반 이벤트 스토밍 → Palantir 온톨로지 → Given-When-Then 룰 엔진**

## 개요

Business OS는 자연어로 비즈니스를 설명하면 자동으로 다음을 생성하는 지능형 시스템입니다:
- **이벤트 스토밍 분석** (DDD Aggregates, Commands, Events, Policies)
- **Palantir 스타일 3-Layer 온톨로지** (Semantic → Kinetic → Dynamic)
- **Given-When-Then 룰 엔진** (선언적 비즈니스 로직)
- **Neo4j 디지털 트윈** (실시간 상태 동기화)

## 아키텍처

```
사용자 프롬프트
    ↓ (LLM)
이벤트 스토밍 결과
    ↓ (온톨로지 빌더)
Neo4j 3-Layer 온톨로지
    ↓ (Vue Flow 시각화)
사용자 검증 및 수정
    ↓ (룰 엔진)
비즈니스 실행 (Command → Event → Policy)
```

## 기술 스택

### 백엔드
- **FastAPI** (Python 3.11+)
- **Neo4j** (그래프 데이터베이스)
- **OpenAI GPT-4** (LLM)
- **Pydantic** (검증)
- **Kafka** (이벤트 버스)

### 프론트엔드
- **Vue 3** (Composition API)
- **Vue Flow** (그래프 시각화)
- **Pinia** (상태 관리)
- **Vite** (빌드 도구)

## 빠른 시작

### 사전 요구사항
- Docker & Docker Compose
- OpenAI API Key

### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# OpenAI API Key 설정
# .env 파일에서 OPENAI_API_KEY 입력
```

### 2. 실행

```bash
# 모든 서비스 시작 (Neo4j, Kafka, Backend, Frontend)
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3. 접속

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j/password)

## 사용 예제

### 1. 이벤트 스토밍

프론트엔드에서 비즈니스 설명 입력:

```
주문 관리 시스템을 만들고 싶어요.
고객이 상품을 선택하고 주문하면 결제가 처리됩니다.
결제가 완료되면 자동으로 배송이 시작되고 고객에게 이메일이 발송됩니다.
```

LLM이 자동 생성:
- **Aggregates**: Order, Payment, Shipment
- **Commands**: PlaceOrder, ProcessPayment, CreateShipment
- **Events**: OrderPlaced, PaymentCompleted, ShipmentCreated
- **Policies**: start_shipment_on_payment

### 2. 온톨로지 생성

Vue Flow에서 시각화된 결과를 확인하고 수정 후 "온톨로지 생성" 버튼 클릭

→ Neo4j에 3-Layer 온톨로지 자동 생성

### 3. 비즈니스 실행

```bash
# 주문 생성 Command 실행
curl -X POST http://localhost:8000/api/commands/PlaceOrder \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": "prod-1", "price": 50000, "quantity": 2}
    ]
  }'

# → OrderPlaced 이벤트 자동 발행
# → Policy 실행 (결제 처리)
# → PaymentCompleted 이벤트
# → 배송 생성 자동 시작
```

## 프로젝트 구조

```
business-os/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # REST 엔드포인트
│   │   ├── services/       # 비즈니스 로직
│   │   ├── models/         # Pydantic 모델
│   │   ├── db/             # Neo4j 클라이언트
│   │   └── domain/         # Aggregate 구현
│   ├── rules/              # GWT 룰 정의 (YAML)
│   └── prompts/            # LLM 프롬프트 템플릿
├── frontend/               # Vue 3 프론트엔드
│   └── src/
│       ├── components/     # Vue 컴포넌트
│       └── stores/         # Pinia 스토어
└── docker-compose.yml      # 전체 스택
```

## 핵심 기능

### 1. LLM 이벤트 스토밍
- 자연어 → DDD 구조 자동 추출
- Few-shot 학습으로 정확도 향상
- 대화형 개선 (반복 피드백)

### 2. Palantir 3-Layer 온톨로지
- **Semantic Layer**: 스키마 정의
- **Kinetic Layer**: 변환 로직
- **Dynamic Layer**: 런타임 인스턴스

### 3. Given-When-Then 룰 엔진
```yaml
rule: validate_order_total
given:
  aggregate: Order
  state: draft
when:
  event: ORDER_LINE_ADDED
then:
  - action: recalculate_total
  - condition: total > 1000000
    then:
      - action: require_approval
```

### 4. 디지털 트윈
- Neo4j에 실시간 상태 동기화
- 이벤트 소싱 기반 감사 추적
- 시간 여행 쿼리 지원

## API 문서

### 이벤트 스토밍
```http
POST /api/event-storm/analyze
Content-Type: application/json

{
  "description": "비즈니스 설명..."
}
```

### 온톨로지 생성
```http
POST /api/ontology/build
Content-Type: application/json

{
  "aggregates": [...],
  "policies": [...]
}
```

### Command 실행
```http
POST /api/commands/{CommandName}
Content-Type: application/json

{
  "aggregate_id": "optional",
  "params": {...}
}
```

## 개발 가이드

### 백엔드 개발 모드
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 프론트엔드 개발 모드
```bash
cd frontend
npm install
npm run dev
```

### 새로운 Aggregate 추가
1. `backend/app/domain/aggregates/` 에 Python 클래스 생성
2. Commands와 Events 정의
3. `backend/rules/` 에 GWT 룰 추가
4. LLM이 자동으로 온톨로지 업데이트

## 테스트

```bash
# 백엔드 테스트
cd backend
pytest

# 프론트엔드 테스트
cd frontend
npm run test
```

## 배포

```bash
# 프로덕션 빌드
docker-compose -f docker-compose.prod.yml up -d

# Kubernetes (선택)
kubectl apply -f k8s/
```

## 라이선스

MIT License

## 기여

Pull Request 환영합니다!

## 참고 자료

- [Event Storming](https://www.eventstorming.com/)
- [Domain-Driven Design](https://domainlanguage.com/ddd/)
- [Palantir Foundry](https://www.palantir.com/platforms/foundry/)
- [Neo4j Graph Database](https://neo4j.com/)

## 문의

이슈를 등록하거나 이메일로 문의주세요.
