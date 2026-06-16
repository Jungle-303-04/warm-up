import { Link, useLocation } from "react-router-dom";

function Header({ onLoginClick, user }) {
  const location = useLocation();
  const accountLabel = user?.nickname ?? "로그인";
  const navLabel =
    location.pathname === "/login"
      ? "Sign in"
      : location.pathname === "/signup"
        ? "Sign up"
        : "Board";

  return (
    <header className="relative rounded-t-md bg-white px-6 py-5 shadow-[0_4px_4px_-4px_rgba(15,23,42,0.18)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-7">
          <Link
            className="font-['Zodiak'] text-[40pt] font-extrabold italic leading-none text-black no-underline [text-shadow:0_2px_4px_rgba(0,0,0,0.18)]"
            to="/"
          >
            f
          </Link>
          <span className="text-[30px] font-normal leading-none text-black">
            {navLabel}
          </span>
        </div>

        <div className="flex items-center gap-5">
          <button
            className="h-11 cursor-pointer rounded-md border border-gray-200 px-8 text-sm font-normal text-black transition-colors hover:bg-[#d4d4d4]"
            type="button"
          >
            글쓰기
          </button>
          <button
            className="cursor-pointer text-[10px] font-semibold text-black transition-colors hover:text-[#d4d4d4]"
            onClick={onLoginClick}
            type="button"
          >
            {accountLabel}
          </button>
        </div>
      </div>

      <span className="absolute bottom-0 left-[110px] h-px w-20 bg-gray-500" />
    </header>
  );
}

export default Header;
