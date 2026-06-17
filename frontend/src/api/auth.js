const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

class AuthRequestError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "AuthRequestError";
    this.status = status;
  }
}

async function parseErrorMessage(response) {
  const fallbackMessage = "요청을 처리하지 못했습니다.";

  try {
    const errorData = await response.json();
    return errorData.detail ?? fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

async function requestAuth(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorMessage = await parseErrorMessage(response);
    throw new AuthRequestError(errorMessage, response.status);
  }

  return response.json();
}

export async function signupUser({ nickname, password }) {
  return requestAuth("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ nickname, password }),
  });
}

export async function loginUser({ nickname, password }) {
  return requestAuth("/auth/login", {
    method: "POST",
    body: JSON.stringify({ nickname, password }),
  });
}

export async function refreshLogin() {
  return requestAuth("/auth/refresh", {
    method: "POST",
  });
}

export async function getCurrentUser() {
  try {
    return await requestAuth("/auth/me");
  } catch (error) {
    if (error.status === 401 && error.message === "토큰이 만료되었습니다.") {
      return refreshLogin();
    }

    throw error;
  }
}

export async function logoutUser() {
  return requestAuth("/auth/logout", {
    method: "POST",
  });
}
