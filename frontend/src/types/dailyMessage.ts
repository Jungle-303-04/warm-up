import type { PageAuthor } from "./page";

// 백엔드에서 받아오는 오늘의 한마디 한 건의 데이터 모양이다.
export type DailyMessage = {
  id: number;
  author_id: number;
  // 작성자 닉네임과 이메일을 화면에 보여주기 위해 author 객체를 함께 받는다.
  author: PageAuthor;
  content: string;
  created_at: string;
  updated_at: string;
};

// 새 한마디를 작성할 때 백엔드로 보내는 요청 데이터다.
export type DailyMessageCreateRequest = {
  content: string;
};

// 기존 한마디를 수정할 때 백엔드로 보내는 요청 데이터다.
export type DailyMessageUpdateRequest = {
  content: string;
};
