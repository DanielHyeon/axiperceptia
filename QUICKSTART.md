# Business OS - 빠른 시작 가이드

## 🎉 프로젝트 생성 완료!

전체 Business OS 시스템이 생성되었습니다.

## 📦 포함된 내용

### 백엔드 (Python/FastAPI)
- ✅ LLM 서비스 (OpenAI/Anthropic)
- ✅ 이벤트 스토밍 분석기
- ✅ Palantir 온톨로지 빌더
- ✅ Neo4j 클라이언트
- ✅ Command/Query API
- ✅ Given-When-Then 룰 예제

### 프론트엔드 (Vue 3)
- ✅ 이벤트 스토밍 캔버스
- ✅ Vue Flow 시각화
- ✅ Dagre 자동 레이아웃

### 인프라
- ✅ Docker Compose (Neo4j, Kafka, 백엔드, 프론트엔드)
- ✅ 환경 설정 템플릿

## 🚀 실행 방법

### 1. 압축 해제
```bash
tar -xzf business-os.tar.gz
cd business-os
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어서 OPENAI_API_KEY 입력
```

### 3. Docker Compose 실행
```bash
docker-compose up -d
```

### 4. 접속
- 프론트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

## 📝 사용 예제

### 1. 이벤트 스토밍
프론트엔드에서 다음을 입력:
```
주문 관리 시스템을 만들고 싶어요.
고객이 상품을 선택하고 주문하면 결제가 처리됩니다.
결제가 완료되면 자동으로 배송이 시작되고 고객에게 이메일이 발송됩니다.
```

### 2. 온톨로지 생성
Vue Flow에서 "온톨로지 생성" 버튼 클릭

### 3. Command 실행
```bash
curl -X POST http://localhost:8000/api/commands/PlaceOrder \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "items": [{"product_id": "p1", "price": 50000, "quantity": 2}]
    }
  }'
```

## 🔧 개발 모드

### 백엔드만 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 프론트엔드만 실행
```bash
cd frontend
npm install
npm run dev
```

## 📚 다음 단계

1. **룰 엔진 구현**: `backend/app/services/rule_engine.py` 완성
2. **Aggregate 구현**: `backend/app/domain/aggregates/` 에 비즈니스 로직 추가
3. **Kafka 통합**: 이벤트 버스 연결
4. **추가 UI**: 온톨로지 편집기, 룰 에디터 등

## 🐛 트러블슈팅

### Neo4j 연결 실패
```bash
docker-compose logs neo4j
# Neo4j가 완전히 시작될 때까지 30초 대기
```

### 포트 충돌
```bash
# docker-compose.yml에서 포트 변경
# 예: "5173:5173" → "3000:5173"
```

## 📖 참고 문서

- [프로젝트 README](./README.md)
- [이벤트 스토밍 가이드](https://www.eventstorming.com/)
- [Palantir Foundry](https://www.palantir.com/platforms/foundry/)

## ⭐ 핵심 특징

- LLM이 자동으로 도메인 모델 생성
- Neo4j에 온톨로지 + 데이터 통합 저장
- Given-When-Then 선언적 비즈니스 로직
- Vue Flow로 시각적 검증
- 이벤트 소싱 기반 감사 추적

---

**프로젝트 시작을 축하합니다! 🎉**
