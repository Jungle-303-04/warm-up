import { api } from "./client";

// 회원가입 요청 때 백엔드로 보내는 값입니다.
export type SignupRequest = {
  email: string;
  password: string;
  nickname: string;
};

// 로그인 요청 때 백엔드로 보내는 값입니다.
export type LoginRequest = {
  email: string;
  password: string;
};

// 백엔드가 돌려주는 사용자 정보 형태입니다.
export type UserResponse = {
  id: number;
  email: string;
  nickname: string;
  created_at: string;
};

// 로그인 성공 시 받는 JWT 응답 형태입니다.
export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
};

// 회원가입 API입니다. 성공하면 생성된 사용자 정보를 반환합니다.
export async function signup(payload: SignupRequest) {
  const response = await api.post<UserResponse>("/auth/signup", payload);
  return response.data;
}

// 로그인 API입니다. 성공하면 access_token을 반환합니다.
export async function login(payload: LoginRequest) {
  const response = await api.post<TokenResponse>("/auth/login", payload);
  return response.data;
}

// 현재 저장된 토큰이 유효한지 확인할 때 사용하는 내 정보 API입니다.
export async function getMe() {
  const response = await api.get<UserResponse>("/auth/me");
  return response.data;
}
