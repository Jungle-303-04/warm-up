import { useEffect, useState } from "react";

const waitingMessages = [
  [
    "같은 문장도 폰트에 따라 인상이 달라져요.",
    "글의 인상을 살피는 중...",
  ],
];

const recommendedFont = {
  name: "Zodiak",
  tags: ["영문", "세리프", "강조"],
  reason:
    "문장에 담긴 선명한 감정과 짧은 호흡이 잘 보여서, 인상이 강하게 남는 세리프 계열 폰트를 추천했어요.",
  previewText: "I want to play this game forever",
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
  const [activeTab, setActiveTab] = useState("write");
  const [content, setContent] = useState("");
  const [isRecommending, setIsRecommending] = useState(false);
  const [recommendation, setRecommendation] = useState(null);
  const waitingMessage = waitingMessages[0];

  const handleRecommend = () => {
    setActiveTab("preview");
    setIsRecommending(true);
    setRecommendation(null);

    setTimeout(() => {
      setRecommendation(recommendedFont);
      setIsRecommending(false);
    }, 1800);
  };

  const isPreviewDisabled = !recommendation && !isRecommending;

  return (
    <main className="min-h-[620px] p-6">
      <section className="mx-auto flex w-full max-w-[560px] flex-col pt-16">
        <div className="min-h-[112px]">
          {activeTab === "preview" && recommendation ? (
            <div className="max-h-28 overflow-y-auto pr-2">
              <div className="flex items-center justify-between gap-5">
                <div className="min-w-0 flex-1">
                  <div className="ml-auto w-2/3">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        className="flex shrink-0 cursor-pointer items-center gap-1 rounded-md bg-black px-2 py-0.5 text-[10px] font-medium text-white transition-opacity hover:opacity-70"
                        type="button"
                      >
                        <svg
                          aria-hidden="true"
                          className="h-3 w-3"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.6"
                          viewBox="0 0 24 24"
                        >
                          <path
                            d="M12 17v-5m0-4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                        {recommendation.name}
                      </button>
                      {recommendation.tags.map((tag) => (
                        <span
                          className="rounded-full border border-gray-200 bg-white px-2 py-0.5 text-[10px] font-medium text-black"
                          key={tag}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>

                    <p className="mt-3 text-left text-sm leading-relaxed text-black">
                      {recommendation.reason}
                    </p>
                  </div>
                </div>
                <span className="animate-tilt-once mt-7 shrink-0 font-['Zodiak'] text-[28pt] font-extrabold italic leading-none text-black">
                  f
                </span>
              </div>
            </div>
          ) : (
            <div className="flex justify-end">
              <span className="font-['Zodiak'] text-[28pt] font-extrabold italic leading-none text-black">
                f
              </span>
            </div>
          )}
        </div>

        <div className="mt-6 flex items-center gap-2">
          <button
            className={[
              "cursor-pointer rounded-md px-4 py-2 text-sm transition-colors",
              activeTab === "write"
                ? "bg-[#d4d4d4] text-black"
                : "text-gray-500 hover:bg-[#d4d4d4] hover:text-black",
            ].join(" ")}
            onClick={() => setActiveTab("write")}
            type="button"
          >
            Write
          </button>
          <button
            className={[
              "rounded-md px-4 py-2 text-sm transition-colors",
              isPreviewDisabled
                ? "cursor-not-allowed text-gray-300"
                : "cursor-pointer hover:bg-[#d4d4d4] hover:text-black",
              activeTab === "preview" ? "bg-[#d4d4d4] text-black" : "text-gray-500",
            ].join(" ")}
            disabled={isPreviewDisabled}
            onClick={() => setActiveTab("preview")}
            type="button"
          >
            Preview
          </button>
        </div>

        <div className="mt-3">
          {activeTab === "write" ? (
            <>
              <textarea
                className="max-h-60 min-h-36 w-full resize-none overflow-y-auto rounded-md border border-gray-300 px-5 py-4 text-base leading-relaxed outline-none transition-colors placeholder:text-gray-300 focus:border-black"
                onChange={(event) => setContent(event.target.value)}
                placeholder="Add your comment..."
                value={content}
              />
              <div className="mt-3 flex justify-end">
                <button
                  className="cursor-pointer rounded-full border border-gray-300 px-5 py-2 text-sm text-black transition-colors hover:bg-black hover:text-white"
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
            <div className="relative min-h-72">
              <div
                className={[
                  "transition duration-300",
                  isRecommending ? "blur-[2px]" : "blur-0",
                ].join(" ")}
              >
                {recommendation ? (
                  <div className="max-h-72 overflow-y-auto pr-2">
                    <div className="mt-12">
                      <p className="border-b border-black pb-2 font-['Zodiak'] text-[28px] font-extrabold italic leading-tight text-black">
                        {recommendation.previewText}
                      </p>
                    </div>

                    <div className="mt-6 flex justify-end">
                      <button
                        className="cursor-pointer rounded-full border border-gray-300 px-5 py-2 text-sm text-black transition-colors hover:bg-black hover:text-white"
                        type="button"
                      >
                        등록 하기
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="min-h-72 rounded-md border border-gray-200" />
                )}
              </div>

              {isRecommending ? (
                <div className="absolute inset-0 flex items-center justify-center">
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
