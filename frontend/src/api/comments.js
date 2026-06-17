import { refreshLogin } from "./auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

class CommentRequestError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "CommentRequestError";
    this.status = status;
  }
}

async function parseCommentErrorMessage(response) {
  const fallbackMessage = "댓글 요청을 처리하지 못했습니다.";

  try {
    const errorData = await response.json();
    return errorData.detail ?? fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

async function requestComment(path, options = {}) {
  let response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (response.status === 401) {
    try {
      await refreshLogin();
      response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });
    } catch {
      throw new CommentRequestError("로그인이 필요해요.", 401);
    }
  }

  if (!response.ok) {
    const errorMessage = await parseCommentErrorMessage(response);
    throw new CommentRequestError(errorMessage, response.status);
  }

  return response.json();
}

export async function getComments(postId) {
  return requestComment(`/posts/${postId}/comments`);
}

export async function createComment(postId, { content }) {
  return requestComment(`/posts/${postId}/comments`, {
    method: "POST",
    body: JSON.stringify({
      content,
    }),
  });
}

export async function deleteComment(commentId) {
  return requestComment(`/comments/${commentId}`, {
    method: "DELETE",
  });
}
