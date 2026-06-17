import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../api/auth";
import AuthForm from "../components/AuthForm";

function Login({ onLoginSuccess }) {
  const navigate = useNavigate();
  const [authMode] = useState("login");
  const description =
    authMode === "login"
      ? "글에 어울리는 폰트를 찾아보세요"
      : "나만의 폰트 보드를 시작해보세요";

  const handleLoginSubmit = async ({ nickname, password }) => {
    const loginResponse = await loginUser({ nickname, password });
    onLoginSuccess(loginResponse.user);
    navigate("/");
  };

  return (
    <AuthForm
      buttonLabel="로그인"
      description={description}
      linkLabel="아직 계정이 없으신가요?"
      linkTo="/signup"
      onSubmit={handleLoginSubmit}
    />
  );
}

export default Login;
