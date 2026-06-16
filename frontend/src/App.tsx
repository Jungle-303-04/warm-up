import { useEffect, useState } from "react";
import "./App.css";
import { getMe, type UserResponse } from "./api/auth";
import type { AppPage } from "./components/layout/AppLayout";
import { AuthPage } from "./pages/AuthPage";
import { CalendarPage } from "./pages/CalendarPage";
import { DailyMessagePage } from "./pages/DailyMessagePage";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthChecking, setIsAuthChecking] = useState(true);
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);
  // 로그인 후 현재 보여줄 메인 페이지를 관리한다.
  const [activePage, setActivePage] = useState<AppPage>("calendar");

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setIsAuthenticated(false);
        setIsAuthChecking(false);
        return;
      }

      try {
        const user = await getMe();
        setCurrentUser(user);
        setIsAuthenticated(true);
      } catch (error) {
        console.error(error);
        localStorage.removeItem("access_token");
        setCurrentUser(null);
        setIsAuthenticated(false);
      } finally {
        setIsAuthChecking(false);
      }
    };

    const handleForceLogout = () => {
      localStorage.removeItem("access_token");
      setCurrentUser(null);
      setIsAuthenticated(false);
      setActivePage("calendar");
    };

    checkAuth();
    window.addEventListener("auth:logout", handleForceLogout);

    return () => {
      window.removeEventListener("auth:logout", handleForceLogout);
    };
  }, []);

  const handleLoginSuccess = async () => {
    const user = await getMe();
    setCurrentUser(user);
    setIsAuthenticated(true);
    setActivePage("calendar");
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setCurrentUser(null);
    setIsAuthenticated(false);
    setActivePage("calendar");
  };

  if (isAuthChecking) {
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
    return <AuthPage onLoginSuccess={handleLoginSuccess} />;
  }

  if (activePage === "daily-message") {
    // 사이드바에서 오늘의 한마디를 선택한 상태다.
    return (
      <DailyMessagePage
        currentUser={currentUser}
        onLogout={handleLogout}
        onNavigate={setActivePage}
      />
    );
  }

  // 기본 화면은 캘린더다.
  return (
    <CalendarPage
      currentUser={currentUser}
      onLogout={handleLogout}
      onNavigate={setActivePage}
    />
  );
}

export default App;
