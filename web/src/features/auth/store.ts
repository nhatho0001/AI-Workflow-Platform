import { create } from "zustand";
import { tokenStorage } from "@/lib/token-storage";

interface AuthState {
  isAuthenticated: boolean;
}

export const useAuthStore = create<AuthState>(() => ({
  isAuthenticated: Boolean(tokenStorage.getAccessToken()),
}));

// Đồng bộ với token storage: login/logout, hoặc refresh thất bại (token bị xoá) → tự về trang login
tokenStorage.subscribe((tokens) => {
  useAuthStore.setState({ isAuthenticated: Boolean(tokens) });
});
