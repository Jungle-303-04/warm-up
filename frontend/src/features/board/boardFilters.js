import {
  BASIC_BOARD_TYPE,
  PROCEEDINGS_BOARD_TYPE,
  SCHEDULE_BOARD_TYPE,
  getBoardTagLabel,
  getBoardTags,
  normalizeBoardTag,
} from './boardForm'

export const DEFAULT_BOARD_SEARCH_FILTERS = {
  boardTypeFilter: 'all',
  searchKeyword: '',
  tagFilter: '',
}

export const BOARD_TYPE_FILTERS = [
  { value: 'all', label: '전체' },
  { value: 'meeting', label: '회의록' },
  { value: 'schedule', label: '일정' },
  { value: 'basic', label: '일반' },
]

export function filterBoards(boards, boardTypeFilter, searchKeyword, tagFilter = '') {
  // Backend: GET /board/
  // Response item DTO:
  // {
  //   id: number,
  //   board_type: 1 | 2 | 3,
  //   title: string,
  //   content: string,
  //   tag?: string | null, // "#기획 #회의"처럼 #으로 구분된 복수 태그 문자열
  //   user_id: number,
  //   author_display_name?: string | null,
  //   author_login?: string | null,
  //   author_name?: string | null,
  //   created_at: string,
  //   updated_at: string,
  //   schedule_board_detail?: object | null,
  //   proceedings_board_detail?: object | null
  // }
  // 이 필터는 이미 받아온 게시글 목록 DTO를 화면에서만 좁혀 보여준다.
  // 검색어는 title, content, 작성자 표시 이름, 태그 문자열을 모두 찾고,
  // tagFilter는 태그 칩 클릭으로 들어온 정확한 태그 일치만 처리한다.
  const normalizedSearchKeyword = normalizeSearchValue(searchKeyword)
  const normalizedTagSearchKeyword = normalizeBoardTag(searchKeyword).toLowerCase()
  const normalizedTagFilter = normalizeBoardTag(tagFilter).toLowerCase()

  return boards.filter((board) => {
    if (!matchesBoardType(board, boardTypeFilter)) {
      return false
    }

    if (
      normalizedTagFilter
      && !getBoardTags(board).some(
        (tag) => normalizeBoardTag(tag).toLowerCase() === normalizedTagFilter,
      )
    ) {
      return false
    }

    if (normalizedSearchKeyword) {
      const tags = getBoardTags(board)
      const tagText = tags.join(' ')
      const haystack = normalizeSearchValue(
        `${board.title} ${board.content} `
        + `${board.author_display_name || ''} ${board.author_login || ''} ${board.author_name || ''} `
        + `${tagText} ${tags.map(getBoardTagLabel).join(' ')}`,
      )
      const hasMatchingTag = normalizedTagSearchKeyword
        && tags.some((tag) => normalizeBoardTag(tag).toLowerCase().includes(normalizedTagSearchKeyword))

      if (!haystack.includes(normalizedSearchKeyword) && !hasMatchingTag) {
        return false
      }
    }

    return true
  })
}

function matchesBoardType(board, boardTypeFilter) {
  if (boardTypeFilter === 'all') {
    return true
  }

  if (boardTypeFilter === 'basic') {
    return board.board_type === BASIC_BOARD_TYPE
  }

  if (boardTypeFilter === 'schedule') {
    return board.board_type === SCHEDULE_BOARD_TYPE
  }

  return board.board_type === PROCEEDINGS_BOARD_TYPE
}

function normalizeSearchValue(value) {
  return value.trim().toLowerCase()
}
