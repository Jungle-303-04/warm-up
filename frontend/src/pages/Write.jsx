import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import FontInfoPopover from "../components/FontInfoPopover";
import { ArrowLongLeftIcon } from "../components/icons";

const waitingMessages = [
  [
    "같은 문장도 폰트에 따라 인상이 달라져요.",
    "글의 인상을 살피는 중...",
  ],
];

const recommendedFont = {
  downloadUrl: "https://www.fontshare.com/fonts/zodiak",
  license: "OFL",
  name: "Zodiak",
  notice: "브랜드 적용 전 라이선스 원문을 한 번 더 확인하세요.",
  tags: ["영문", "세리프", "강조"],
  reason:
    "입력한 문장은 짧지만 감정의 방향이 분명하고, 말의 끝에 힘이 남는 구조예요. 그래서 부드럽기보다는 인상이 또렷하게 남는 세리프 계열 폰트가 잘 어울려요. 특히 Zodiak은 문장의 리듬을 조금 더 극적으로 보여주면서도 과하게 장식적으로 느껴지지 않아, 제목이나 강조 문장에 사용하기 좋아요.",
  source: "Fontshare",
  previewText: "I want to play this game forever",
  usage: "인쇄, 웹사이트, 영상, BI/CI",
};

const editablePost = {
  content:
    "Once upon a time, in a quiet village beside a silver forest, a small lantern learned how to glow. Every night it listened to the wind, gathered stories from the stars, and lit a narrow path for children who dreamed of finding a hidden garden beyond the hill.",
  font: recommendedFont,
  title: "Boost your conversion rate",
};

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
    <>
      {fixedLines.map((line) => (
        <p className="text-base font-semibold text-black" key={line}>
          {line}
        </p>
      ))}
      <p className="text-base font-semibold text-black">
        {typedLine}
        <span className="ml-0.5 inline-block h-4 w-px translate-y-0.5 animate-pulse bg-black" />
      </p>
    </>
  );
}

function Write() {
  const navigate = useNavigate();
  const { postId } = useParams();
  const isEditMode = Boolean(postId);
  const initialTitle = isEditMode ? editablePost.title : "";
  const initialContent = isEditMode ? editablePost.content : "";
  const initialRecommendation = isEditMode ? editablePost.font : null;
  const [activeTab, setActiveTab] = useState("write");
  const [title, setTitle] = useState(initialTitle);
  const [content, setContent] = useState(initialContent);
  const [isRecommending, setIsRecommending] = useState(false);
  const [recommendation, setRecommendation] = useState(initialRecommendation);
  const waitingMessage = waitingMessages[0];
  const isPreviewTab = activeTab === "preview";
  const hasRecommendation = isPreviewTab && recommendation;
  const previewText = isEditMode ? content : recommendation?.previewText;

  const handleRecommend = () => {
    setActiveTab("preview");
    setIsRecommending(true);
    setRecommendation(null);

    setTimeout(() => {
      setRecommendation(recommendedFont);
      setIsRecommending(false);
    }, 1800);
  };

  const handleSubmitPost = () => {
    navigate("/posts/1");
  };

  const handleUpdatePost = () => {
    navigate(`/posts/${postId}`);
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
          onChange={(event) => setTitle(event.target.value)}
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
        </div>
        <div className="min-h-[340px]">
          {activeTab === "write" ? (
            <>
              <textarea
                className="thin-transparent-scrollbar h-36 w-full resize-none overflow-y-auto rounded-md border border-gray-300 px-5 py-4 text-base leading-relaxed outline-none transition-colors placeholder:text-gray-300 focus:border-black"
                onChange={(event) => setContent(event.target.value)}
                placeholder="게시글 내용을 입력하세요."
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
            <div className="relative min-h-[340px]">
              <div
                className={[
                  "transition duration-300",
                  isRecommending ? "blur-[2px]" : "blur-0",
                ].join(" ")}
              >
                {recommendation ? (
                  <div>
                    <div className="flex h-36 items-end border-b border-black">
                      <div className="thin-transparent-scrollbar max-h-[calc(9rem-1px)] w-full overflow-y-auto pr-2 pb-1.5">
                        <p className="font-['Zodiak'] text-[28px] font-extrabold italic leading-tight text-black">
                          {previewText}
                        </p>
                      </div>
                    </div>

                    <div className="mt-6 flex justify-end">
                      <button
                        className="cursor-pointer rounded-md border border-gray-300 px-5 py-2 text-sm text-black transition-colors hover:bg-black hover:text-white"
                        onClick={isEditMode ? handleUpdatePost : handleSubmitPost}
                        type="button"
                      >
                        {isEditMode ? "수정하기" : "등록 하기"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="h-36 rounded-md border border-gray-200" />
                )}
              </div>

              {isRecommending ? (
                <div className="absolute inset-x-0 top-0 flex h-36 items-center justify-center">
                  <div className="rounded-md bg-white/80 px-8 py-6 text-center">
                    <TypingWaitingMessage lines={waitingMessage} />
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

export default Write;
