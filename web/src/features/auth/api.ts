import { apiClient } from "@/lib/api-client";
import type { TokenPair } from "@/lib/token-storage";
import type { LoginRequest, RegisterRequest } from "./types";

export const authApi = {
  login: (body: LoginRequest) => apiClient.post<TokenPair>("/auth/login", body).then((r) => r.data),

  register: (body: RegisterRequest) => apiClient.post<TokenPair>("/auth/register", body).then((r) => r.data),

  logout: (refreshToken: string) =>
    apiClient.post<{ message: string }>("/auth/logout", { refresh_token: refreshToken }).then((r) => r.data),
};
