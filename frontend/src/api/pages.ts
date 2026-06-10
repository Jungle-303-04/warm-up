import { api } from "./client";
import type { PageCreateRequest, PageResponse } from "../types/page";

// 새 회의/회고를 백엔드에 저장해주는 함수



// 회의/회고 작성 모달에서 만든 payload를 백엔드 pages 테이블로 저장합니다.
export async function createPage(payload: PageCreateRequest) {
  const response = await api.post<PageResponse>("/pages", payload);
  return response.data;
}
