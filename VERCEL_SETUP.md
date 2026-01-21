# Vercel 배포 설정 가이드

## 백엔드 URL
```
https://medical-article-aggregator.onrender.com
```

## Vercel 환경 변수 설정 방법

### 1. Vercel 대시보드 접속
1. [Vercel](https://vercel.com/)에 로그인
2. 프로젝트 선택 (`medical-article-aggregator`)

### 2. 환경 변수 추가
1. 프로젝트 → **Settings** → **Environment Variables**
2. 다음 변수 추가:

   | Name | Value |
   |------|-------|
   | `VITE_API_URL` | `https://medical-article-aggregator.onrender.com/api` |

3. Environment: **Production**, **Preview**, **Development** 모두 선택
4. "Save" 클릭

### 3. 재배포
환경 변수를 추가한 후 반드시 재배포해야 적용됩니다:

1. **Deployments** 탭으로 이동
2. 최신 배포 찾기
3. 오른쪽 메뉴 (⋯) 클릭
4. **Redeploy** 선택
5. "Redeploy" 버튼 클릭

### 4. 확인
재배포가 완료되면:
1. Vercel이 제공한 URL로 접속 (예: `https://medical-article-aggregator.vercel.app`)
2. 브라우저 개발자 도구 (F12) → Console 탭 확인
3. 에러가 없으면 성공!

## 문제 해결

### API 연결 에러
- Render 백엔드가 실행 중인지 확인: https://medical-article-aggregator.onrender.com/api/articles/stats
- Render 무료 플랜은 15분 비활동 후 sleep 상태가 됩니다 (첫 요청 시 30초~1분 소요)
- 환경 변수가 올바르게 설정되었는지 확인

### CORS 에러
백엔드 `app/__init__.py`에서 CORS가 올바르게 설정되어 있어야 합니다:
```python
CORS(app)  # 모든 origin 허용
```

### Render 백엔드 Sleep 방지
Render 무료 플랜은 15분 비활동 후 sleep됩니다. 방지 방법:
1. UptimeRobot 같은 서비스로 5분마다 ping
2. Render 유료 플랜 ($7/월)으로 업그레이드

## 다음 단계

1. ✅ 백엔드 배포 완료 (Render)
2. ⏳ Vercel 환경 변수 설정
3. ⏳ Vercel 재배포
4. ⏳ 사이트 확인 및 테스트

배포 완료 후 데이터베이스가 비어있을 수 있습니다. Render 대시보드에서 환경 변수가 올바르게 설정되었는지 확인하고, 프론트엔드에서 "기사 수집" 버튼을 눌러 데이터를 수집하세요.
