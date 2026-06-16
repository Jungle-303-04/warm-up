import { Link, useLocation } from "react-router-dom";

function Header({ onLoginClick, user }) {
  const location = useLocation();
  const accountLabel = user?.nickname ?? "로그인";
  const isPostDetailPage = location.pathname.startsWith("/posts/");
  const navItems = [
    { label: "Board", path: "/" },
    {
      isActive: isPostDetailPage || location.pathname === "/write",
      label: isPostDetailPage ? "글보기" : "글쓰기",
      path: isPostDetailPage ? location.pathname : user ? "/write" : "/login",
    },
  ];

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
            className="cursor-pointer text-[10px] font-semibold text-black transition-colors hover:text-[#d4d4d4]"
            onClick={onLoginClick}
            type="button"
          >
            {accountLabel}
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;
