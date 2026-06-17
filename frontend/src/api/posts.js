const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

class PostRequestError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "PostRequestError";
    this.status = status;
  }
}

async function parsePostErrorMessage(response) {
  const fallbackMessage = "게시글 요청을 처리하지 못했습니다.";

  try {
    const errorData = await response.json();
    return errorData.detail ?? fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

async function requestPost(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorMessage = await parsePostErrorMessage(response);
    throw new PostRequestError(errorMessage, response.status);
  }

  return response.json();
}

export async function getPosts() {
  return requestPost("/posts");
}

export async function getPost(postId) {
  return requestPost(`/posts/${postId}`);
}

export async function createPost({ title, content, fontId }) {
  return requestPost("/posts", {
    method: "POST",
    body: JSON.stringify({
      title,
      content,
      font_id: fontId,
    }),
  });
}

export async function deletePost(postId) {
  return requestPost(`/posts/${postId}`, {
    method: "DELETE",
  });
}
