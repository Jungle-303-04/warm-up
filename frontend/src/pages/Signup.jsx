import { useState } from "react";
import AuthForm from "../components/AuthForm";

function Signup() {
  const [authMode] = useState("signup");
  const description =
    authMode === "signup"
      ? "나만의 글과 폰트를 기록해보세요"
      : "글에 어울리는 폰트를 찾아보세요";

  return (
    <AuthForm
      buttonLabel="회원가입"
      description={description}
      linkLabel="계정이 이미 있으신가요?"
      linkTo="/login"
    />
  );
}

export default Signup;
