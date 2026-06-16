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
    fontName: "Zodiak",
    title: "Boost your conversion rate",
    nickname: "Min Park",
    previewText: "hello world",
  },
  {
    id: 3,
    date: "Mar 16, 2026",
    fontName: "Zodiak",
    title: "Boost your conversion rate",
    nickname: "Yuna Lee",
    previewText: "hello world",
  },
];

function Board() {
  return (
    <main className="p-6">
      <section className="grid grid-cols-3 gap-6">
        {posts.map((post) => (
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
