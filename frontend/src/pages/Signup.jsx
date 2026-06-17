import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signupUser } from "../api/auth";
import AuthForm from "../components/AuthForm";
import { CheckIcon } from "../components/icons";

function Signup({ onSignupSuccess }) {
  const navigate = useNavigate();
  const [authMode] = useState("signup");
  const [isSignupCompleteDialogOpen, setIsSignupCompleteDialogOpen] =
    useState(false);
  const description =
    authMode === "signup"
      ? "나만의 글과 폰트를 기록해보세요"
      : "글에 어울리는 폰트를 찾아보세요";

  const waitForSignupCompleteMessage = () => {
    return new Promise((resolve) => {
      setTimeout(resolve, 1200);
    });
  };

  const handleSignupSubmit = async ({ nickname, password }) => {
    const signupResponse = await signupUser({ nickname, password });
    onSignupSuccess(signupResponse.user);
    setIsSignupCompleteDialogOpen(true);
    await waitForSignupCompleteMessage();
    setIsSignupCompleteDialogOpen(false);
    navigate("/");
  };

  return (
    <>
      <AuthForm
        buttonLabel="회원가입"
        description={description}
        linkLabel="계정이 이미 있으신가요?"
        linkTo="/login"
        onSubmit={handleSignupSubmit}
      />

      {isSignupCompleteDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/10 px-6 backdrop-blur-[1px]">
          <div
            aria-modal="true"
            className="w-full max-w-[320px] rounded-md border border-gray-200 bg-white p-5 shadow-[0_12px_32px_rgba(15,23,42,0.14)]"
            role="dialog"
          >
            <div className="flex items-center gap-2">
              <CheckIcon className="h-5 w-5 text-black" />
              <p className="text-base font-semibold text-black">
                회원가입이 완료됐어요.
              </p>
            </div>
            <p className="mt-2 text-sm text-[#9ca3af]">
              홈 화면으로 이동할게요.
            </p>
          </div>
        </div>
      ) : null}
    </>
  );
}

export default Signup;
