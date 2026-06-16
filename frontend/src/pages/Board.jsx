import { Link } from "react-router-dom";
import { useState } from "react";

const posts = [
  {
    id: 1,
    date: "Mar 16, 2026",
    fontName: "Zodiak",
    title: "Boost your conversion rate",
    nickname: "Jisoo Kim",
    previewText: "hello world",
    previewFontClass: "font-['Zodiak'] font-extrabold italic",
  },
  {
    id: 2,
    date: "Mar 16, 2026",
    fontName: "어그로체",
    title: "Boost your conversion rate",
    nickname: "Min Park",
    previewText: "세상에 이런 폰트가 나오다니",
    previewFontClass: "font-['Pretendard'] font-normal",
  },
  {
    id: 3,
    date: "Mar 16, 2026",
    fontName: "Zodiak",
    title: "my board",
    nickname: "Yuna Lee",
    previewText: "hello world",
    previewFontClass: "font-['Zodiak'] font-extrabold italic",
  },
  {
    id: 4,
    date: "Mar 17, 2026",
    fontName: "Pretendard",
    title: "Simple notes for daily writing",
    nickname: "font_maker",
    previewText: "차분한 문장에는 담백한 폰트가 어울려요",
    previewFontClass: "font-['Pretendard'] font-normal",
  },
  {
    id: 5,
    date: "Mar 17, 2026",
    fontName: "Zodiak",
    title: "A bright title for a small story",
    nickname: "문장수집가",
    previewText: "little story",
    previewFontClass: "font-['Zodiak'] font-extrabold italic",
  },
  {
    id: 6,
    date: "Mar 18, 2026",
    fontName: "어그로체",
    title: "브랜드 문구 테스트",
    nickname: "type_note",
    previewText: "강한 첫인상을 남기는 문장",
    previewFontClass: "font-['Pretendard'] font-normal",
  },
  {
    id: 7,
    date: "Mar 18, 2026",
    fontName: "Zodiak",
    title: "Elegant font pairing",
    nickname: "Yuna Lee",
    previewText: "soft elegance",
    previewFontClass: "font-['Zodiak'] font-extrabold italic",
  },
  {
    id: 8,
    date: "Mar 19, 2026",
    fontName: "Pretendard",
    title: "읽기 쉬운 본문 조합",
    nickname: "글꼴탐험가",
    previewText: "본문은 읽는 흐름이 가장 중요해요",
    previewFontClass: "font-['Pretendard'] font-normal",
  },
  {
    id: 9,
    date: "Mar 19, 2026",
    fontName: "Zodiak",
    title: "Serif mood board",
    nickname: "Min Park",
    previewText: "classic mood",
    previewFontClass: "font-['Zodiak'] font-extrabold italic",
  },
  {
    id: 10,
    date: "Mar 20, 2026",
    fontName: "Pretendard",
    title: "검색 페이지 확인용",
    nickname: "Jisoo Kim",
    previewText: "검색 결과가 다음 페이지에도 이어져요",
    previewFontClass: "font-['Pretendard'] font-normal",
  },
  {
    id: 11,
    date: "Mar 20, 2026",
    fontName: "Zodiak",
    title: "Long preview sample",
    nickname: "type_note",
    previewText: "forever and ever",
    previewFontClass: "font-['Zodiak'] font-extrabold italic",
  },
  {
    id: 12,
    date: "Mar 21, 2026",
    fontName: "어그로체",
    title: "태그 필터 고민중",
    nickname: "문장수집가",
    previewText: "태그는 나중에 필터로 확장할 수 있어요",
    previewFontClass: "font-['Pretendard'] font-normal",
  },
];

const postsPerPage = 9;

function Board() {
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredPosts = posts.filter((post) => {
    if (!normalizedQuery) {
      return true;
    }

    return [post.title, post.fontName].some((value) =>
      value.toLowerCase().includes(normalizedQuery),
    );
  });
  const totalPages = Math.max(1, Math.ceil(filteredPosts.length / postsPerPage));
  const firstPostIndex = (currentPage - 1) * postsPerPage;
  const visiblePosts = filteredPosts.slice(
    firstPostIndex,
    firstPostIndex + postsPerPage,
  );
  const isFirstPage = currentPage === 1;
  const isLastPage = currentPage === totalPages;
  const pageNumbers = Array.from(
    { length: totalPages },
    (_, pageIndex) => pageIndex + 1,
  );

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
    setCurrentPage(1);
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setCurrentPage(1);
  };

  const handlePreviousPage = () => {
    if (!isFirstPage) {
      setCurrentPage((pageNumber) => pageNumber - 1);
    }
  };

  const handleNextPage = () => {
    if (!isLastPage) {
      setCurrentPage((pageNumber) => pageNumber + 1);
    }
  };

  const handleSelectPage = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

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
            onChange={handleSearchChange}
            placeholder="제목, 폰트 이름 등 검색어를 입력하세요"
            type="text"
            value={searchQuery}
          />
          {searchQuery ? (
            <button
              aria-label="검색어 지우기"
              className="absolute right-3 top-1/2 flex h-4 w-4 -translate-y-1/2 cursor-pointer items-center justify-center text-black transition-opacity hover:opacity-60"
              onClick={handleClearSearch}
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

      <section className="mt-20 grid grid-cols-3 gap-x-6 gap-y-10">
        {visiblePosts.map((post) => (
          <article
            key={post.id}
            className="min-w-0 rounded-md shadow-[0_0_12px_rgba(15,23,42,0.06)] transition duration-200 ease-out hover:-translate-y-1 hover:shadow-[0_0_18px_rgba(15,23,42,0.1)]"
          >
            <Link
              className="block cursor-pointer p-4"
              to={`/posts/${post.id}`}
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
                <p
                  className={`${post.previewFontClass} text-[22px] leading-tight text-black`}
                >
                  {post.previewText}
                </p>
              </div>

              <p className="mt-3 text-xs font-semibold text-black">
                {post.nickname}
              </p>
            </Link>
          </article>
        ))}
      </section>

      <nav
        aria-label="게시글 페이지"
        className="mt-12 flex items-center justify-center gap-4"
      >
        <button
          className={[
            "text-sm transition-colors",
            isFirstPage
              ? "cursor-not-allowed text-[#d4d4d4]"
              : "cursor-pointer text-black hover:text-[#d4d4d4]",
          ].join(" ")}
          disabled={isFirstPage}
          onClick={handlePreviousPage}
          type="button"
        >
          이전
        </button>
        <div className="flex items-center gap-2">
          {pageNumbers.map((pageNumber) => {
            const isCurrentPage = pageNumber === currentPage;

            return (
              <button
                aria-current={isCurrentPage ? "page" : undefined}
                className={[
                  "h-8 min-w-8 rounded-md border px-2 text-sm transition-colors",
                  isCurrentPage
                    ? "cursor-default border-black bg-white text-black"
                    : "cursor-pointer border-transparent text-[#d4d4d4] hover:bg-[#F8F9FA] hover:text-black",
                ].join(" ")}
                disabled={isCurrentPage}
                key={pageNumber}
                onClick={() => handleSelectPage(pageNumber)}
                type="button"
              >
                {pageNumber}
              </button>
            );
          })}
        </div>
        <button
          className={[
            "text-sm transition-colors",
            isLastPage
              ? "cursor-not-allowed text-[#d4d4d4]"
              : "cursor-pointer text-black hover:text-[#d4d4d4]",
          ].join(" ")}
          disabled={isLastPage}
          onClick={handleNextPage}
          type="button"
        >
          다음
        </button>
      </nav>
    </main>
  );
}

export default Board;
