# App.tsx 인증 흐름 정리

## 1. App.tsx의 역할

`App.tsx`는 앱의 입구이자 화면 분기 담당입니다.

쉽게 말하면 아래 내용을 결정합니다.

```text
이 사람이 로그인한 사람인가?
맞으면 CalendarPage 보여주기
아니면 AuthPage 보여주기
확인 중이면 로딩 보여주기
```

## 2. import 하는 것들

```tsx
import { useEffect, useState } from "react";
import { getMe } from "./api/auth";
import { AuthPage } from "./pages/AuthPage";
import { CalendarPage } from "./pages/CalendarPage";
```

각 역할:

```text
useState = 로그인 상태 기억
useEffect = 앱 처음 켜질 때 토큰 검사 실행
getMe = /auth/me 요청으로 토큰 유효성 확인
AuthPage = 로그인/회원가입 화면
CalendarPage = 로그인 후 메인 화면
```

## 3. 로그인 상태 관리

```tsx
const [isAuthenticated, setIsAuthenticated] = useState(false);
const [isAuthChecking, setIsAuthChecking] = useState(true);
```

두 상태의 의미:

```text
isAuthenticated
= 지금 로그인된 상태인가?

isAuthChecking
= 지금 토큰 확인 중인가?
```

앱이 처음 켜질 때는 아직 로그인 여부를 모릅니다.

브라우저에 토큰이 있을 수도 있고 없을 수도 있습니다.

그래서 처음에는 `isAuthChecking`을 `true`로 두고, 토큰 확인이 끝난 뒤 화면을 결정합니다.

## 4. 앱 시작 시 토큰 확인

```tsx
useEffect(() => {
  const checkAuth = async () => {
    ...
  };

  checkAuth();
}, []);
```

`useEffect(..., [])`는 `App` 컴포넌트가 처음 화면에 나타날 때 한 번 실행됩니다.

여기서 하는 일은 `localStorage`에 `access_token`이 있는지 확인하는 것입니다.

## 5. 토큰이 없을 때

```tsx
const token = localStorage.getItem("access_token");

if (!token) {
  setIsAuthenticated(false);
  setIsAuthChecking(false);
  return;
}
```

토큰이 없으면 로그인한 사용자가 아니라고 판단합니다.

```text
토큰 없음
↓
로그인 상태 false
↓
확인 끝
↓
AuthPage 보여줌
```

## 6. 토큰이 있을 때

```tsx
try {
  await getMe();
  setIsAuthenticated(true);
}
```

토큰이 있다고 무조건 믿으면 안 됩니다.

토큰이 만료됐거나 잘못된 토큰일 수도 있습니다.

그래서 백엔드에 `/auth/me` 요청으로 확인합니다.

```text
GET /auth/me
```

의미:

```text
이 토큰 아직 유효해?
유효하면 내 정보 줘.
```

성공하면 로그인 상태로 보고 캘린더 화면을 보여줍니다.

## 7. 토큰이 잘못됐을 때

```tsx
catch (error) {
  localStorage.removeItem("access_token");
  setIsAuthenticated(false);
}
```

`getMe()`가 실패하면 보통 토큰이 만료됐거나 잘못된 경우입니다.

그러면 더 이상 그 토큰을 쓰면 안 되므로 삭제합니다.

```text
토큰 삭제
↓
로그인 상태 false
↓
AuthPage 보여줌
```

## 8. finally의 역할

```tsx
finally {
  setIsAuthChecking(false);
}
```

성공하든 실패하든 토큰 확인은 끝났으므로 로딩 상태를 끝냅니다.

```text
확인 중 화면 종료
```

## 9. 강제 로그아웃 이벤트 처리

```tsx
const handleForceLogout = () => {
  localStorage.removeItem("access_token");
  setIsAuthenticated(false);
};
```

이 코드는 앱 사용 중 API 요청이 `401`을 받았을 때를 위한 처리입니다.

예를 들어 캘린더를 보다가 토큰이 만료되면 `client.ts`에서 아래 이벤트를 보냅니다.

```tsx
window.dispatchEvent(new Event("auth:logout"));
```

`App.tsx`는 이 이벤트를 듣고 있습니다.

```tsx
window.addEventListener("auth:logout", handleForceLogout);
```

흐름:

```text
API 요청 중 401 발생
↓
client.ts가 auth:logout 이벤트 발생
↓
App.tsx가 이벤트 감지
↓
토큰 삭제
↓
isAuthenticated false
↓
AuthPage로 이동
```

## 10. 이벤트 리스너 정리

```tsx
return () => {
  window.removeEventListener("auth:logout", handleForceLogout);
};
```

컴포넌트가 사라질 때 이벤트 리스너를 제거합니다.

이 코드는 메모리 누수나 중복 실행을 막기 위한 정리 코드입니다.

## 11. 로그인 성공 처리

```tsx
const handleLoginSuccess = () => {
  setIsAuthenticated(true);
};
```

`AuthPage`에서 로그인 성공하면 이 함수를 호출합니다.

```tsx
<AuthPage onLoginSuccess={handleLoginSuccess} />
```

흐름:

```text
AuthPage에서 로그인 성공
↓
토큰 저장
↓
onLoginSuccess()
↓
App.tsx의 handleLoginSuccess 실행
↓
isAuthenticated true
↓
CalendarPage 렌더링
```

## 12. 직접 로그아웃 처리

```tsx
const handleLogout = () => {
  localStorage.removeItem("access_token");
  setIsAuthenticated(false);
};
```

사용자가 로그아웃 버튼을 누르면 실행됩니다.

흐름:

```text
로그아웃 클릭
↓
토큰 삭제
↓
isAuthenticated false
↓
AuthPage로 이동
```

이 함수는 `CalendarPage`로 넘깁니다.

```tsx
<CalendarPage onLogout={handleLogout} />
```

## 13. 화면 분기

이 부분이 핵심입니다.

```tsx
if (isAuthChecking) {
  return <로딩 화면 />;
}
```

토큰 확인 중이면 로딩 화면을 보여줍니다.

```tsx
if (!isAuthenticated) {
  return <AuthPage onLoginSuccess={handleLoginSuccess} />;
}
```

로그인하지 않은 상태면 로그인/회원가입 화면을 보여줍니다.

```tsx
return <CalendarPage onLogout={handleLogout} />;
```

로그인된 상태면 캘린더 화면을 보여줍니다.

## 14. 전체 흐름

앱 시작 흐름:

```text
App 실행
↓
isAuthChecking = true
↓
localStorage에서 access_token 확인
↓
토큰 없음
   → AuthPage
↓
토큰 있음
   → getMe()로 /auth/me 요청
      ↓
      성공 → CalendarPage
      실패 → 토큰 삭제 후 AuthPage
```

로그인 후 흐름:

```text
AuthPage에서 로그인 성공
↓
토큰 저장
↓
onLoginSuccess()
↓
App.tsx가 isAuthenticated true
↓
CalendarPage 표시
```

로그아웃 후 흐름:

```text
로그아웃 버튼 클릭
↓
토큰 삭제
↓
isAuthenticated false
↓
AuthPage 표시
```

## 한 줄 요약

`App.tsx`는 앱이 시작될 때 토큰을 확인해서 로그인 상태를 판단하고, 그 결과에 따라 `AuthPage` 또는 `CalendarPage`를 보여주는 최상위 화면 컨트롤러입니다.
