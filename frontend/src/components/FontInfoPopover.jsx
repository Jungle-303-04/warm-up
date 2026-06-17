import { useId, useState } from "react";
import { InformationCircleIcon, XMarkIcon } from "./icons";

function isAllowedLicenseItem(item) {
  const allowedText = String(item.allowed ?? "").trim().toLowerCase();

  if (!allowedText) {
    return false;
  }

  return !["x", "불가", "금지", "금지됨", "사용 불가"].some((blockedText) =>
    allowedText.includes(blockedText),
  );
}

function createAllowedUsageText(font) {
  const licenseSummary = Array.isArray(font.licenseSummary)
    ? font.licenseSummary
    : [];
  const allowedCategories = licenseSummary
    .filter((item) => isAllowedLicenseItem(item))
    .map((item) => item.category)
    .filter(Boolean);

  if (allowedCategories.length > 0) {
    return allowedCategories.join(" | ");
  }

  return font.usage;
}

function FontInfoPopover({ font }) {
  const [isOpen, setIsOpen] = useState(false);
  const popoverId = useId();
  const allowedUsageText = createAllowedUsageText(font);
  const priceText = font.isPaid ? "유료" : "무료";

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
        <InformationCircleIcon className="h-3.5 w-3.5" />
        {font.name}
      </button>

      {isOpen ? (
        <div
          className="absolute right-full top-0 z-30 mr-3 w-64 rounded-md border border-gray-300/35 bg-[#F8F9FA]/88 p-4 text-left shadow-[0_8px_24px_rgba(15,23,42,0.1),inset_0_1px_0_rgba(255,255,255,0.45)] backdrop-blur-[2px]"
          id={popoverId}
          role="dialog"
        >
          <span
            aria-hidden="true"
            className="absolute right-[-6px] top-2.5 h-3 w-3 rotate-45 border-t border-r border-gray-300/35 bg-[#F8F9FA]/88"
          />

          <div className="-mt-2 flex items-center justify-between gap-4">
            <p className="text-sm font-semibold text-black">{font.name}</p>
            <button
              aria-label="폰트 정보 닫기"
              className="flex h-5 w-5 cursor-pointer items-center justify-center text-black transition-opacity hover:opacity-50"
              onClick={() => setIsOpen(false)}
              type="button"
            >
              <XMarkIcon className="h-4 w-4" />
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
              <dt className="font-semibold">가격</dt>
              <dd className="mt-1 text-[#6b7280]">{priceText}</dd>
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
              <dd className="mt-1 text-[#6b7280]">{allowedUsageText}</dd>
            </div>
          </dl>
        </div>
      ) : null}
    </div>
  );
}

export default FontInfoPopover;
