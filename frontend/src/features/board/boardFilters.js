import {
  BASIC_BOARD_TYPE,
  PROCEEDINGS_BOARD_TYPE,
  SCHEDULE_BOARD_TYPE,
} from './boardForm'

export const DEFAULT_BOARD_SEARCH_FILTERS = {
  boardTypeFilter: 'all',
  searchKeyword: '',
}

export const BOARD_TYPE_FILTERS = [
  { value: 'all', label: '전체' },
  { value: 'meeting', label: '회의록' },
  { value: 'schedule', label: '일정' },
  { value: 'basic', label: '일반' },
]

export function filterBoards(boards, boardTypeFilter, searchKeyword) {
  // Backend: GET /board/
  // Response item DTO:
  // {
  //   id: number,
  //   board_type: 1 | 2 | 3,
  //   title: string,
  //   content: string,
  //   tag?: string | null,
  //   user_id: number,
  //   created_at: string,
  //   updated_at: string,
  //   schedule_board_detail?: object | null,
  //   proceedings_board_detail?: object | null
  // }
  // 이 필터는 이미 받아온 게시글 목록 DTO를 화면에서만 좁혀 보여준다.
  // 검색어 하나로 title, content, tag를 함께 찾는다.
  const normalizedSearchKeyword = normalizeSearchValue(searchKeyword)

  return boards.filter((board) => {
    if (!matchesBoardType(board, boardTypeFilter)) {
      return false
    }

    if (normalizedSearchKeyword) {
      const haystack = normalizeSearchValue(`${board.title} ${board.content} ${board.tag || ''}`)
      if (!haystack.includes(normalizedSearchKeyword)) {
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
