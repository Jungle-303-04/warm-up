import axios from "axios";

// 백엔드 API를 호출할 때 공통으로 사용하는 axios 인스턴스입니다.
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  withCredentials: true,
});

// 백엔드로 요청 보내기 전에 실행
api.interceptors.request.use((config) => {
  // 로그인 성공 후 저장한 JWT를 모든 API 요청에 자동으로 붙입니다.
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// 백엔드에서 401오면 토큰이 만료됐거나 잘못된 거니까 자동으로 로그아웃
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 인증이 필요한 요청에서 401이 오면 저장된 토큰을 지우고 앱 전체를 로그아웃시킵니다.
    const status = error.response?.status;
    const requestUrl = error.config?.url ?? "";

    // 로그인/회원가입 실패는 화면에서 직접 처리해야 하므로 강제 로그아웃 대상에서 제외합니다.
    const isAuthRequest =
      requestUrl.includes("/auth/login") || requestUrl.includes("/auth/signup");

    if (status === 401 && !isAuthRequest) {
      localStorage.removeItem("access_token");
      window.dispatchEvent(new Event("auth:logout"));
    }

    return Promise.reject(error);
  }
);
