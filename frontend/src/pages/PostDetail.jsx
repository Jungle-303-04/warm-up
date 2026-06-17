import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  createComment,
  deleteComment,
  getComments,
} from "../api/comments";
import { deletePost, getPost } from "../api/posts";
import FontInfoPopover from "../components/FontInfoPopover";
import {
  ArrowLongLeftIcon,
  ChatBubbleLeftEllipsisIcon,
  XMarkIcon,
} from "../components/icons";

const fallbackFontReason =
  "이 글에 어울리는 폰트 정보를 확인하고 있어요. 추천 이유는 AI 연결 후 더 자세히 보여줄 예정이에요.";

function formatPostDate(createdAt) {
  const date = new Date(createdAt);

  if (Number.isNaN(date.getTime())) {
    return {
      date: "",
      dateTime: "",
      time: "",
    };
  }

  return {
    date: new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(date),
    dateTime: date.toISOString(),
    time: new Intl.DateTimeFormat("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(date),
  };
}

function formatCommentDate(createdAt) {
  const date = new Date(createdAt);

  if (Number.isNaN(date.getTime())) {
    return {
      date: "",
      dateTime: "",
      time: "",
    };
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");

  return {
    date: `${year}.${month}.${day}`,
    dateTime: date.toISOString(),
    time: `${hour}:${minute}`,
  };
}

function getContentFontClass(fontName) {
  if (fontName.toLowerCase() === "zodiak") {
    return "font-['Zodiak'] font-extrabold italic";
  }

  return "font-['Pretendard'] font-normal";
}

function transformPostDetail(post) {
  const formattedDate = formatPostDate(post.created_at);
  const fontName = post.font?.name ?? "Unknown";

  return {
    author: post.user?.nickname ?? post.nickname ?? "작성자",
    content: post.content,
    date: formattedDate.date,
    dateTime: formattedDate.dateTime,
    font: {
      downloadUrl: post.font?.download_url ?? post.font?.downloadUrl ?? "#",
      license: post.font?.license ?? "",
      name: fontName,
      notice:
        post.font?.notice ?? "브랜드 적용 전 라이선스 원문을 한 번 더 확인하세요.",
      reason: post.font?.reason ?? post.reason ?? fallbackFontReason,
      source: post.font?.source ?? "",
      tags: post.font?.tags ?? [],
      usage: post.font?.usage ?? "",
    },
    time: formattedDate.time,
    title: post.title,
    contentFontClass: getContentFontClass(fontName),
  };
}

function transformComment(comment) {
  const formattedDate = formatCommentDate(comment.created_at);

  return {
    content: comment.content,
    date: formattedDate.date,
    dateTime: formattedDate.dateTime,
    id: comment.id,
    nickname: comment.nickname,
    time: formattedDate.time,
  };
}

function PostDetail({ user }) {
  const navigate = useNavigate();
  const { postId } = useParams();
  const [postDetail, setPostDetail] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentContent, setCommentContent] = useState("");
  const [isLoadingPost, setIsLoadingPost] = useState(true);
  const [postErrorMessage, setPostErrorMessage] = useState("");
  const [commentErrorMessage, setCommentErrorMessage] = useState("");
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [isDeletingPost, setIsDeletingPost] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const handleCommentContentChange = (event) => {
    setCommentContent(event.target.value);
    setCommentErrorMessage("");
  };

  const handleCreateComment = async () => {
    const trimmedContent = commentContent.trim();

    if (!user) {
      setCommentErrorMessage("로그인 후 댓글을 등록해주세요.");
      return;
    }

    if (!trimmedContent) {
      setCommentErrorMessage("댓글 내용을 입력해주세요.");
      return;
    }

    setIsSubmittingComment(true);
    setCommentErrorMessage("");

    try {
      const commentResponse = await createComment(postId, {
        content: trimmedContent,
      });
      setComments((currentComments) => [
        ...currentComments,
        transformComment(commentResponse),
      ]);
      setCommentContent("");
    } catch (error) {
      setCommentErrorMessage(error.message);
    } finally {
      setIsSubmittingComment(false);
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      await deleteComment(commentId);
      setComments((currentComments) =>
        currentComments.filter((comment) => comment.id !== commentId),
      );
    } catch (error) {
      setCommentErrorMessage(error.message);
    }
  };

  const handleDeletePost = async () => {
    setIsDeletingPost(true);

    try {
      await deletePost(postId);
      setIsDeleteDialogOpen(false);
      navigate("/");
    } catch (error) {
      setPostErrorMessage(error.message);
      setIsDeleteDialogOpen(false);
    } finally {
      setIsDeletingPost(false);
    }
  };

  useEffect(() => {
    let isMounted = true;

    Promise.all([getPost(postId), getComments(postId)])
      .then(([postResponse, commentResponse]) => {
        if (!isMounted) {
          return;
        }

        setPostDetail(transformPostDetail(postResponse));
        setComments(commentResponse.map((comment) => transformComment(comment)));
      })
      .catch((error) => {
        if (!isMounted) {
          return;
        }

        setPostErrorMessage(error.message);
      })
      .finally(() => {
        if (!isMounted) {
          return;
        }

        setIsLoadingPost(false);
      });

    return () => {
      isMounted = false;
    };
  }, [postId]);

  if (isLoadingPost) {
    return (
      <main className="p-6">
        <section className="flex min-h-[520px] items-center justify-center text-center">
          <p className="text-sm text-[#d4d4d4]">게시글을 불러오는 중이에요.</p>
        </section>
      </main>
    );
  }

  if (postErrorMessage || !postDetail) {
    return (
      <main className="p-6">
        <section className="flex min-h-[520px] items-center justify-center text-center">
          <p className="text-sm text-[#d4d4d4]">
            {postErrorMessage || "게시글을 찾을 수 없습니다."}
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="p-6">
      <section className="mx-auto w-full max-w-[720px] pt-8 pb-12">
        <button
          aria-label="이전으로"
          className="mb-16 flex h-6 w-8 cursor-pointer items-center text-black transition-colors hover:text-[#d4d4d4]"
          onClick={() => navigate(-1)}
          type="button"
        >
          <ArrowLongLeftIcon className="h-6 w-8" />
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
          <time className="text-xs text-[#d4d4d4]" dateTime={postDetail.dateTime}>
            {postDetail.date} · {postDetail.time}
          </time>
          <h1 className="mt-4 text-xl font-bold leading-tight text-black">
            {postDetail.title}
          </h1>
          <p
            className={`mt-7 ${postDetail.contentFontClass} text-[28px] leading-snug text-black`}
          >
            {postDetail.content}
          </p>

          <div className="mt-8 flex items-center justify-between">
            <p className="text-sm font-semibold text-black">
              {postDetail.author}
            </p>
            <div className="flex items-center gap-4">
              <button
                className="cursor-pointer text-xs text-black transition-colors hover:text-[#d4d4d4]"
                onClick={() => navigate(`/posts/${postId}/edit`)}
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
          <div className="flex items-center gap-2 leading-none">
            <ChatBubbleLeftEllipsisIcon className="h-4 w-4 translate-y-px text-black" />
            <h2 className="text-sm font-semibold text-black">comment</h2>
            <span className="text-sm text-black">{comments.length}</span>
          </div>

          <div className="mt-3 flex items-center gap-3">
            <textarea
              className="h-20 flex-1 resize-none rounded-md border border-gray-300 px-4 py-3 text-sm leading-relaxed outline-none transition-colors placeholder:text-sm placeholder:text-gray-300 focus:border-black"
              onChange={handleCommentContentChange}
              placeholder="댓글을 입력하세요."
              value={commentContent}
            />
            <button
              className="cursor-pointer px-2 text-xs text-black transition-colors hover:text-[#d4d4d4] disabled:cursor-not-allowed disabled:text-[#d4d4d4]"
              disabled={isSubmittingComment}
              onClick={handleCreateComment}
              type="button"
            >
              {isSubmittingComment ? "등록 중" : "등록"}
            </button>
          </div>

          <p className="mt-2 min-h-5 text-right text-sm text-neutral-600">
            {commentErrorMessage}
          </p>

          {comments.length > 0 ? (
            <ul className="mt-6 space-y-5">
              {comments.map((comment) => (
                <li
                  className="grid grid-cols-[120px_1fr_auto_auto] items-start gap-4 text-xs"
                  key={comment.id}
                >
                  <p className="text-sm font-extrabold text-black">
                    {comment.nickname}
                  </p>
                  <p className="text-sm leading-relaxed text-black">
                    {comment.content}
                  </p>
                  <time
                    className="text-sm text-[#d4d4d4]"
                    dateTime={comment.dateTime}
                  >
                    {comment.date} · {comment.time}
                  </time>
                  <button
                    aria-label="댓글 삭제"
                    className="flex h-4 w-4 cursor-pointer items-center justify-center text-black transition-opacity hover:opacity-50"
                    onClick={() => handleDeleteComment(comment.id)}
                    type="button"
                  >
                    <XMarkIcon className="h-4 w-4" />
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
                className="cursor-pointer rounded-md border border-gray-300 px-4 py-1.5 text-sm text-black transition-colors hover:bg-black hover:text-white disabled:cursor-not-allowed disabled:text-[#d4d4d4] disabled:hover:bg-white disabled:hover:text-[#d4d4d4]"
                disabled={isDeletingPost}
                onClick={handleDeletePost}
                type="button"
              >
                {isDeletingPost ? "삭제 중" : "삭제"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}

export default PostDetail;
