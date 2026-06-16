import { useState } from "react";
import AuthForm from "../components/AuthForm";

function Login() {
  const [authMode] = useState("login");
  const description =
    authMode === "login"
      ? "글에 어울리는 폰트를 찾아보세요"
      : "나만의 폰트 보드를 시작해보세요";

  return (
    <AuthForm
      buttonLabel="로그인"
      description={description}
      linkLabel="아직 계정이 없으신가요?"
      linkTo="/signup"
    />
  );
}

export default Login;
