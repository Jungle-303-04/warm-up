import { useState } from "react";

const posts = [
  {
    id: 1,
    date: "Mar 16, 2026",
    fontName: "Zodiak",
    title: "Boost your conversion rate",
    nickname: "Jisoo Kim",
    previewText: "hello world",
  },
  {
    id: 2,
    date: "Mar 16, 2026",
    fontName: "어그로체",
    title: "Boost your conversion rate",
    nickname: "Min Park",
    previewText: "hello world",
  },
  {
    id: 3,
    date: "Mar 16, 2026",
    fontName: "Zodiak",
    title: "my board",
    nickname: "Yuna Lee",
    previewText: "hello world",
  },
];

function Board() {
  const [searchQuery, setSearchQuery] = useState("");
  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredPosts = posts.filter((post) => {
    if (!normalizedQuery) {
      return true;
    }

    return [post.title, post.fontName].some((value) =>
      value.toLowerCase().includes(normalizedQuery),
    );
  });

  return (
    <main className="p-6">
      <div className="flex justify-center pt-10">
        <label className="relative w-full max-w-[360px]">
          <span className="sr-only">게시글 검색</span>
          <svg
            aria-hidden="true"
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            viewBox="0 0 24 24"
          >
            <path
              d="m21 21-4.35-4.35m1.35-5.15a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0Z"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <input
            className="h-10 w-full rounded-md border border-gray-300 pl-10 pr-9 text-sm outline-none transition-colors placeholder:text-gray-300 focus:border-black"
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="제목, 폰트 이름 등 검색어를 입력하세요"
            type="text"
            value={searchQuery}
          />
          {searchQuery ? (
            <button
              aria-label="검색어 지우기"
              className="absolute right-3 top-1/2 flex h-4 w-4 -translate-y-1/2 cursor-pointer items-center justify-center text-black transition-opacity hover:opacity-60"
              onClick={() => setSearchQuery("")}
              type="button"
            >
              <svg
                aria-hidden="true"
                className="h-3 w-3"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                viewBox="0 0 12 12"
              >
                <path
                  d="M3 3l6 6M9 3 3 9"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          ) : null}
        </label>
      </div>

      <section className="mt-20 grid grid-cols-3 gap-6">
        {filteredPosts.map((post) => (
          <article
            key={post.id}
            className="min-w-0 cursor-pointer rounded-md p-4 shadow-[0_0_12px_rgba(15,23,42,0.06)] transition duration-200 ease-out hover:-translate-y-1 hover:shadow-[0_0_18px_rgba(15,23,42,0.1)]"
          >
            <div className="flex items-center gap-2 text-xs text-[#d4d4d4]">
              <time dateTime="2026-03-16">{post.date}</time>
              <span aria-hidden="true">•</span>
              <span className="rounded-full bg-[#d4d4d4] px-2 py-0.5 text-[10px] font-medium text-black">
                {post.fontName}
              </span>
            </div>

            <h2 className="mt-3 text-sm font-bold leading-tight text-black">
              {post.title}
            </h2>

            <div className="mt-3 h-24 overflow-hidden rounded-md border border-gray-200 px-4 py-3">
              <p className="font-['Zodiak'] text-[22px] font-extrabold italic leading-tight text-black">
                {post.previewText}
              </p>
            </div>

            <p className="mt-3 text-xs font-semibold text-black">
              {post.nickname}
            </p>
          </article>
        ))}
      </section>
    </main>
  );
}

export default Board;
