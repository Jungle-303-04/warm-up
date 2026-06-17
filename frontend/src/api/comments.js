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
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorMessage = await parseCommentErrorMessage(response);
    throw new CommentRequestError(errorMessage, response.status);
  }

  return response.json();
}

export async function getComments(postId) {
  return requestComment(`/posts/${postId}/comments`);
}

export async function createComment(postId, { content, userId }) {
  return requestComment(`/posts/${postId}/comments`, {
    method: "POST",
    body: JSON.stringify({
      content,
      user_id: userId,
    }),
  });
}

export async function deleteComment(commentId) {
  return requestComment(`/comments/${commentId}`, {
    method: "DELETE",
  });
}
