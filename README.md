- 백엔드 설계 문서:
https://glossy-cello-8d3.notion.site/ERD-API-2563ae1b20c680ccb481f7223dd5a73a?source=copy_link
- 모델 의존성 버전 변경사항:
https://glossy-cello-8d3.notion.site/_-2583ae1b20c6809cacedf700028e200a?source=copy_link
- 포스트맨 테스트 문서:
https://glossy-cello-8d3.notion.site/2583ae1b20c6807c925ad399ecfa92c4?source=copy_link
- 통합테스트 QA 문서:
https://glossy-cello-8d3.notion.site/QA-2583ae1b20c68016841bd5059ef4b7f4?source=copy_link
- .env:
https://www.notion.so/env-2583ae1b20c680d6b986e0984822b7cc?source=copy_link
---
requirements.txt 의존성들을 모두 받아야 모델이 로컬에서 동작함.
두 번째 '모델 의존성 버전 변경사항'을 읽어보면 알겠지만, 해당 requirements는 python 3.11, window 기준으로 호환되도록 변경되어서 각자 로컬에 맞게 변경이 필요할 수 있습니다..🤮🤮
### venv 사용 시:
```
1. python -m venv venv        # 가상환경 생성
2. source venv/bin/activate   # Windows: .venv\Scripts\activate       -> 좌측에 (.venv) 표시 뜨면 venv 환경에 들어온 것.
3. pip install -r requirements.txt    # requirements.txt 내 의존성들 모두 설치
4. 프로젝트 구조에서 python SDK를 .venv/Scripts/python.exe로 바꿔주기
```

### 전역 Python 환경 사용 시:
```
pip install -r requirements.txt
```

### 기타 서버실행을 위한 필수 설치 패키지 
```
pip install fastapi
pip install uvicorn
pip install sqlalchemy
pip install openai
pip install dotenv
pip install psycopg2
```
