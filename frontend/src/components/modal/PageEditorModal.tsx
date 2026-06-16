import { X } from "lucide-react";
import { useState } from "react";

import { createPage } from "../../api/pages";
import type { BlockInput, PageCreateRequest, PageType } from "../../types/page";
import { BlockEditor } from "./BlockEditor";

type PageEditorModalProps = {
  pageType: PageType;
  initialDate: string;
  onClose: () => void;
  onSaved: () => void;
};

// 쉼표로 입력한 참여자 문자열을 배열로 바꿉니다.
function splitCommaText(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

// input[type="time"]의 HH:mm 값을 백엔드가 기대하는 HH:mm:ss 형태로 바꿉니다.
function normalizeTime(value: string) {
  if (!value) {
    return null;
  }

  return `${value}:00`;
}

export function PageEditorModal({
  pageType,
  initialDate,
  onClose,
  onSaved,
}: PageEditorModalProps) {
  const isMeeting = pageType === "MEETING";

  // 모달 내부 폼 입력값들입니다. 회의와 회고는 같은 모달을 쓰되 일부 필드만 다릅니다.
  const [title, setTitle] = useState(
    isMeeting ? "새 회의" : `${initialDate} 회고`
  );
  const [date, setDate] = useState(initialDate);
  const [startTime, setStartTime] = useState("14:00");
  const [endTime, setEndTime] = useState("15:00");
  const [participantsText, setParticipantsText] = useState("");
  const [blocks, setBlocks] = useState<BlockInput[]>([
    {
      type: "PARAGRAPH",
      content: "",
      checked: null,
    },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleBackdropMouseDown = (
    event: React.MouseEvent<HTMLDivElement>
  ) => {
    // 모달 바깥 배경을 클릭했을 때만 닫고, 모달 내부 클릭은 무시합니다.
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    // 백엔드에서 title은 필수이므로 프론트에서 먼저 검사합니다.
    if (!title.trim()) {
      alert("제목을 입력해주세요.");
      return;
    }

    try {
      setIsSubmitting(true);

      // 빈 본문 블록은 저장하지 않도록 제거합니다.
      const cleanedBlocks = blocks
        .map((block) => ({
          ...block,
          content: block.content.trim(),
        }))
        .filter((block) => block.content.length > 0);

      // 화면 입력값을 백엔드 PageCreateRequest 형태로 조립합니다.
      const payload: PageCreateRequest = {
        type: pageType,
        title: title.trim(),
        date,
        start_time: isMeeting ? normalizeTime(startTime) : null,
        end_time: isMeeting ? normalizeTime(endTime) : null,
        participants: splitCommaText(participantsText),
        blocks: cleanedBlocks,
      };

      await createPage(payload);

      // 저장 성공 후 부모(CalendarPage)에게 알리고, 부모가 목록을 다시 조회합니다.
      onSaved();
    } catch (error) {
      console.error(error);
      alert("저장에 실패했습니다. 로그인 토큰이나 서버 상태를 확인해주세요.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={handleBackdropMouseDown}>
      <form className="page-modal" onSubmit={handleSubmit}>
        <header className="page-modal-header">
          <div>
            <span className={`modal-type-badge ${isMeeting ? "meeting" : "retro"}`}>
              {isMeeting ? "회의" : "회고"}
            </span>
            <h2>{isMeeting ? "회의 작성" : "회고 작성"}</h2>
          </div>

          <button type="button" className="modal-close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </header>

        <div className="page-modal-body">
          <label className="form-field">
            <span>제목</span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder={isMeeting ? "회의 제목" : "회고 제목"}
            />
          </label>

          <div className="form-grid">
            <label className="form-field">
              <span>날짜</span>
              <input
                type="date"
                value={date}
                onChange={(event) => setDate(event.target.value)}
                disabled
              />
            </label>

            {isMeeting && (
              <>
                <label className="form-field">
                  <span>시작 시간</span>
                  <input
                    type="time"
                    value={startTime}
                    onChange={(event) => setStartTime(event.target.value)}
                  />
                </label>

                <label className="form-field">
                  <span>종료 시간</span>
                  <input
                    type="time"
                    value={endTime}
                    onChange={(event) => setEndTime(event.target.value)}
                  />
                </label>
              </>
            )}
          </div>

          <label className="form-field">
            <span>참여자</span>
            <input
              value={participantsText}
              onChange={(event) => setParticipantsText(event.target.value)}
              placeholder="예: 찬빈, 민수, 지영"
            />
          </label>

          <BlockEditor blocks={blocks} onChange={setBlocks} />
        </div>

        <footer className="page-modal-footer">
          <button type="button" className="secondary-button" onClick={onClose}>
            취소
          </button>

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? "저장 중..." : "저장"}
          </button>
        </footer>
      </form>
    </div>
  );
}
