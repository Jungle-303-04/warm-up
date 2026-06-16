import { Edit3, LogOut, MessageSquareText, Send, Trash2, X } from "lucide-react";
import type { FormEvent } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { UserResponse } from "../api/auth";
import {
  createDailyMessage,
  deleteDailyMessage,
  getDailyMessages,
  updateDailyMessage,
} from "../api/dailyMessages";
import { AppLayout } from "../components/layout/AppLayout";
import type { DailyMessage } from "../types/dailyMessage";

type DailyMessagePageProps = {
  currentUser: UserResponse | null;
  onLogout: () => void;
  onNavigate: (page: "calendar" | "daily-message") => void;
};

// 백엔드에서 받은 ISO 날짜 문자열을 한국어 날짜/시간 표시로 바꾼다.
function formatDateTime(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

// 사용자 닉네임의 첫 글자를 동그란 아바타에 표시한다.
function getInitial(nickname: string) {
  return nickname.trim().charAt(0).toUpperCase() || "U";
}

export function DailyMessagePage({
  currentUser,
  onLogout,
  onNavigate,
}: DailyMessagePageProps) {
  // 화면에 보여줄 오늘의 한마디 목록이다.
  const [messages, setMessages] = useState<DailyMessage[]>([]);

  // 새 한마디 작성 textarea의 입력값이다.
  const [content, setContent] = useState("");

  // 현재 수정 모드로 열린 한마디 id다. null이면 수정 중인 글이 없다.
  const [editingId, setEditingId] = useState<number | null>(null);

  // 수정 textarea의 입력값이다.
  const [editingContent, setEditingContent] = useState("");

  // 목록 조회 중인지 표시하기 위한 상태다.
  const [isLoading, setIsLoading] = useState(false);

  // 작성/수정/삭제 요청이 진행 중인지 표시하기 위한 상태다.
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nickname = currentUser?.nickname ?? "사용자";
  const initial = getInitial(nickname);

  const messageCountLabel = useMemo(() => {
    return `전체 ${messages.length}개`;
  }, [messages.length]);

  const fetchMessages = useCallback(async () => {
    try {
      setIsLoading(true);
      // 백엔드에서 최신 한마디 목록을 다시 가져와 화면 상태에 저장한다.
      const data = await getDailyMessages();
      setMessages(data);
    } catch (error) {
      console.error(error);
      alert("오늘의 한마디를 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // 페이지가 처음 열릴 때 한마디 목록을 조회한다.
    fetchMessages();
  }, [fetchMessages]);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedContent = content.trim();
    if (!trimmedContent) {
      alert("한마디를 입력해 주세요.");
      return;
    }

    try {
      setIsSubmitting(true);
      await createDailyMessage({ content: trimmedContent });
      setContent("");
      // 작성 후 DB 기준 최신 목록을 다시 불러온다.
      await fetchMessages();
    } catch (error) {
      console.error(error);
      alert("오늘의 한마디를 등록하지 못했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const startEdit = (message: DailyMessage) => {
    // 연필 버튼을 누르면 해당 글을 수정 모드로 전환한다.
    setEditingId(message.id);
    setEditingContent(message.content);
  };

  const cancelEdit = () => {
    // 수정 모드를 닫고 수정 textarea 값도 비운다.
    setEditingId(null);
    setEditingContent("");
  };

  const handleUpdate = async (messageId: number) => {
    const trimmedContent = editingContent.trim();
    if (!trimmedContent) {
      alert("수정할 내용을 입력해 주세요.");
      return;
    }

    try {
      setIsSubmitting(true);
      await updateDailyMessage(messageId, { content: trimmedContent });
      cancelEdit();
      // 수정 후 DB 기준 최신 목록을 다시 불러온다.
      await fetchMessages();
    } catch (error) {
      console.error(error);
      alert("오늘의 한마디를 수정하지 못했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (messageId: number) => {
    const confirmed = window.confirm("이 한마디를 삭제할까요?");
    if (!confirmed) {
      return;
    }

    try {
      setIsSubmitting(true);
      await deleteDailyMessage(messageId);
      // 삭제 후 DB 기준 최신 목록을 다시 불러온다.
      await fetchMessages();
    } catch (error) {
      console.error(error);
      alert("오늘의 한마디를 삭제하지 못했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppLayout
      activePage="daily-message"
      onNavigate={onNavigate}
      topbar={
        <header className="topbar">
          <div>
            <h1 className="topbar-title">오늘의 한마디</h1>
            <p className="topbar-subtitle">
              팀원들이 가볍게 남기는 짧은 메시지
            </p>
          </div>

          <div className="topbar-actions">
            <div className="user-chip" title={currentUser?.email}>
              <span className="user-chip-avatar">{initial}</span>
              <strong className="user-chip-name">{nickname}</strong>
            </div>

            <button className="logout-button" type="button" onClick={onLogout}>
              <LogOut size={16} />
              <span>로그아웃</span>
            </button>
          </div>
        </header>
      }
    >
      <div className="daily-message-page">
        <section className="daily-message-compose">
          <div className="daily-message-heading">
            <div className="daily-message-heading-icon">
              <MessageSquareText size={22} />
            </div>
            <div>
              <h2>오늘 남길 한마디</h2>
              <p>
                회의/회고와 별개로 팀원들에게 짧게 공유할 말을 남겨보세요.
              </p>
            </div>
          </div>

          <form className="daily-message-form" onSubmit={handleCreate}>
            <textarea
              value={content}
              onChange={(event) => setContent(event.target.value)}
              maxLength={500}
              placeholder="예: 오늘도 구현 화이팅입니다."
            />
            <div className="daily-message-form-footer">
              <span>{content.length}/500</span>
              <button type="submit" disabled={isSubmitting}>
                <Send size={16} />
                등록
              </button>
            </div>
          </form>
        </section>

        <section className="daily-message-list-section">
          <div className="daily-message-list-header">
            <div>
              <h2>팀 한마디</h2>
              <p>{isLoading ? "불러오는 중입니다." : messageCountLabel}</p>
            </div>
          </div>

          <div className="daily-message-list">
            {messages.map((message) => {
              // 현재 로그인한 사용자가 이 글의 작성자인 경우에만 수정/삭제 버튼을 보여준다.
              const isOwner = currentUser?.id === message.author_id;
              const isEditing = editingId === message.id;

              return (
                <article className="daily-message-card" key={message.id}>
                  <div className="daily-message-card-header">
                    <div className="daily-message-author">
                      <span>{getInitial(message.author.nickname)}</span>
                      <div>
                        <strong>{message.author.nickname}</strong>
                        <p>{formatDateTime(message.created_at)}</p>
                      </div>
                    </div>

                    {isOwner && (
                      <div className="daily-message-actions">
                        {isEditing ? (
                          <button type="button" onClick={cancelEdit}>
                            <X size={16} />
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => startEdit(message)}
                          >
                            <Edit3 size={16} />
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => handleDelete(message.id)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    )}
                  </div>

                  {isEditing ? (
                    <div className="daily-message-edit">
                      <textarea
                        value={editingContent}
                        onChange={(event) =>
                          setEditingContent(event.target.value)
                        }
                        maxLength={500}
                      />
                      <div>
                        <span>{editingContent.length}/500</span>
                        <button
                          type="button"
                          disabled={isSubmitting}
                          onClick={() => handleUpdate(message.id)}
                        >
                          저장
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="daily-message-content">{message.content}</p>
                  )}
                </article>
              );
            })}

            {!isLoading && messages.length === 0 && (
              <p className="daily-message-empty">
                아직 등록된 한마디가 없습니다.
              </p>
            )}
          </div>
        </section>
      </div>
    </AppLayout>
  );
}
