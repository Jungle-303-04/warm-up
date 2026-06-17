import { Link } from "react-router-dom";
import { ArchiveBoxIcon } from "../components/icons";

const myPosts = [
  {
    fontName: "Zodiak",
    id: 1,
    title: "Boost your conversion rate",
  },
  {
    fontName: "Zodiak",
    id: 3,
    title: "my board",
  },
  {
    fontName: "Pretendard",
    id: 8,
    title: "읽기 쉬운 본문 조합",
  },
];

const usedFonts = [
  {
    fontName: "Zodiak",
    posts: [
      {
        id: 1,
        title: "Boost your conversion rate",
      },
      {
        id: 3,
        title: "my board",
      },
    ],
  },
  {
    fontName: "Pretendard",
    posts: [
      {
        id: 8,
        title: "읽기 쉬운 본문 조합",
      },
    ],
  },
];

function MyPage({ user }) {
  const nickname = user?.nickname ?? "guest";

  return (
    <main className="flex min-h-[calc(100vh-96px)] flex-col p-6">
      <section className="mx-auto flex w-full max-w-[380px] flex-col items-center pt-[120px]">
        <span className="animate-tilt-once font-['Zodiak'] text-[35pt] font-extrabold italic leading-none text-black">
          f
        </span>

        <p className="mt-4 min-h-6 text-center text-base font-normal text-black">
          안녕하세요 {nickname} 님
        </p>

        <button
          className="mt-2 cursor-pointer !text-sm leading-none text-[#d4d4d4] transition-colors hover:text-black"
          type="button"
        >
          로그아웃
        </button>

        <div className="mt-10 w-full overflow-hidden rounded-md border border-gray-300">
          <details className="group border-b border-gray-300">
            <summary className="flex h-10 cursor-pointer list-none items-center justify-between px-4 text-sm text-black transition-colors hover:bg-[#F8F9FA]">
              <span className="flex items-center gap-2">
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
              {myPosts.map((post) => (
                <li key={post.id}>
                  <Link
                    className="flex items-center gap-2 py-1.5 text-sm text-black no-underline transition-colors hover:text-[#d4d4d4]"
                    to={`/posts/${post.id}`}
                  >
                    <span className="h-1 w-1 shrink-0 rounded-full bg-[#d4d4d4]" />
                    {post.title}
                  </Link>
                </li>
              ))}
            </ul>
          </details>

          <details className="group">
            <summary className="flex h-10 cursor-pointer list-none items-center justify-between px-4 text-sm text-black transition-colors hover:bg-[#F8F9FA]">
              <span className="flex items-center gap-2">
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
            <ul className="thin-transparent-scrollbar max-h-[540px] overflow-y-auto border-t border-gray-200 px-4 py-3">
              {usedFonts.map((fontGroup) => (
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
              ))}
            </ul>
          </details>
        </div>
      </section>

    </main>
  );
}

export default MyPage;
