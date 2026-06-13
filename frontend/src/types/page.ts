// 페이지는 현재 회의록과 회고 두 종류를 지원합니다.
export type PageType = "MEETING" | "RETROSPECTIVE";

// 페이지 본문은 여러 블록으로 구성되고, 각 블록은 아래 타입 중 하나입니다.
export type BlockType =
  | "PARAGRAPH"
  | "HEADING"
  | "BULLET"
  | "CHECKLIST"
  | "CODE";

// 캘린더 화면에서 월별 목록을 그릴 때 필요한 최소 페이지 정보입니다.
export type CalendarPageItem = {
  id: number;
  type: PageType;
  title: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
};

// 작성 모달에서 입력하는 본문 블록 하나의 형태입니다.
export type BlockInput = {
  type: BlockType;
  content: string;
  checked: boolean | null;
};

// 새 페이지를 만들 때 백엔드로 보내는 요청 형태입니다.
export type PageCreateRequest = {
  type: PageType;
  title: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  participants: string[];
  blocks: BlockInput[];
};

// 페이지 생성 후 백엔드가 돌려주는 저장 결과입니다.
export type PageResponse = {
  id: number;
  type: PageType;
  title: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  author_id: number;
  participants: string[];
  ai_summary: string | null;
  created_at: string;
  updated_at: string;
};
