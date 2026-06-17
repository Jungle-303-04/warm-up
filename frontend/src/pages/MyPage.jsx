import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { getMyBoard } from "../api/auth";
import { ArchiveBoxIcon, HandRaisedIcon } from "../components/icons";

function createMyPostItem(post) {
  return {
    fontName: post.font?.name ?? "Unknown",
    id: post.id,
    title: post.title,
  };
}

function createUsedFontItem(fontGroup) {
  return {
    fontName: fontGroup.font_name,
    posts: fontGroup.posts ?? [],
  };
}

function MyPage({ onLogout, user }) {
  const nickname = user?.nickname ?? "guest";
  const [myPosts, setMyPosts] = useState([]);
  const [usedFonts, setUsedFonts] = useState([]);
  const [isLoadingMyBoard, setIsLoadingMyBoard] = useState(true);
  const [myBoardErrorMessage, setMyBoardErrorMessage] = useState("");
  const [logoutMessage, setLogoutMessage] = useState("");
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const hasMyPosts = myPosts.length > 0;
  const hasUsedFonts = usedFonts.length > 0;

  useEffect(() => {
    let shouldUpdateState = true;

    const loadMyBoard = async () => {
      setIsLoadingMyBoard(true);
      setMyBoardErrorMessage("");

      try {
        const myBoardResponse = await getMyBoard();

        if (!shouldUpdateState) {
          return;
        }

        setMyPosts((myBoardResponse.posts ?? []).map(createMyPostItem));
        setUsedFonts(
          (myBoardResponse.used_fonts ?? []).map(createUsedFontItem),
        );
      } catch (error) {
        if (shouldUpdateState) {
          if (error.status === 401) {
            await onLogout({ shouldRequestLogout: false });
            return;
          }

          setMyBoardErrorMessage("정보를 불러오지 못했어요.");
        }
      } finally {
        if (shouldUpdateState) {
          setIsLoadingMyBoard(false);
        }
      }
    };

    loadMyBoard();

    return () => {
      shouldUpdateState = false;
    };
  }, [onLogout]);

  const handleLogoutClick = async () => {
    setLogoutMessage("");
    setIsLoggingOut(true);

    try {
      await onLogout();
    } catch (error) {
      setLogoutMessage(error.message);
      setIsLoggingOut(false);
    }
  };

  return (
    <main className="flex min-h-[calc(100vh-96px)] flex-col p-6">
      <section className="mx-auto flex w-full max-w-[380px] flex-col items-center pt-[120px]">
        <span className="animate-tilt-once font-['Zodiak'] text-[35pt] font-extrabold italic leading-none text-black">
          f
        </span>

        <p className="mt-4 flex min-h-6 items-center justify-center gap-2 text-center text-base font-normal text-black">
          <span>안녕하세요 {nickname} 님</span>
          <HandRaisedIcon className="h-5 w-5" />
        </p>

        <button
          className="mt-2 cursor-pointer !text-sm leading-none text-[#d4d4d4] transition-colors hover:text-black disabled:cursor-not-allowed disabled:hover:text-[#d4d4d4]"
          disabled={isLoggingOut}
          onClick={handleLogoutClick}
          type="button"
        >
          {isLoggingOut ? "로그아웃 중..." : "로그아웃"}
        </button>
        <p className="mt-2 min-h-5 text-center text-sm text-neutral-600">
          {logoutMessage}
        </p>

        <div className="mt-5 w-full overflow-hidden rounded-md border border-gray-300">
          <details className="group border-b border-gray-300">
            <summary className="flex h-10 cursor-pointer list-none items-center justify-between px-4 text-sm text-black transition-colors hover:bg-[#F8F9FA] group-open:bg-[#F8F9FA]">
              <span className="flex items-center gap-2 font-bold">
                <span className="flex w-4 items-center justify-center">
                  <ArchiveBoxIcon className="h-4 w-4" />
                </span>
                내가 등록한 게시물
              </span>
              <span className="text-xs text-[#d4d4d4] group-open:rotate-90">
                &gt;
              </span>
            </summary>
            <ul className="thin-transparent-scrollbar max-h-[360px] overflow-y-auto border-t border-gray-200 px-4 py-3">
              {isLoadingMyBoard ? (
                <li className="py-1.5 text-sm text-[#d4d4d4]">
                  게시물을 불러오는 중...
                </li>
              ) : hasMyPosts ? (
                myPosts.map((post) => (
                  <li key={post.id}>
                    <Link
                      className="flex items-center gap-2 py-1.5 text-sm text-black no-underline transition-colors hover:text-[#d4d4d4]"
                      to={`/posts/${post.id}`}
                    >
                      <span className="h-1 w-1 shrink-0 rounded-full bg-[#d4d4d4]" />
                      {post.title}
                    </Link>
                  </li>
                ))
              ) : (
                <li className="py-1.5 text-sm text-[#d4d4d4]">
                  아직 등록한 게시물이 없어요.
                </li>
              )}
            </ul>
          </details>

          <details className="group">
            <summary className="flex h-10 cursor-pointer list-none items-center justify-between px-4 text-sm text-black transition-colors hover:bg-[#F8F9FA] group-open:bg-[#F8F9FA]">
              <span className="flex items-center gap-2 font-bold">
                <span className="flex w-4 items-center justify-center">
                  <span className="font-['Zodiak'] text-[17px] font-extrabold italic leading-none text-black">
                    f
                  </span>
                </span>
                내가 사용한 폰트
              </span>
              <span className="text-xs text-[#d4d4d4] group-open:rotate-90">
                &gt;
              </span>
            </summary>
            <ul className="thin-transparent-scrollbar max-h-[320px] overflow-y-auto border-t border-gray-200 px-4 py-3">
              {isLoadingMyBoard ? (
                <li className="py-1.5 text-sm text-[#d4d4d4]">
                  폰트 기록을 불러오는 중...
                </li>
              ) : hasUsedFonts ? (
                usedFonts.map((fontGroup) => (
                  <li className="py-1.5 text-sm text-black" key={fontGroup.fontName}>
                    <p className="font-semibold">
                      {fontGroup.fontName}
                      <span className="ml-2 text-xs font-normal text-[#d4d4d4]">
                        {fontGroup.posts.length}
                      </span>
                    </p>
                    <ul className="mt-1">
                      {fontGroup.posts.map((post) => (
                        <li key={post.id}>
                          <Link
                            className="flex items-center gap-2 py-1 text-sm text-black no-underline transition-colors hover:text-[#d4d4d4]"
                            to={`/posts/${post.id}`}
                          >
                            <span className="h-1 w-1 shrink-0 rounded-full bg-[#d4d4d4]" />
                            {post.title}
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </li>
                ))
              ) : (
                <li className="py-1.5 text-sm text-[#d4d4d4]">
                  아직 사용한 폰트가 없어요.
                </li>
              )}
            </ul>
          </details>
        </div>
        <p className="mt-2 min-h-5 text-center text-sm text-[#d4d4d4]">
          {myBoardErrorMessage}
        </p>
      </section>
    </main>
  );
}

export default MyPage;
