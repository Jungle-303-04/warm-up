import {api} from './client';

export type ChatReference = {
  page_id: number;
  title: string;
  date?: string | null;
  chunk_index?: number;
  distance?: number;
};

export type ChatResponse = {
  session_id: number;
  message: string;
  references: ChatReference[];
};

export async function sendChatMessage(params: {
  sessionId: number | null;
  message: string;
}) {
  const response = await api.post<ChatResponse>('/ai/chat', {
    session_id: params.sessionId,
    message: params.message,
  });

  return response.data;
}
