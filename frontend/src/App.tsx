import { useEffect, useState } from "react";
import "./App.css";
import { getMe } from "./api/auth";
import { AuthPage } from "./pages/AuthPage";
import { CalendarPage } from "./pages/CalendarPage";







// 흐름
// localStorage에서 access_token 확인
// 토큰이 있으면 getMe()로 /auth/me 호출
// 성공하면 로그인 상태로 보고 CalendarPage 렌더링
// 실패하면 토큰 삭제 후 AuthPage 렌더링





function App() {
  // 로그인 여부와, 앱이 처음 켜질 때 토큰 확인이 끝났는지 관리합니다.
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      // 브라우저에 저장된 JWT 토큰이 있는지 먼저 확인합니다.
      const token = localStorage.getItem("access_token");

      if (!token) {
        // 토큰이 없으면 로그인하지 않은 상태로 보고 로그인 화면을 보여줍니다.
        setIsAuthenticated(false);
        setIsAuthChecking(false);
        return;
      }

      try {
        // 토큰이 있으면 백엔드에 내 정보를 요청해서 토큰이 유효한지 확인합니다.
        await getMe();
        setIsAuthenticated(true);
      } catch (error) {
        console.error(error);
        // 토큰이 만료되었거나 잘못되었으면 저장된 토큰을 지우고 로그아웃 상태로 바꿉니다.
        localStorage.removeItem("access_token");
        setIsAuthenticated(false);
      } finally {
        // 성공/실패와 관계없이 최초 인증 확인 로딩은 끝냅니다.
        setIsAuthChecking(false);
      }
    };

    const handleForceLogout = () => {
      // API 요청 중 401 에러가 발생하면 client.ts에서 이 이벤트를 발생시켜 강제 로그아웃합니다.
      localStorage.removeItem("access_token");
      setIsAuthenticated(false);
    };

    checkAuth();

    // axios 응답 인터셉터가 발생시키는 전역 로그아웃 이벤트를 구독합니다.
    window.addEventListener("auth:logout", handleForceLogout);

    return () => {
      // 컴포넌트가 사라질 때 이벤트 리스너를 정리합니다.
      window.removeEventListener("auth:logout", handleForceLogout);
    };
  }, []);

  const handleLoginSuccess = () => {
    // AuthPage에서 로그인이 성공하면 캘린더 화면으로 전환합니다.
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    // 사용자가 직접 로그아웃하면 토큰을 삭제하고 로그인 화면으로 전환합니다.
    localStorage.removeItem("access_token");
    setIsAuthenticated(false);
  };

  if (isAuthChecking) {
    // 앱 시작 직후 토큰 유효성을 확인하는 동안 보여주는 로딩 화면입니다.
    return (
      <main className="auth-page">
        <section className="auth-card">
          <div className="auth-brand">
            <div className="auth-logo">T</div>
            <div>
              <h1>TeamLog</h1>
              <p>로그인 상태를 확인하는 중입니다...</p>
            </div>
          </div>
        </section>
      </main>
    );
  }

  if (!isAuthenticated) {
    // 로그인하지 않은 사용자는 로그인/회원가입 화면을 봅니다.
    return <AuthPage onLoginSuccess={handleLoginSuccess} />;
  }

  // 인증된 사용자는 메인 캘린더 화면을 봅니다.
  return <CalendarPage onLogout={handleLogout} />;
}

export default App;
