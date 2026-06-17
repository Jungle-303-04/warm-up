import { Link, useLocation } from "react-router-dom";
import { FingerPrintIcon } from "./icons";

function Header({ onAccountClick, user }) {
  const location = useLocation();
  const accountLabel = user?.nickname ?? "로그인";
  const isLoginPage = location.pathname === "/login";
  const isSignupPage = location.pathname === "/signup";
  const isMyPage = location.pathname === "/mypage";
  const isPostPage = location.pathname.startsWith("/posts/");
  const isPostEditPage = location.pathname.endsWith("/edit");
  const postPageLabel = isPostEditPage ? "글수정" : "글보기";
  const defaultNavItems = [
    { label: "Board", path: "/" },
    {
      isActive: isPostPage || location.pathname === "/write",
      label: isPostPage ? postPageLabel : "글쓰기",
      path: isPostPage ? location.pathname : user ? "/write" : "/login",
    },
  ];
  const navItems =
    isLoginPage || isSignupPage
      ? [
          {
            isActive: true,
            label: isLoginPage ? "Login" : "Signup",
            path: location.pathname,
          },
        ]
      : isMyPage
        ? [
            ...defaultNavItems,
            {
              isActive: true,
              label: "내정보",
              path: "/mypage",
            },
          ]
        : defaultNavItems;

  return (
    <header className="relative rounded-t-md bg-white px-6 py-5 shadow-[0_4px_4px_-4px_rgba(15,23,42,0.14)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-7">
          <Link
            className="font-['Zodiak'] text-[40pt] font-extrabold italic leading-none text-black no-underline [text-shadow:0_2px_4px_rgba(0,0,0,0.18)]"
            to="/"
          >
            f
          </Link>
          <nav className="flex items-center gap-7">
            {navItems.map((item) => {
              const isActive = item.isActive ?? location.pathname === item.path;

              return (
                <Link
                  className={[
                    "text-[30px] font-normal leading-none no-underline transition-colors",
                    isActive
                      ? "text-black [text-shadow:0_1px_3px_rgba(0,0,0,0.14)]"
                      : "text-[#d4d4d4] hover:text-black",
                  ].join(" ")}
                  key={item.path}
                  to={item.path}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-5">
          <button
            className="flex cursor-pointer items-center gap-1.5 text-[10px] font-semibold text-black transition-colors hover:text-[#d4d4d4]"
            onClick={onAccountClick}
            type="button"
          >
            {user ? <FingerPrintIcon className="h-4 w-4" /> : null}
            {accountLabel}
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;
