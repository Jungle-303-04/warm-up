import { Route, Routes, useNavigate } from "react-router-dom";
import Header from "./components/Header";
import Board from "./pages/Board";
import Login from "./pages/Login";
import Signup from "./pages/Signup";

function App() {
  const navigate = useNavigate();
  const user = null;

  const handleLoginClick = () => {
    navigate("/login");
  };

  return (
    <div className="min-h-screen w-full max-w-[1024px] rounded-[10px] bg-white">
      <Header onLoginClick={handleLoginClick} user={user} />
      <Routes>
        <Route element={<Board />} path="/" />
        <Route element={<Login />} path="/login" />
        <Route element={<Signup />} path="/signup" />
      </Routes>
    </div>
  );
}

export default App;
