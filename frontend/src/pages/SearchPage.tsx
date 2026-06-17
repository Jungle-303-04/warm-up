import { LogOut, Search } from "lucide-react";
import type { FormEvent } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { UserResponse } from "../api/auth";
import { searchPages } from "../api/pages";
import { AppLayout } from "../components/layout/AppLayout";
import type { AppPage } from "../components/layout/AppLayout";
import { PageDetailModal } from "../components/modal/PageDetailModal";
import type { PageListItem, PageType } from "../types/page";

type SearchPageProps = {
  currentUser: UserResponse | null;
  onLogout: () => void;
  onNavigate: (page: AppPage) => void;
};

type SearchType = "" | PageType;

const PAGE_SIZE = 10;

function getInitial(nickname: string) {
  return nickname.trim().charAt(0).toUpperCase() || "U";
}

function getTypeLabel(type: PageType) {
  return type === "MEETING" ? "회의" : "회고";
}

function getTypeResultLabel(type: SearchType) {
  if (type === "MEETING") {
    return "회의 기록";
  }

  if (type === "RETROSPECTIVE") {
    return "회고 기록";
  }

  return "전체 기록";
}

function formatDate(value: string) {
  const date = new Date(`${value}T00:00:00`);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

export function SearchPage({
  currentUser,
  onLogout,
  onNavigate,
}: SearchPageProps) {
  const [keyword, setKeyword] = useState("");
  const [selectedType, setSelectedType] = useState<SearchType>("");
  const [items, setItems] = useState<PageListItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPageId, setSelectedPageId] = useState<number | null>(null);

  const nickname = currentUser?.nickname ?? "사용자";
  const initial = getInitial(nickname);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const resultTitle = `${getTypeResultLabel(selectedType)} (${total})`;

  const fetchResults = useCallback(
    async (targetPage = page) => {
      try {
        setIsLoading(true);

        const trimmedKeyword = keyword.trim();
        const data = await searchPages({
          keyword: trimmedKeyword || undefined,
          type: selectedType || undefined,
          page: targetPage,
          size: PAGE_SIZE,
        });

        setItems(data.items);
        setTotal(data.total);
        setPage(data.page);
      } catch (error) {
        console.error(error);
        alert("검색 결과를 불러오지 못했습니다.");
      } finally {
        setIsLoading(false);
      }
    },
    [keyword, page, selectedType]
  );

  useEffect(() => {
    fetchResults(1);
    // 첫 진입 때 전체 목록을 불러오기 위한 효과입니다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const visiblePages = useMemo(() => {
    const start = Math.max(1, page - 4);
    const end = Math.min(totalPages, start + 8);

    return Array.from({ length: end - start + 1 }, (_, index) => start + index);
  }, [page, totalPages]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    fetchResults(1);
  };

  const handleTypeChange = (nextType: SearchType) => {
    setSelectedType(nextType);
    setPage(1);
  };

  const handlePageChange = (nextPage: number) => {
    if (nextPage < 1 || nextPage > totalPages || nextPage === page) {
      return;
    }

    fetchResults(nextPage);
  };

  return (
    <AppLayout
      activePage="search"
      onNavigate={onNavigate}
      topbar={
        <header className="topbar">
          <div>
            <h1 className="topbar-title">검색</h1>
            <p className="topbar-subtitle">
              저장된 회의와 회고를 제목 또는 타입으로 찾아봅니다.
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
      <section className="search-page">
        <form className="search-toolbar" onSubmit={handleSubmit}>
          <div className="search-input-wrap">
            <Search size={18} />
            <input
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="제목 검색어를 입력하세요"
            />
          </div>

          <div className="search-type-tabs" aria-label="검색 타입">
            <button
              className={selectedType === "" ? "active" : ""}
              type="button"
              onClick={() => handleTypeChange("")}
            >
              전체
            </button>
            <button
              className={selectedType === "MEETING" ? "active" : ""}
              type="button"
              onClick={() => handleTypeChange("MEETING")}
            >
              회의
            </button>
            <button
              className={selectedType === "RETROSPECTIVE" ? "active" : ""}
              type="button"
              onClick={() => handleTypeChange("RETROSPECTIVE")}
            >
              회고
            </button>
          </div>

          <button className="search-submit-button" type="submit">
            검색
          </button>
        </form>

        <div className="search-result-panel">
          <div className="search-result-header">
            <h2>{resultTitle}</h2>
            <span>{isLoading ? "불러오는 중" : `페이지 ${page} / ${totalPages}`}</span>
          </div>

          <div className="search-result-table">
            <div className="search-result-row search-result-row-head">
              <span>제목</span>
              <span>타입</span>
              <span>작성자</span>
              <span>날짜</span>
            </div>

            {items.map((item) => (
              <button
                className="search-result-row"
                key={item.id}
                type="button"
                onClick={() => setSelectedPageId(item.id)}
              >
                <span className="search-title-cell">
                  <span className="search-row-dot" />
                  <strong>{item.title}</strong>
                </span>
                <span className={`search-type-badge ${item.type.toLowerCase()}`}>
                  {getTypeLabel(item.type)}
                </span>
                <span>{item.author.nickname}</span>
                <span>{formatDate(item.date)}</span>
              </button>
            ))}

            {!isLoading && items.length === 0 && (
              <p className="search-empty">검색 결과가 없습니다.</p>
            )}
          </div>

          <div className="search-pagination">
            {visiblePages.map((pageNumber) => (
              <button
                className={pageNumber === page ? "active" : ""}
                key={pageNumber}
                type="button"
                onClick={() => handlePageChange(pageNumber)}
              >
                {pageNumber}
              </button>
            ))}

            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => handlePageChange(page + 1)}
            >
              다음
            </button>
          </div>
        </div>
      </section>

      {selectedPageId !== null && (
        <PageDetailModal
          pageId={selectedPageId}
          currentUser={currentUser}
          onClose={() => setSelectedPageId(null)}
          onSaved={() => {
            setSelectedPageId(null);
            fetchResults(page);
          }}
        />
      )}
    </AppLayout>
  );
}
