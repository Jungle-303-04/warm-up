import { X } from "lucide-react";
import { useEffect, useState } from "react";

import type { UserResponse } from "../../api/auth";
import { getPage, updatePage } from "../../api/pages";
import type {
  BlockInput,
  BlockResponse,
  BlockType,
  PageResponse,
  PageType,
} from "../../types/page";

type PageDetailModalProps = {
  pageId: number;
  currentUser: UserResponse | null;
  onClose: () => void;
  onSaved: () => void;
};

const BLOCK_TYPES: { label: string; value: BlockType }[] = [
  { label: "문단", value: "PARAGRAPH" },
  { label: "제목", value: "HEADING" },
  { label: "불릿", value: "BULLET" },
  { label: "체크리스트", value: "CHECKLIST" },
  { label: "코드", value: "CODE" },
];

function getTypeText(type: PageType) {
  return type === "MEETING" ? "회의" : "회고";
}

function getBlockTypeText(type: BlockResponse["type"]) {
  switch (type) {
    case "HEADING":
      return "제목";
    case "BULLET":
      return "불릿";
    case "CHECKLIST":
      return "체크리스트";
    case "CODE":
      return "코드";
    default:
      return "문단";
  }
}

function splitCommaText(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeTime(value: string) {
  if (!value) {
    return null;
  }

  return `${value}:00`;
}

function toTimeInputValue(value: string | null) {
  return value ? value.slice(0, 5) : "";
}

function responseBlocksToInput(blocks: BlockResponse[]): BlockInput[] {
  return blocks.map((block) => ({
    type: block.type,
    content: block.content,
    checked: block.checked,
  }));
}

function renderReadonlyBlock(block: BlockResponse) {
  if (block.type === "CHECKLIST") {
    return (
      <div className="detail-check-block">
        <input type="checkbox" checked={block.checked ?? false} readOnly />
        <span>{block.content}</span>
      </div>
    );
  }

  if (block.type === "CODE") {
    return <pre className="detail-code-block">{block.content}</pre>;
  }

  return <p className="detail-text-block">{block.content}</p>;
}

export function PageDetailModal({
  pageId,
  currentUser,
  onClose,
  onSaved,
}: PageDetailModalProps) {
  const [page, setPage] = useState<PageResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const [title, setTitle] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [participantsText, setParticipantsText] = useState("");
  const [blocks, setBlocks] = useState<BlockInput[]>([]);

  useEffect(() => {
    let isMounted = true;

    async function loadPage() {
      try {
        setIsLoading(true);
        setErrorMessage("");
        const nextPage = await getPage(pageId);

        if (isMounted) {
          setPage(nextPage);
          setTitle(nextPage.title);
          setStartTime(toTimeInputValue(nextPage.start_time));
          setEndTime(toTimeInputValue(nextPage.end_time));
          setParticipantsText(nextPage.participants.join(", "));
          setBlocks(responseBlocksToInput(nextPage.blocks));
        }
      } catch (error) {
        console.error(error);

        if (isMounted) {
          setErrorMessage("상세 내용을 불러오지 못했습니다.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadPage();

    return () => {
      isMounted = false;
    };
  }, [pageId]);

  const handleBackdropMouseDown = (
    event: React.MouseEvent<HTMLDivElement>
  ) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  const canEdit = Boolean(
    page && currentUser && page.author_id === currentUser.id
  );
  const isMeeting = page?.type === "MEETING";

  const updateBlock = (index: number, nextBlock: Partial<BlockInput>) => {
    setBlocks((prevBlocks) =>
      prevBlocks.map((block, blockIndex) =>
        blockIndex === index ? { ...block, ...nextBlock } : block
      )
    );
  };

  const addBlock = () => {
    setBlocks((prevBlocks) => [
      ...prevBlocks,
      {
        type: "PARAGRAPH",
        content: "",
        checked: null,
      },
    ]);
  };

  const deleteBlock = (index: number) => {
    setBlocks((prevBlocks) =>
      prevBlocks.filter((_, blockIndex) => blockIndex !== index)
    );
  };

  const handleBlockTypeChange = (index: number, type: BlockType) => {
    updateBlock(index, {
      type,
      checked: type === "CHECKLIST" ? false : null,
    });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!page || !canEdit) {
      alert("작성자만 수정할 수 있습니다.");
      return;
    }

    if (!title.trim()) {
      alert("제목을 입력해주세요.");
      return;
    }

    try {
      setIsSubmitting(true);

      const cleanedBlocks = blocks
        .map((block) => ({
          ...block,
          content: block.content.trim(),
        }))
        .filter((block) => block.content.length > 0);

      await updatePage(page.id, {
        title: title.trim(),
        start_time: isMeeting ? normalizeTime(startTime) : null,
        end_time: isMeeting ? normalizeTime(endTime) : null,
        participants: splitCommaText(participantsText),
        blocks: cleanedBlocks,
      });

      onSaved();
    } catch (error: any) {
      console.error(error);

      if (error?.response?.status === 403) {
        alert("작성자만 수정할 수 있습니다.");
        return;
      }

      alert("수정에 실패했습니다. 서버 상태를 확인해주세요.");
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
              {page ? getTypeText(page.type) : "상세"}
            </span>
            <h2>
              {page
                ? `${getTypeText(page.type)} ${canEdit ? "수정" : "상세"}`
                : "기록 상세"}
            </h2>
          </div>

          <button type="button" className="modal-close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </header>

        <div className="page-modal-body">
          {isLoading && <p className="detail-status-text">불러오는 중입니다.</p>}

          {!isLoading && errorMessage && (
            <p className="detail-status-text">{errorMessage}</p>
          )}

          {!isLoading && page && canEdit && (
            <>
              <label className="form-field">
                <span>제목</span>
                <input
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                />
              </label>

              <div className="form-grid">
                <label className="form-field">
                  <span>날짜</span>
                  <input type="date" value={page.date} disabled />
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

              <div className="detail-meta-grid">
                <div>
                  <span>작성자</span>
                  <strong>{page.author.nickname}</strong>
                </div>
              </div>

              <label className="form-field">
                <span>참여자</span>
                <input
                  value={participantsText}
                  onChange={(event) => setParticipantsText(event.target.value)}
                  placeholder="예: 찬빈, 민수, 지영"
                />
              </label>

              <div className="block-editor">
                <div className="block-editor-header">
                  <h3>본문 블록</h3>
                  <button type="button" onClick={addBlock}>
                    + 블록 추가
                  </button>
                </div>

                {blocks.length === 0 && (
                  <p className="block-empty">작성된 블록이 없습니다.</p>
                )}

                <div className="block-list">
                  {blocks.map((block, index) => (
                    <div key={index} className="block-row">
                      <div className="block-row-toolbar">
                        <select
                          value={block.type}
                          onChange={(event) =>
                            handleBlockTypeChange(
                              index,
                              event.target.value as BlockType
                            )
                          }
                        >
                          {BLOCK_TYPES.map((type) => (
                            <option key={type.value} value={type.value}>
                              {type.label}
                            </option>
                          ))}
                        </select>

                        <button
                          type="button"
                          className="block-delete-button"
                          onClick={() => deleteBlock(index)}
                        >
                          삭제
                        </button>
                      </div>

                      {block.type === "CHECKLIST" ? (
                        <div className="check-block-input">
                          <input
                            type="checkbox"
                            checked={block.checked ?? false}
                            onChange={(event) =>
                              updateBlock(index, {
                                checked: event.target.checked,
                              })
                            }
                          />

                          <input
                            value={block.content}
                            placeholder="체크리스트 내용을 입력하세요"
                            onChange={(event) =>
                              updateBlock(index, {
                                content: event.target.value,
                              })
                            }
                          />
                        </div>
                      ) : (
                        <textarea
                          className={block.type === "CODE" ? "code-textarea" : ""}
                          value={block.content}
                          placeholder="내용을 입력하세요"
                          rows={block.type === "HEADING" ? 2 : 4}
                          onChange={(event) =>
                            updateBlock(index, {
                              content: event.target.value,
                            })
                          }
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {!isLoading && page && !canEdit && (
            <>
              <div className="detail-meta-grid">
                <div>
                  <span>날짜</span>
                  <strong>{page.date}</strong>
                </div>

                {isMeeting && (
                  <div>
                    <span>시간</span>
                    <strong>
                      {page.start_time
                        ? `${page.start_time.slice(0, 5)}${
                            page.end_time
                              ? ` - ${page.end_time.slice(0, 5)}`
                              : ""
                          }`
                        : "시간 없음"}
                    </strong>
                  </div>
                )}

                <div>
                  <span>작성자</span>
                  <strong>{page.author.nickname}</strong>
                </div>

                <div>
                  <span>참여자</span>
                  <strong>
                    {page.participants.length > 0
                      ? page.participants.join(", ")
                      : "없음"}
                  </strong>
                </div>
              </div>

              <div className="detail-block-list">
                {page.blocks.length === 0 && (
                  <p className="detail-status-text">작성된 본문이 없습니다.</p>
                )}

                {page.blocks.map((block) => (
                  <article key={block.id} className="detail-block">
                    <div className="detail-block-label">
                      {getBlockTypeText(block.type)}
                    </div>
                    {renderReadonlyBlock(block)}
                  </article>
                ))}
              </div>
            </>
          )}
        </div>

        <footer className="page-modal-footer">
          <button type="button" className="secondary-button" onClick={onClose}>
            닫기
          </button>

          {!isLoading && page && canEdit && (
            <button
              type="submit"
              className="primary-button"
              disabled={isSubmitting}
            >
              {isSubmitting ? "저장 중..." : "저장"}
            </button>
          )}
        </footer>
      </form>
    </div>
  );
}
