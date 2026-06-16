import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import FontInfoPopover from "../components/FontInfoPopover";

const postDetail = {
  author: "font_maker",
  comments: [
    {
      content:
        "문장 분위기랑 폰트가 잘 맞아요. 제목용으로 쓰면 더 선명하게 보일 것 같아요.",
      date: "2026.03.16",
      id: 1,
      nickname: "글꼴탐험가",
      time: "10:24",
    },
  ],
  content:
    "Once upon a time, in a quiet village beside a silver forest, a small lantern learned how to glow. Every night it listened to the wind, gathered stories from the stars, and lit a narrow path for children who dreamed of finding a hidden garden beyond the hill. The garden was said to bloom only for those who carried kind words in their pockets and brave thoughts in their hearts.",
  date: "Mar 16, 2026",
  font: {
    downloadUrl: "https://www.fontshare.com/fonts/zodiak",
    license: "OFL",
    name: "Zodiak",
    notice: "브랜드 적용 전 라이선스 원문을 한 번 더 확인하세요.",
    reason:
      "입력한 문장은 짧지만 감정의 방향이 분명하고, 말의 끝에 힘이 남는 구조예요. 그래서 부드럽기보다는 인상이 또렷하게 남는 세리프 계열 폰트를 추천했어요.",
    source: "Fontshare",
    tags: ["영문", "세리프", "강조"],
    usage: "인쇄, 웹사이트, 영상, BI/CI",
  },
  time: "10:24",
  title: "Boost your conversion rate",
};

function PostDetail() {
  const navigate = useNavigate();
  const { postId } = useParams();
  const [comments, setComments] = useState(postDetail.comments);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const handleDeleteComment = (commentId) => {
    setComments((currentComments) =>
      currentComments.filter((comment) => comment.id !== commentId),
    );
  };

  const handleDeletePost = () => {
    setIsDeleteDialogOpen(false);
    navigate("/");
  };

  return (
    <main className="p-6">
      <section className="mx-auto w-full max-w-[720px] pt-8 pb-12">
        <button
          aria-label="이전으로"
          className="mb-16 cursor-pointer text-2xl leading-none text-black transition-colors hover:text-[#d4d4d4]"
          onClick={() => navigate(-1)}
          type="button"
        >
          &lt;-
        </button>

        <div className="grid min-h-[132px] grid-cols-[1fr_auto] items-start gap-5 overflow-visible pr-2">
          <div className="ml-auto flex h-full w-2/3 flex-col">
            <div className="flex min-h-7 flex-wrap items-center gap-2">
              <FontInfoPopover font={postDetail.font} />
              {postDetail.font.tags.map((tag) => (
                <span
                  className="rounded-full border border-gray-200 bg-white px-2 py-0.5 text-[10px] font-medium text-black"
                  key={tag}
                >
                  {tag}
                </span>
              ))}
            </div>

            <div className="mt-3 flex min-h-16 items-center overflow-visible pr-1">
              <p className="thin-transparent-scrollbar max-h-16 overflow-y-auto text-left text-sm leading-relaxed text-black">
                {postDetail.font.reason}
              </p>
            </div>
          </div>

          <div className="flex h-full flex-col">
            <div className="min-h-7" />
            <div className="mt-3 flex min-h-16 items-center overflow-visible">
              <span className="shrink-0 font-['Zodiak'] text-[28pt] font-extrabold italic leading-none text-black">
                f
              </span>
            </div>
          </div>
        </div>

        <article className="mt-20">
          <time className="text-xs text-[#d4d4d4]" dateTime="2026-03-16T10:24">
            {postDetail.date} · {postDetail.time}
          </time>
          <h1 className="mt-4 text-xl font-bold leading-tight text-black">
            {postDetail.title}
          </h1>
          <p className="mt-7 font-['Zodiak'] text-[28px] font-extrabold italic leading-snug text-black">
            {postDetail.content}
          </p>

          <div className="mt-8 flex items-center justify-between">
            <p className="text-sm font-semibold text-black">
              {postDetail.author}
            </p>
            <div className="flex items-center gap-4">
              <button
                className="cursor-pointer text-xs text-black transition-colors hover:text-[#d4d4d4]"
                type="button"
              >
                수정
              </button>
              <button
                className="cursor-pointer text-xs text-black transition-colors hover:text-[#d4d4d4]"
                onClick={() => setIsDeleteDialogOpen(true)}
                type="button"
              >
                삭제
              </button>
            </div>
          </div>
        </article>

        <section className="mt-5 border-t border-black pt-4">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-black">comment</h2>
            <span className="text-sm text-black">{comments.length}</span>
          </div>

          <div className="mt-3 flex items-center gap-3">
            <textarea
              className="h-20 flex-1 resize-none rounded-md border border-gray-300 px-4 py-3 text-sm leading-relaxed outline-none transition-colors placeholder:text-xs placeholder:text-gray-300 focus:border-black"
              placeholder="댓글을 입력하세요."
            />
            <button
              className="cursor-pointer px-2 text-xs text-black transition-colors hover:text-[#d4d4d4]"
              type="button"
            >
              등록
            </button>
          </div>

          {comments.length > 0 ? (
            <ul className="mt-8 space-y-5">
              {comments.map((comment) => (
              <li
                className="grid grid-cols-[120px_1fr_auto_auto] items-start gap-4 text-xs"
                key={comment.id}
              >
                <p className="text-sm font-extrabold text-black">
                  {comment.nickname}
                </p>
                <p className="leading-relaxed text-black">{comment.content}</p>
                <time className="text-[#d4d4d4]" dateTime="2026-03-16T10:24">
                  {comment.date} · {comment.time}
                </time>
                <button
                  aria-label="댓글 삭제"
                  className="cursor-pointer text-black transition-opacity hover:opacity-50"
                  onClick={() => handleDeleteComment(comment.id)}
                  type="button"
                >
                  x
                </button>
              </li>
              ))}
            </ul>
          ) : (
            <p className="mt-8 text-center text-sm text-[#9ca3af]">
              첫 댓글을 달아보세요!
            </p>
          )}
        </section>

        <div className="mt-16 flex justify-end">
          <Link
            className="rounded-md border border-gray-300 px-5 py-2 text-sm text-black no-underline transition-colors hover:bg-black hover:text-white"
            to="/"
          >
            목록으로
          </Link>
        </div>

        <p className="sr-only">현재 게시글 ID는 {postId}입니다.</p>
      </section>

      {isDeleteDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/10 px-6 backdrop-blur-[1px]">
          <div
            aria-modal="true"
            className="w-full max-w-[320px] rounded-md border border-gray-200 bg-white p-5 shadow-[0_12px_32px_rgba(15,23,42,0.14)]"
            role="dialog"
          >
            <p className="text-base font-semibold text-black">
              게시물을 삭제할까요?
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button
                className="cursor-pointer px-2 py-1 text-sm text-black transition-colors hover:text-[#d4d4d4]"
                onClick={() => setIsDeleteDialogOpen(false)}
                type="button"
              >
                취소
              </button>
              <button
                className="cursor-pointer rounded-md border border-gray-300 px-4 py-1.5 text-sm text-black transition-colors hover:bg-black hover:text-white"
                onClick={handleDeletePost}
                type="button"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}

export default PostDetail;
