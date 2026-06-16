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

function AuthForm({ buttonLabel, description, linkLabel, linkTo }) {
  return (
    <main className="flex min-h-[620px] items-center justify-center p-6">
      <section className="flex w-full max-w-[380px] flex-col items-center">
        <span className="font-['Zodiak'] text-[35pt] font-extrabold italic leading-none text-black">
          f
        </span>

        <p className="mt-4 min-h-6 text-center text-base font-normal text-black">
          <TypingText key={description} text={description} />
        </p>

        <form className="mt-10 w-full">
          <div className="overflow-hidden rounded-md border border-gray-300">
            <input
              className="h-10 w-full border-b border-gray-300 px-4 text-sm outline-none transition-colors placeholder:text-gray-300 focus:border-black"
              placeholder="닉네임을 입력하세요"
              type="text"
            />
            <input
              className="h-10 w-full border-b border-transparent px-4 text-sm outline-none transition-colors placeholder:text-gray-300 focus:border-black"
              placeholder="패스워드를 입력하세요"
              type="password"
            />
          </div>

          <button
            className="mt-10 h-10 w-full cursor-pointer rounded-md border border-gray-300 text-sm font-normal text-black transition-colors hover:bg-black hover:text-white"
            type="button"
          >
            {buttonLabel}
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
