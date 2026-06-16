import { useId, useState } from "react";

function FontInfoPopover({ font }) {
  const [isOpen, setIsOpen] = useState(false);
  const popoverId = useId();

  const handleToggle = () => {
    setIsOpen((currentValue) => !currentValue);
  };

  return (
    <div className="relative inline-flex">
      <button
        aria-controls={popoverId}
        aria-expanded={isOpen}
        className="flex shrink-0 cursor-pointer items-center gap-1 rounded-md bg-black px-2 py-0.5 text-[10px] font-medium text-white transition-opacity hover:opacity-70"
        onClick={handleToggle}
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
        {font.name}
      </button>

      {isOpen ? (
        <div
          className="absolute right-full top-0 z-30 mr-3 w-64 rounded-md border border-gray-300/40 bg-[#F8F9FA]/86 p-4 text-left shadow-[0_8px_24px_rgba(15,23,42,0.1),inset_0_1px_0_rgba(255,255,255,0.55)] backdrop-blur-sm"
          id={popoverId}
          role="dialog"
        >
          <span
            aria-hidden="true"
            className="absolute right-[-9px] top-2 h-0 w-0 border-y-[9px] border-l-[9px] border-y-transparent border-l-gray-300/40"
          />
          <span
            aria-hidden="true"
            className="absolute right-[-7px] top-[9px] h-0 w-0 border-y-8 border-l-8 border-y-transparent border-l-[#F8F9FA]/86"
          />

          <div className="-mt-2 flex items-center justify-between gap-4">
            <p className="text-sm font-semibold text-black">{font.name}</p>
            <button
              aria-label="폰트 정보 닫기"
              className="cursor-pointer text-xs leading-none text-black transition-opacity hover:opacity-50"
              onClick={() => setIsOpen(false)}
              type="button"
            >
              x
            </button>
          </div>

          <dl className="mt-4 space-y-3 text-xs leading-relaxed text-black">
            <div>
              <dt className="font-semibold">출처</dt>
              <dd className="mt-1 text-[#6b7280]">{font.source}</dd>
            </div>
            <div>
              <dt className="font-semibold">라이선스</dt>
              <dd className="mt-1 text-[#6b7280]">{font.license}</dd>
            </div>
            <div>
              <dt className="font-semibold">Download URL</dt>
              <dd className="mt-1">
                <a
                  className="text-[#6b7280] underline-offset-2 transition-colors hover:text-black hover:underline"
                  href={font.downloadUrl}
                  rel="noreferrer"
                  target="_blank"
                >
                  {font.downloadUrl}
                </a>
              </dd>
            </div>
            <div>
              <dt className="font-semibold">사용 가능</dt>
              <dd className="mt-1 text-[#6b7280]">{font.usage}</dd>
            </div>
            <div>
              <dt className="font-semibold">주의</dt>
              <dd className="mt-1 text-[#6b7280]">{font.notice}</dd>
            </div>
          </dl>
        </div>
      ) : null}
    </div>
  );
}

export default FontInfoPopover;
