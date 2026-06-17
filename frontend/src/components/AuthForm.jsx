import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { EyeIcon, EyeSlashIcon } from "./icons";

function TypingText({ text }) {
  const [typedText, setTypedText] = useState("");

  useEffect(() => {
    let typingTimer;
    let currentIndex = 0;

    typingTimer = setInterval(() => {
      currentIndex += 1;
      setTypedText(text.slice(0, currentIndex));

      if (currentIndex >= text.length) {
        clearInterval(typingTimer);
      }
    }, 80);

    return () => {
      clearInterval(typingTimer);
    };
  }, [text]);

  return (
    <>
      {typedText}
      <span className="ml-0.5 inline-block h-4 w-px translate-y-0.5 animate-pulse bg-black" />
    </>
  );
}

function AuthForm({ buttonLabel, description, linkLabel, linkTo, onSubmit }) {
  const [nickname, setNickname] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [errorField, setErrorField] = useState("");
  const [errorAnimationKey, setErrorAnimationKey] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const [focusedField, setFocusedField] = useState("");

  const getFocusedFieldGuideMessage = () => {
    if (focusedField === "nickname") {
      return "닉네임은 20자 이내로 입력해주세요.";
    }

    if (focusedField === "password") {
      return "영문 대소문자를 구분, 숫자를 포함해 8~20자로 입력해주세요.";
    }

    return "";
  };

  const guideMessage = getFocusedFieldGuideMessage();
  const helperMessage = errorMessage || guideMessage;
  const helperMessageColor = errorMessage ? "text-black" : "text-[#d4d4d4]";
  const helperMessageAnimation = errorMessage ? "animate-shake-error" : "";

  const showAuthError = (message, field) => {
    setErrorMessage(message);
    setErrorField(field);
    setErrorAnimationKey((currentKey) => currentKey + 1);
  };

  const validateAuthForm = () => {
    const passwordPattern = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,20}$/;

    if (!nickname.trim()) {
      return {
        field: "nickname",
        message: "닉네임을 입력해주세요.",
      };
    }

    if (nickname.trim().length > 20) {
      return {
        field: "nickname",
        message: "닉네임은 20자 이내로 입력해주세요.",
      };
    }

    if (!password.trim()) {
      return {
        field: "password",
        message: "비밀번호를 입력해주세요.",
      };
    }

    if (!passwordPattern.test(password)) {
      return {
        field: "password",
        message: "영문 대소문자를 구분, 숫자를 포함해 8~20자로 입력해주세요.",
      };
    }

    return null;
  };

  const handleNicknameChange = (event) => {
    setNickname(event.target.value);
    setErrorMessage("");
    setErrorField("");
  };

  const handlePasswordChange = (event) => {
    setPassword(event.target.value);
    setErrorMessage("");
    setErrorField("");
  };

  const handleTogglePasswordVisible = () => {
    setIsPasswordVisible((currentValue) => !currentValue);
  };

  const handleNicknameFocus = () => {
    setFocusedField("nickname");
  };

  const handlePasswordFocus = () => {
    setFocusedField("password");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage("");
    setErrorField("");

    const validationError = validateAuthForm();

    if (validationError) {
      showAuthError(validationError.message, validationError.field);
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({ nickname, password });
    } catch (error) {
      showAuthError(error.message, "form");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-[620px] items-center justify-center p-6">
      <section className="flex w-full max-w-[380px] flex-col items-center">
        <span className="font-['Zodiak'] text-[35pt] font-extrabold italic leading-none text-black">
          f
        </span>

        <p className="mt-4 min-h-6 text-center text-base font-normal text-black">
          <TypingText key={description} text={description} />
        </p>

        <form className="mt-10 w-full" onSubmit={handleSubmit}>
          <div className="overflow-hidden rounded-md border border-gray-300">
            <input
              className={[
                "h-10 w-full border-b px-4 text-base outline-none transition-colors placeholder:text-base placeholder:text-gray-300 focus:border-black",
                errorField === "nickname"
                  ? "border-neutral-500"
                  : "border-gray-300",
              ].join(" ")}
              onChange={handleNicknameChange}
              onFocus={handleNicknameFocus}
              placeholder="닉네임을 입력하세요"
              type="text"
              value={nickname}
            />
            <div className="relative">
              <input
                className={[
                  "h-10 w-full border-b px-4 pr-12 text-base outline-none transition-colors placeholder:text-base placeholder:text-gray-300 focus:border-black",
                  errorField === "password"
                    ? "border-neutral-500"
                    : "border-transparent",
                ].join(" ")}
                onChange={handlePasswordChange}
                onFocus={handlePasswordFocus}
                placeholder="비밀번호를 입력하세요"
                type={isPasswordVisible ? "text" : "password"}
                value={password}
              />
              <button
                aria-label={
                  isPasswordVisible ? "비밀번호 숨기기" : "비밀번호 보기"
                }
                className="absolute right-3 top-1/2 flex h-5 w-5 -translate-y-1/2 cursor-pointer items-center justify-center text-black transition-colors hover:text-[#d4d4d4]"
                onClick={handleTogglePasswordVisible}
                type="button"
              >
                {isPasswordVisible ? (
                  <EyeIcon className="h-4 w-4" />
                ) : (
                  <EyeSlashIcon className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          <p
            className={[
              "mt-3 min-h-5 text-right text-sm",
              helperMessageColor,
              helperMessageAnimation,
            ].join(" ")}
            key={errorAnimationKey}
          >
            {helperMessage}
          </p>

          <button
            className="mt-6 h-10 w-full cursor-pointer rounded-md border border-gray-300 text-sm font-normal text-black transition-colors hover:bg-black hover:text-white disabled:cursor-not-allowed disabled:text-gray-300 disabled:hover:bg-white disabled:hover:text-gray-300"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "처리 중..." : buttonLabel}
          </button>
        </form>

        <Link
          className="mt-3 self-end text-xs text-gray-400 no-underline transition-colors hover:text-black"
          to={linkTo}
        >
          {linkLabel}
        </Link>
      </section>
    </main>
  );
}

export default AuthForm;
