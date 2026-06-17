import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createPost, getPost, updatePost } from "../api/posts";
import { recommendFont } from "../api/recommendations";
import FontInfoPopover from "../components/FontInfoPopover";
import { ArrowLongLeftIcon } from "../components/icons";
import PreservedText from "../components/PreservedText";
import { createWebFontStyle, hasWebFontUrl } from "../utils/webFont";

const waitingMessages = [
  [
    "고딕체는 명확함을, 손글씨체는 친근함을 전달하는 경우가 많아요.",
    "문장의 분위기를 분석하는 중...",
  ],
  [
    "좋은 폰트는 내용을 꾸미기보다 돋보이게 해요.",
    "어울리는 폰트를 탐색하는 중...",
  ],
  [
    "굵기 하나만 달라도 분위기는 크게 바뀔 수 있어요.",
    "폰트 특징을 분석하는 중...",
  ],
];

function createRecommendationFromPost(post) {
  const font = post.font ?? {};
  const isPaid = font.is_paid ?? font.isPaid;

  return {
    downloadUrl: font.download_url ?? font.downloadUrl ?? "",
    id: font.id,
    isDefaultFontApplied: !hasWebFontUrl(font),
    isPaid,
    license: font.license ?? "",
    licenseSummary: font.license_summary ?? font.licenseSummary ?? [],
    name: font.name ?? "",
    previewFontStyle: createWebFontStyle(font),
    reason: post.recommend_reason ?? "",
    source: font.source ?? "",
    sourceUrl: font.source_url ?? font.sourceUrl,
    tags: font.tags ?? [],
    usage: font.category ?? "",
    webfonts: font.webfonts ?? [],
  };
}

function createRecommendationFromResponse(recommendationResponse) {
  const selectedFont = recommendationResponse.font ?? {};
  const selection = recommendationResponse.selection ?? {};
  const isPaid = selectedFont.is_paid ?? selectedFont.isPaid;

  return {
    downloadUrl: selectedFont.download_url ?? "",
    id: selectedFont.id ?? selection.font_id,
    isDefaultFontApplied: !hasWebFontUrl(selectedFont),
    isPaid,
    license: selectedFont.license ?? "",
    licenseSummary: selectedFont.license_summary ?? selectedFont.licenseSummary ?? [],
    name: selectedFont.name ?? "",
    previewFontStyle: createWebFontStyle(selectedFont),
    reason:
      selection.display_reason ??
      selection.reason ??
      selectedFont.description ??
      "",
    source: selectedFont.source ?? "",
    sourceUrl: selectedFont.source_url ?? selectedFont.sourceUrl,
    tags: selectedFont.tags ?? [],
    usage: selectedFont.category ?? "",
    webfonts: selectedFont.webfonts ?? [],
  };
}

function TypingWaitingMessage({ lines }) {
  const fixedLines = lines.slice(0, -1);
  const typingLine = lines.at(-1) ?? "";
  const [typedLine, setTypedLine] = useState("");

  useEffect(() => {
    let currentIndex = 0;
    const typingTimer = setInterval(() => {
      currentIndex += 1;
      setTypedLine(typingLine.slice(0, currentIndex));

      if (currentIndex >= typingLine.length) {
        clearInterval(typingTimer);
      }
    }, 70);

    return () => {
      clearInterval(typingTimer);
    };
  }, [typingLine]);

  return (
    <div className="space-y-1">
      {fixedLines.map((line) => (
        <p className="text-base font-semibold text-black" key={line}>
          {line}
        </p>
      ))}
      <p className="text-base font-semibold text-black">
        {typedLine}
        <span className="ml-0.5 inline-block h-4 w-px translate-y-0.5 animate-pulse bg-black" />
      </p>
    </div>
  );
}

function shuffleWaitingMessages() {
  const shuffledMessages = [...waitingMessages];

  for (let index = shuffledMessages.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    const currentMessage = shuffledMessages[index];

    shuffledMessages[index] = shuffledMessages[randomIndex];
    shuffledMessages[randomIndex] = currentMessage;
  }

  return shuffledMessages;
}

function Write({ onAuthExpired = () => {} }) {
  const navigate = useNavigate();
  const { postId } = useParams();
  const isEditMode = Boolean(postId);
  const [activeTab, setActiveTab] = useState("write");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isLoadingPost, setIsLoadingPost] = useState(isEditMode);
  const [isRecommending, setIsRecommending] = useState(false);
  const [isSubmittingPost, setIsSubmittingPost] = useState(false);
  const [postErrorMessage, setPostErrorMessage] = useState("");
  const [recommendation, setRecommendation] = useState(null);
  const [waitingMessageIndex, setWaitingMessageIndex] = useState(0);
  const [waitingMessageQueue, setWaitingMessageQueue] = useState(waitingMessages);
  const waitingMessage = waitingMessageQueue[waitingMessageIndex] ?? waitingMessages[0];
  const isPreviewTab = activeTab === "preview";
  const hasRecommendation = isPreviewTab && recommendation;
  const defaultFontMessage =
    "웹폰트가 없어 기본 폰트로 표시됐어요.";
  const shouldShowDefaultFontNotice =
    isPreviewTab && recommendation?.isDefaultFontApplied;
  const hasDefaultFontDownloadUrl =
    typeof recommendation?.downloadUrl === "string" &&
    recommendation.downloadUrl.trim() !== "" &&
    recommendation.downloadUrl !== "#";
  const previewText = content;

  useEffect(() => {
    if (!isEditMode) {
      return;
    }

    let shouldUpdateState = true;

    const loadPostForEdit = async () => {
      setIsLoadingPost(true);
      setPostErrorMessage("");

      try {
        const post = await getPost(postId);

        if (!shouldUpdateState) {
          return;
        }

        setTitle(post.title ?? "");
        setContent(post.content ?? "");
        setRecommendation(createRecommendationFromPost(post));
        setActiveTab("write");
      } catch (error) {
        if (shouldUpdateState) {
          setPostErrorMessage(error.message);
        }
      } finally {
        if (shouldUpdateState) {
          setIsLoadingPost(false);
        }
      }
    };

    loadPostForEdit();

    return () => {
      shouldUpdateState = false;
    };
  }, [isEditMode, postId]);

  const handleTitleChange = (event) => {
    setTitle(event.target.value);
    setPostErrorMessage("");
  };

  const handleContentChange = (event) => {
    setContent(event.target.value);
    setPostErrorMessage("");
  };

  const handleRecommend = async () => {
    const trimmedContent = content.trim();

    if (!trimmedContent) {
      setPostErrorMessage("게시글 내용을 입력해주세요.");
      return;
    }

    setPostErrorMessage("");
    setActiveTab("preview");
    setWaitingMessageIndex(0);
    setWaitingMessageQueue(shuffleWaitingMessages());
    setIsRecommending(true);
    setRecommendation(null);

    try {
      const recommendationResponse = await recommendFont({
        text: trimmedContent,
      });

      setRecommendation(createRecommendationFromResponse(recommendationResponse));
    } catch (error) {
      setPostErrorMessage(error.message);
    } finally {
      setIsRecommending(false);
    }
  };

  useEffect(() => {
    if (!isRecommending) {
      return undefined;
    }

    const waitingMessageTimer = setInterval(() => {
      setWaitingMessageIndex((currentIndex) => {
        return (currentIndex + 1) % waitingMessageQueue.length;
      });
    }, 4200);

    return () => {
      clearInterval(waitingMessageTimer);
    };
  }, [isRecommending, waitingMessageQueue.length]);

  const handleSubmitPost = async () => {
    const trimmedTitle = title.trim();
    const trimmedContent = content.trim();
    const selectedFontId = recommendation?.id;
    const recommendReason = recommendation?.reason?.trim();

    if (!trimmedTitle) {
      setPostErrorMessage("제목을 입력해주세요.");
      return;
    }

    if (!trimmedContent) {
      setPostErrorMessage("게시글 내용을 입력해주세요.");
      return;
    }

    if (!selectedFontId) {
      setPostErrorMessage("폰트 추천 후 등록할 수 있어요.");
      return;
    }

    if (!recommendReason) {
      setPostErrorMessage("추천 이유가 필요해요.");
      return;
    }

    setIsSubmittingPost(true);
    setPostErrorMessage("");

    try {
      const createdPost = await createPost({
        title: trimmedTitle,
        content: trimmedContent,
        fontId: selectedFontId,
        recommendReason,
      });

      navigate(`/posts/${createdPost.id}`);
    } catch (error) {
      if (error.status === 401) {
        onAuthExpired();
        return;
      }

      setPostErrorMessage(error.message);
    } finally {
      setIsSubmittingPost(false);
    }
  };

  const handleUpdatePost = async () => {
    const trimmedTitle = title.trim();
    const trimmedContent = content.trim();
    const selectedFontId = recommendation?.id;
    const recommendReason = recommendation?.reason?.trim();

    if (!trimmedTitle) {
      setPostErrorMessage("제목을 입력해주세요.");
      return;
    }

    if (!trimmedContent) {
      setPostErrorMessage("게시글 내용을 입력해주세요.");
      return;
    }

    if (!selectedFontId) {
      setPostErrorMessage("폰트 정보가 필요해요.");
      return;
    }

    if (!recommendReason) {
      setPostErrorMessage("추천 이유가 필요해요.");
      return;
    }

    setIsSubmittingPost(true);
    setPostErrorMessage("");

    try {
      await updatePost(postId, {
        title: trimmedTitle,
        content: trimmedContent,
        fontId: selectedFontId,
        recommendReason,
      });

      navigate(`/posts/${postId}`);
    } catch (error) {
      if (error.status === 401) {
        onAuthExpired();
        return;
      }

      setPostErrorMessage(error.message);
    } finally {
      setIsSubmittingPost(false);
    }
  };

  const isPreviewDisabled = !recommendation && !isRecommending;

  return (
    <main className="min-h-[620px] p-6">
      <section
        className={[
          "mx-auto flex w-full max-w-[720px] flex-col pb-10",
          isEditMode ? "pt-8" : "pt-36",
        ].join(" ")}
      >
        {isEditMode ? (
          <button
            aria-label="이전으로"
            className="mb-16 flex h-6 w-8 cursor-pointer items-center text-black transition-colors hover:text-[#d4d4d4]"
            onClick={() => navigate(-1)}
            type="button"
          >
            <ArrowLongLeftIcon className="h-6 w-8" />
          </button>
        ) : null}

        {isLoadingPost ? (
          <div className="flex min-h-[420px] items-center justify-center text-sm text-[#d4d4d4]">
            게시글을 불러오는 중...
          </div>
        ) : (
          <>

        <div className="h-[132px]">
          <div className="h-full overflow-visible pr-2">
            <div className="grid h-full grid-cols-[1fr_auto] items-start gap-5 overflow-visible">
              <div className="ml-auto flex h-full w-2/3 flex-col">
                <div className="flex min-h-7 flex-wrap items-center gap-2">
                  {hasRecommendation ? (
                    <>
                      <FontInfoPopover font={recommendation} />
                      {recommendation.tags.map((tag) => (
                        <span
                          className="rounded-full border border-gray-200 bg-white px-2 py-0.5 text-[10px] font-medium text-black"
                          key={tag}
                        >
                          {tag}
                        </span>
                      ))}
                    </>
                  ) : null}
                </div>

                <div className="mt-3 flex min-h-16 items-center overflow-visible pr-1">
                  {hasRecommendation ? (
                    <p className="thin-transparent-scrollbar max-h-16 overflow-y-auto text-left text-sm leading-relaxed text-black">
                      {recommendation.reason}
                    </p>
                  ) : (
                    <p className="w-full text-right text-sm leading-relaxed text-[#d4d4d4]">
                      문장을 입력하고 폰트 추천을 눌러보세요.
                    </p>
                  )}
                </div>
              </div>
              <div className="flex h-full flex-col">
                <div className="min-h-7" />
                <div className="mt-3 flex min-h-16 items-center overflow-visible">
                  <span
                    className={[
                      "shrink-0 font-['Zodiak'] text-[28pt] font-extrabold italic leading-none text-black",
                      hasRecommendation ? "animate-tilt-once" : "",
                    ].join(" ")}
                  >
                    f
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <input
          className="mt-20 w-full border-b border-gray-200 px-1 py-2 text-base outline-none transition-colors placeholder:text-gray-300 focus:border-black"
          maxLength={100}
          onChange={handleTitleChange}
          placeholder="제목을 입력하세요."
          type="text"
          value={title}
        />

        <div
          className={[
            "relative z-10 mt-10 flex items-end gap-1 pl-2",
            isPreviewTab ? "border-b border-gray-200" : "-mb-px",
          ].join(" ")}
        >
          <button
            className={[
              "cursor-pointer rounded-t-md border px-4 py-2 text-sm transition-colors",
              activeTab === "write"
                ? "border-gray-300 border-b-[#F8F9FA] bg-[#F8F9FA] text-black"
                : isPreviewTab
                  ? "border-transparent text-gray-500 hover:bg-[#F8F9FA] hover:text-black"
                  : "border-transparent text-gray-500 hover:border-gray-200 hover:border-b-[#F8F9FA] hover:bg-[#F8F9FA] hover:text-black",
            ].join(" ")}
            onClick={() => setActiveTab("write")}
            type="button"
          >
            Write
          </button>
          <button
            className={[
              "rounded-t-md border px-4 py-2 text-sm transition-colors",
              isPreviewDisabled
                ? "cursor-not-allowed text-gray-300"
                : isPreviewTab
                  ? "cursor-pointer hover:bg-[#F8F9FA] hover:text-black"
                  : "cursor-pointer hover:border-gray-200 hover:border-b-[#F8F9FA] hover:bg-[#F8F9FA] hover:text-black",
              activeTab === "preview"
                ? isPreviewTab
                  ? "border-gray-300 border-b-[#F8F9FA] bg-[#F8F9FA] text-black"
                  : "border-gray-300 border-b-[#F8F9FA] bg-[#F8F9FA] text-black"
                : "border-transparent text-gray-500",
            ].join(" ")}
            disabled={isPreviewDisabled}
            onClick={() => setActiveTab("preview")}
            type="button"
          >
            Preview
          </button>
          {shouldShowDefaultFontNotice ? (
            <p className="ml-auto mb-2 inline-flex items-center gap-2 text-xs text-[#d4d4d4]">
              <span>{defaultFontMessage}</span>
              {hasDefaultFontDownloadUrl ? (
                <a
                  className="text-black underline-offset-2 transition-colors hover:text-[#d4d4d4] hover:underline"
                  href={recommendation.downloadUrl}
                  rel="noreferrer"
                  target="_blank"
                >
                  폰트 보러가기
                </a>
              ) : (
                <span className="text-black">다운로드 페이지를 확인해주세요.</span>
              )}
            </p>
          ) : null}
        </div>
        <div className="min-h-[380px]">
          {activeTab === "write" ? (
            <>
              <textarea
                className="thin-transparent-scrollbar h-52 w-full resize-none overflow-y-auto rounded-md border border-gray-300 px-5 py-4 text-base leading-relaxed outline-none transition-colors placeholder:text-gray-300 focus:border-black"
                maxLength={1500}
                onChange={handleContentChange}
                placeholder="게시글 내용을 입력하세요. 1500자 이내"
                value={content}
              />
              <div className="mt-3 flex justify-end">
                <button
                  className="cursor-pointer rounded-md border border-gray-300 px-5 py-2 text-sm text-black transition-colors hover:bg-black hover:text-white"
                  onClick={handleRecommend}
                  type="button"
                >
                  폰트 추천
                </button>
              </div>
              <p className="mt-2 text-right text-xs text-[#d4d4d4]">
                문장을 수정하면 다른 폰트가 추천될 수 있어요.
              </p>
            </>
          ) : (
            <div className="relative min-h-[380px]">
              <div
                className={[
                  "transition duration-300",
                  isRecommending ? "blur-[2px]" : "blur-0",
                ].join(" ")}
              >
                {recommendation ? (
                  <div>
                    <div className="flex h-52 items-stretch border-b border-black">
                      <div className="thin-transparent-scrollbar h-full w-full overflow-y-auto px-5 pt-4 pb-3">
                        <PreservedText
                          className="text-[22px] leading-relaxed text-black"
                          style={recommendation.previewFontStyle}
                          text={previewText}
                        />
                      </div>
                    </div>

                    <div className="mt-6 flex justify-end">
                      <button
                        className="cursor-pointer rounded-md border border-gray-300 px-5 py-2 text-sm text-black transition-colors hover:bg-black hover:text-white disabled:cursor-not-allowed disabled:text-gray-300 disabled:hover:bg-white disabled:hover:text-gray-300"
                        disabled={isSubmittingPost}
                        onClick={isEditMode ? handleUpdatePost : handleSubmitPost}
                        type="button"
                      >
                        {isSubmittingPost
                          ? isEditMode
                            ? "수정 중..."
                            : "등록 중..."
                          : isEditMode
                            ? "수정하기"
                            : "등록 하기"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="h-52 rounded-md border border-gray-200" />
                )}
              </div>

              {isRecommending ? (
                <div className="absolute inset-x-0 top-0 flex h-52 items-center justify-center">
                  <div className="rounded-md bg-white/80 px-8 py-6 text-center">
                    <TypingWaitingMessage lines={waitingMessage} />
                  </div>
                </div>
              ) : null}
              <p className="mt-2 min-h-4 text-right text-xs text-black">
                {postErrorMessage}
              </p>
            </div>
          )}
        </div>
          </>
        )}
      </section>
    </main>
  );
}

export default Write;
