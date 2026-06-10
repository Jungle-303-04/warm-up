import { useState } from "react";
import { login, signup } from "../api/auth";


// 로그인 성공 후 부모 App.tsx가 넘겨준 함수 실행
type AuthPageProps = {
  onLoginSuccess: () => void;
};


// 흐름
// 로그인/회원가입 입력을 받고,
// API 요청을 보낸 뒤,
// 로그인 성공하면 App.tsx에게 "로그인 성공했어"라고 알려주는 화면



export function AuthPage({ onLoginSuccess }: AuthPageProps) {
  // 같은 화면에서 로그인/회원가입 폼을 탭처럼 전환합니다.
  const [mode, setMode] = useState<"login" | "signup">("login");

  // 폼 입력값을 React state로 관리합니다.
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");

  // API 요청 중에는 버튼을 비활성화해서 중복 제출을 막습니다.
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isLoginMode = mode === "login";

const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
  event.preventDefault();

  // 로그인과 회원가입 모두 이메일/비밀번호는 필수입니다.
  if (!email.trim() || !password.trim()) {
    alert("이메일과 비밀번호를 입력해주세요.");
    return;
  }

  // 회원가입 모드일 때만 닉네임을 추가로 검사합니다.
  if (!isLoginMode && !nickname.trim()) {
    alert("닉네임을 입력해주세요.");
    return;
  }

  try {
    setIsSubmitting(true);

    if (isLoginMode) {
      // 로그인 성공 시 JWT를 브라우저에 저장하고 App.tsx에 성공을 알립니다.
      const tokenResponse = await login({
        email: email.trim(),
        password,
      });

      localStorage.setItem("access_token", tokenResponse.access_token);
      onLoginSuccess();
      return;
    }

    // 회원가입은 계정 생성만 하고, 사용자가 다시 로그인하도록 로그인 탭으로 돌립니다.
    await signup({
      email: email.trim(),
      password,
      nickname: nickname.trim(),
    });

    alert("회원가입이 완료되었습니다. 로그인해주세요.");

    setMode("login");
    setEmail("");
    setPassword("");
    setNickname("");
  } catch (error) {
    console.error(error);

    // 로그인 실패와 회원가입 실패는 사용자에게 서로 다른 메시지를 보여줍니다.
    if (isLoginMode) {
      alert("로그인에 실패했습니다. 이메일 또는 비밀번호를 확인해주세요.");
    } else {
      alert("회원가입에 실패했습니다. 이미 사용 중인 이메일일 수 있습니다.");
    }
  } finally {
    setIsSubmitting(false);
  }
};

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="auth-logo">T</div>
          <div>
            <h1>TeamLog</h1>
            <p>캘린더 기반 회의/회고 협업툴</p>
          </div>
        </div>

        <div className="auth-tabs">
          <button
            type="button"
            className={isLoginMode ? "active" : ""}
            onClick={() => setMode("login")}
          >
            로그인
          </button>

          <button
            type="button"
            className={!isLoginMode ? "active" : ""}
            onClick={() => setMode("signup")}
          >
            회원가입
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>이메일</span>
            <input
              type="email"
              value={email}
              placeholder="example@email.com"
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label>
            <span>비밀번호</span>
            <input
              type="password"
              value={password}
              placeholder="비밀번호"
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {!isLoginMode && (
            <label>
              <span>닉네임</span>
              <input
                value={nickname}
                placeholder="닉네임"
                onChange={(event) => setNickname(event.target.value)}
              />
            </label>
          )}

          <button
            className="auth-submit-button"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "처리 중..."
              : isLoginMode
              ? "로그인"
              : "회원가입"}
          </button>
        </form>

        <p className="auth-help">
          로그인 성공 시 JWT 토큰이 브라우저에 저장되고, 이후 캘린더 API
          요청에 자동으로 포함됩니다.
        </p>
      </section>
    </main>
  );
}
