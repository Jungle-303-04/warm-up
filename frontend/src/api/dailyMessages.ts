import { api } from "./client";
import type {
  DailyMessage,
  DailyMessageCreateRequest,
  DailyMessageUpdateRequest,
} from "../types/dailyMessage";

// 오늘의 한마디 전체 목록을 가져온다.
export async function getDailyMessages() {
  const response = await api.get<DailyMessage[]>("/daily-messages");
  return response.data;
}

// 새 한마디를 작성한다. 작성자 정보는 백엔드가 JWT 토큰으로 판단한다.
export async function createDailyMessage(payload: DailyMessageCreateRequest) {
  const response = await api.post<DailyMessage>("/daily-messages", payload);
  return response.data;
}

// 작성자 본인이 기존 한마디 내용을 수정한다.
export async function updateDailyMessage(
  messageId: number,
  payload: DailyMessageUpdateRequest
) {
  const response = await api.patch<DailyMessage>(
    `/daily-messages/${messageId}`,
    payload
  );
  return response.data;
}

// 작성자 본인이 기존 한마디를 삭제한다.
export async function deleteDailyMessage(messageId: number) {
  await api.delete(`/daily-messages/${messageId}`);
}
