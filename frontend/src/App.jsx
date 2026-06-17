import { useCallback, useEffect, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { getCurrentUser, logoutUser } from "./api/auth";
import Header from "./components/Header";
import ScrollToTop from "./components/ScrollToTop";
import Board from "./pages/Board";
import Login from "./pages/Login";
import MyPage from "./pages/MyPage";
import PostDetail from "./pages/PostDetail";
import Signup from "./pages/Signup";
import Write from "./pages/Write";

function App() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    const checkCurrentUser = async () => {
      try {
        const currentUserResponse = await getCurrentUser();
        setUser(currentUserResponse.user);
      } catch {
        setUser(null);
      } finally {
        setIsCheckingAuth(false);
      }
    };

    checkCurrentUser();
  }, []);

  const handleAccountClick = () => {
    if (user) {
      navigate("/mypage");
      return;
    }

    navigate("/login");
  };

  const handleAuthSuccess = (authUser) => {
    setUser(authUser);
  };

  const handleLogout = useCallback(async ({ shouldRequestLogout = true } = {}) => {
    if (shouldRequestLogout) {
      await logoutUser();
    }

    setUser(null);
    navigate("/");
  }, [navigate]);

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen w-full max-w-[1024px] rounded-[10px] bg-white">
        <Header onAccountClick={handleAccountClick} user={user} />
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full max-w-[1024px] rounded-[10px] bg-white">
      <ScrollToTop />
      <Header onAccountClick={handleAccountClick} user={user} />
      <Routes>
        <Route element={<Board />} path="/" />
        <Route
          element={
            user ? (
              <MyPage onLogout={handleLogout} user={user} />
            ) : (
              <Navigate replace to="/login" />
            )
          }
          path="/mypage"
        />
        <Route element={<PostDetail user={user} />} path="/posts/:postId" />
        <Route
          element={user ? <Write /> : <Navigate replace to="/login" />}
          path="/posts/:postId/edit"
        />
        <Route
          element={user ? <Write /> : <Navigate replace to="/login" />}
          path="/write"
        />
        <Route
          element={<Login onLoginSuccess={handleAuthSuccess} />}
          path="/login"
        />
        <Route
          element={<Signup onSignupSuccess={handleAuthSuccess} />}
          path="/signup"
        />
      </Routes>
    </div>
  );
}

export default App;
