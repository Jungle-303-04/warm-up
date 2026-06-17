import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { getCurrentUser } from "./api/auth";
import Header from "./components/Header";
import Board from "./pages/Board";
import Login from "./pages/Login";
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

  const handleLoginClick = () => {
    navigate("/login");
  };

  const handleAuthSuccess = (authUser) => {
    setUser(authUser);
  };

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen w-full max-w-[1024px] rounded-[10px] bg-white">
        <Header onLoginClick={handleLoginClick} user={user} />
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full max-w-[1024px] rounded-[10px] bg-white">
      <Header onLoginClick={handleLoginClick} user={user} />
      <Routes>
        <Route element={<Board />} path="/" />
        <Route element={<PostDetail />} path="/posts/:postId" />
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
