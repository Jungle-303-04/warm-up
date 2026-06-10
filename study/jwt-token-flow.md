# JWT 토큰 흐름 정리

## 1. 토큰을 쓰는 이유

토큰은 백엔드가 사용자를 확인하기 위한 값입니다.

프론트가 API 요청을 보낼 때 토큰을 같이 보내면, 백엔드는 그 토큰을 보고 아래 내용을 판단합니다.

```text
이 요청을 보낸 사람이 로그인한 사용자인가?
몇 번 유저인가?
이 유저의 요청으로 처리해도 되는가?
```

## 2. 토큰은 언제 만들어지나

토큰은 로그인 성공 시 백엔드에서 만들어집니다.

```text
POST /auth/login
```

흐름:

```text
이메일/비밀번호 입력
↓
백엔드가 DB에서 유저 조회
↓
비밀번호 검증
↓
성공하면 JWT access_token 생성
↓
프론트로 access_token 반환
```

토큰 안에는 주로 아래 정보가 들어갑니다.

```text
sub = user_id
exp = 만료 시간
```

`sub`는 몇 번 유저인지 나타냅니다.

## 3. 토큰 유효시간

현재 프로젝트의 access token 유효시간은 60분입니다.

```env
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

즉 로그인 성공 후 발급된 토큰은 발급 시점부터 60분 뒤 만료됩니다.

## 4. 프론트는 토큰을 어디에 저장하나

로그인 성공 후 프론트는 토큰을 브라우저 `localStorage`에 저장합니다.

```tsx
localStorage.setItem("access_token", tokenResponse.access_token);
```

저장 위치:

```text
localStorage["access_token"]
```

## 5. API 요청 때 토큰은 어떻게 보내나

`client.ts`의 request interceptor가 API 요청 직전에 토큰을 자동으로 붙입니다.

```text
API 요청 발생
↓
localStorage에서 access_token 확인
↓
토큰이 있으면 Authorization 헤더에 붙임
↓
백엔드로 요청 보냄
```

실제 요청 형태:

```http
Authorization: Bearer <access_token>
```

즉 프론트는 백엔드에게 아래처럼 말하는 셈입니다.

```text
나 로그인한 사용자야. 이 토큰으로 확인해줘.
```

## 6. 백엔드는 토큰 유효성을 어떻게 확인하나

백엔드는 인증이 필요한 요청에서 토큰을 검사합니다.

```text
Authorization 헤더에서 Bearer 토큰 꺼냄
↓
jwt.decode()로 토큰 검증
↓
토큰 안의 sub에서 user_id 꺼냄
↓
DB에서 해당 user_id 유저 조회
↓
유저가 있으면 요청 허용
↓
실패하면 401 Unauthorized 반환
```

검증하는 것:

```text
토큰이 우리 서버 비밀키로 만든 것인가?
토큰이 조작되지 않았는가?
토큰이 만료되지 않았는가?
토큰 안에 user_id가 있는가?
그 user_id의 유저가 DB에 존재하는가?
```

## 7. `/auth/me`는 언제 호출되나

`/auth/me`는 앱이 처음 켜질 때 또는 새로고침할 때 저장된 토큰이 유효한지 확인하려고 호출됩니다.

```http
GET /auth/me
```

흐름:

```text
앱 시작 또는 새로고침
↓
localStorage에서 access_token 확인
↓
토큰이 있으면 /auth/me 요청
↓
백엔드가 토큰 검증
↓
성공하면 현재 유저 정보 반환
↓
프론트는 로그인 상태 유지
↓
실패하면 로그인 화면으로 이동
```

즉 `/auth/me`는 아래 의미의 요청입니다.

```text
내 토큰 아직 유효해?
유효하면 내 사용자 정보 줘.
```

## 8. 새로고침하면 어떤 API가 나가나

로그인 후 캘린더 화면에서 새로고침하면 앱이 처음부터 다시 실행됩니다.

보통 아래 순서로 요청이 나갑니다.

```text
1. GET /auth/me
   - 저장된 토큰 유효성 확인

2. GET /pages/calendar?year=...&month=...
   - 토큰이 유효하면 캘린더 데이터 조회
```

토큰이 만료됐으면 `/auth/me`에서 실패하고 캘린더 요청까지 가지 않습니다.

## 9. 토큰이 만료되거나 잘못되면 어떻게 되나

백엔드가 토큰 검증에 실패하면 `401 Unauthorized`를 반환합니다.

프론트의 response interceptor가 이 `401`을 받습니다.

```text
백엔드가 401 반환
↓
client.ts가 401 감지
↓
localStorage에서 access_token 삭제
↓
auth:logout 이벤트 발생
↓
App.tsx가 이벤트 감지
↓
isAuthenticated false로 변경
↓
AuthPage 로그인 화면으로 이동
```

즉 백엔드가 직접 로그아웃시키는 게 아닙니다.

```text
백엔드: 이 토큰 유효하지 않아. 401 줄게.
프론트: 401 받았네. 토큰 지우고 로그인 화면으로 보낼게.
```

## 10. 토큰 안의 유저가 DB에 없으면?

토큰 자체는 유효해도, 토큰 안의 `user_id`에 해당하는 유저가 DB에 없을 수 있습니다.

예를 들면 유저가 삭제된 경우입니다.

이때 백엔드는 DB에서 유저를 못 찾고 `401`을 반환합니다.

그러면 프론트는 똑같이 로그아웃 처리합니다.

```text
토큰 안의 user_id 확인
↓
DB에서 유저 조회
↓
유저 없음
↓
401 반환
↓
프론트가 토큰 삭제
↓
로그인 화면으로 이동
```

## 11. 로그인/회원가입 화면에서 401이 나면?

로그인/회원가입 요청에서 발생한 실패는 자동 로그아웃 처리하지 않습니다.

이유:

```text
POST /auth/login에서 401
= 비밀번호 틀림 같은 로그인 실패

POST /auth/signup 실패
= 회원가입 입력 문제 또는 중복 이메일 문제
```

이건 토큰 만료가 아니라 사용자가 입력한 값 문제입니다.

그래서 `client.ts`에서 `/auth/login`, `/auth/signup`은 자동 로그아웃 대상에서 제외합니다.

```text
로그인/회원가입 실패
↓
AuthPage.tsx의 catch에서 alert 표시
```

## 12. 전체 흐름 요약

```text
로그인
↓
백엔드가 JWT 생성
↓
프론트가 localStorage에 저장
↓
API 요청마다 Authorization: Bearer 토큰 첨부
↓
백엔드가 토큰 검증
↓
정상 → 요청 처리
↓
실패 → 401 반환
↓
프론트가 토큰 삭제 + 로그인 화면 이동
```

## 한 줄 요약

이 프로젝트의 JWT는 로그인 성공 시 백엔드가 발급하고, 프론트가 `localStorage`에 저장한 뒤 API 요청마다 Bearer 토큰으로 보냅니다.

백엔드는 토큰을 검증해서 현재 유저를 찾고, 실패하면 `401`을 보내며 프론트는 이를 받아 자동 로그아웃 처리합니다.
