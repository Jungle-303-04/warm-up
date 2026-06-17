const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

class RecommendationRequestError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "RecommendationRequestError";
    this.status = status;
  }
}

async function parseRecommendationErrorMessage(response) {
  const fallbackMessage = "폰트 추천을 처리하지 못했습니다.";

  try {
    const errorData = await response.json();
    return errorData.detail ?? fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

async function requestRecommendation(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorMessage = await parseRecommendationErrorMessage(response);
    throw new RecommendationRequestError(errorMessage, response.status);
  }

  return response.json();
}

export async function recommendFont({ text, preferredTone }) {
  return requestRecommendation("/recommend", {
    method: "POST",
    body: JSON.stringify({
      text,
      preferred_tone: preferredTone ?? null,
    }),
  });
}
