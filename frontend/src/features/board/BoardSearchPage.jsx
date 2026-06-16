import { useMemo, useState } from 'react'

import {
  BOARD_TYPE_FILTERS,
  DEFAULT_BOARD_SEARCH_FILTERS,
  filterBoards,
} from './boardFilters'
import { formatDateTime, getBoardTypeLabel } from './boardForm'

export function BoardSearchPage({
  boards,
  initialFilters = DEFAULT_BOARD_SEARCH_FILTERS,
  onBack,
  onOpenBoard,
}) {
  const [boardTypeFilter, setBoardTypeFilter] = useState(
    initialFilters.boardTypeFilter || DEFAULT_BOARD_SEARCH_FILTERS.boardTypeFilter,
  )
  const [searchKeyword, setSearchKeyword] = useState(
    initialFilters.searchKeyword || DEFAULT_BOARD_SEARCH_FILTERS.searchKeyword,
  )
  const [sortOrder, setSortOrder] = useState('newest')
  const filteredBoards = useMemo(
    () => sortBoards(filterBoards(boards, boardTypeFilter, searchKeyword), sortOrder),
    [boards, boardTypeFilter, searchKeyword, sortOrder],
  )
  const hasSearchKeyword = searchKeyword.trim().length > 0
  const hasTypeFilter = boardTypeFilter !== DEFAULT_BOARD_SEARCH_FILTERS.boardTypeFilter
  const resultLabel = buildResultLabel({
    hasSearchKeyword,
    hasTypeFilter,
    count: filteredBoards.length,
    totalCount: boards.length,
  })

  return (
    <section className="board-search-page" aria-labelledby="board-search-title">
      <div className="board-detail-toolbar">
        <button type="button" className="secondary-button compact" onClick={onBack}>
          메인으로
        </button>
        <strong>{resultLabel}</strong>
      </div>

      <header className="board-detail-header">
        <div className="board-search-heading-row">
          <div>
            <h2 id="board-search-title">게시글 목록</h2>
          </div>
          <label className="board-search-box">
            <span className="visually-hidden">게시글 검색</span>
            <IconSearch />
            <input
              type="search"
              value={searchKeyword}
              onChange={(event) => setSearchKeyword(event.target.value)}
              placeholder="제목, 내용, 태그"
            />
          </label>
        </div>
      </header>

      <div className="board-list-controls">
        <fieldset className="calendar-type-filter board-type-tabs" aria-label="게시글 유형 필터">
          {BOARD_TYPE_FILTERS.map((filter) => (
            <label key={filter.value}>
              <input
                type="radio"
                name="board-search-type"
                value={filter.value}
                checked={boardTypeFilter === filter.value}
                onChange={(event) => setBoardTypeFilter(event.target.value)}
              />
              <span>{filter.label}</span>
            </label>
          ))}
        </fieldset>

        <button
          type="button"
          className="board-sort-button"
          onClick={() => setSortOrder((current) => (
            current === 'newest' ? 'oldest' : 'newest'
          ))}
        >
          {sortOrder === 'newest' ? '최신순' : '오래된순'}
        </button>
      </div>

      {filteredBoards.length ? (
        <ul className="board-search-list">
          {filteredBoards.map((board) => (
            <li key={board.id}>
              <button type="button" onClick={() => onOpenBoard(board.id)}>
                <span className="board-search-type">
                  {getBoardTypeLabel(board.board_type)}
                </span>
                <strong>{board.title}</strong>
                <p>{buildBoardExcerpt(board.content)}</p>
                <dl className="board-search-meta" aria-label={`${board.title} 게시글 정보`}>
                  <div>
                    <dt>작성자</dt>
                    <dd>{board.user_id}</dd>
                  </div>
                  <div>
                    <dt>작성일</dt>
                    <dd>{formatDateTime(board.created_at)}</dd>
                  </div>
                  <div>
                    <dt>태그</dt>
                    <dd>{board.tag ? `#${board.tag}` : '-'}</dd>
                  </div>
                </dl>
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="calendar-empty">조건에 맞는 게시글이 없습니다.</p>
      )}
    </section>
  )
}

function buildBoardExcerpt(content) {
  const normalizedContent = content.trim().replace(/\s+/g, ' ')

  if (normalizedContent.length <= 120) {
    return normalizedContent
  }

  return `${normalizedContent.slice(0, 120)}...`
}

function buildResultLabel({ hasSearchKeyword, hasTypeFilter, count, totalCount }) {
  if (hasSearchKeyword) {
    return `검색 결과 ${count}개`
  }

  if (hasTypeFilter) {
    return `필터 결과 ${count}개`
  }

  return `전체 게시글 ${totalCount}개`
}

function sortBoards(boards, sortOrder) {
  return [...boards].sort((left, right) => {
    const leftTime = new Date(left.created_at).getTime() || 0
    const rightTime = new Date(right.created_at).getTime() || 0

    return sortOrder === 'newest' ? rightTime - leftTime : leftTime - rightTime
  })
}

function IconSearch() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="11" cy="11" r="6" />
      <path d="m16 16 4 4" />
    </svg>
  )
}
