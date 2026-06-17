import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

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
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleNicknameChange = (event) => {
    setNickname(event.target.value);
  };

  const handlePasswordChange = (event) => {
    setPassword(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    try {
      await onSubmit({ nickname, password });
    } catch (error) {
      setErrorMessage(error.message);
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
              className="h-10 w-full border-b border-gray-300 px-4 text-sm outline-none transition-colors placeholder:text-gray-300 focus:border-black"
              onChange={handleNicknameChange}
              placeholder="닉네임을 입력하세요"
              type="text"
              value={nickname}
            />
            <input
              className="h-10 w-full border-b border-transparent px-4 text-sm outline-none transition-colors placeholder:text-gray-300 focus:border-black"
              onChange={handlePasswordChange}
              placeholder="패스워드를 입력하세요"
              type="password"
              value={password}
            />
          </div>

          {errorMessage && (
            <p className="mt-3 text-sm text-red-500">{errorMessage}</p>
          )}

          <button
            className="mt-10 h-10 w-full cursor-pointer rounded-md border border-gray-300 text-sm font-normal text-black transition-colors hover:bg-black hover:text-white disabled:cursor-not-allowed disabled:text-gray-300 disabled:hover:bg-white disabled:hover:text-gray-300"
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
