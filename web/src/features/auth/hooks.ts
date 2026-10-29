import { useMutation, useQueryClient } from "@tanstack/react-query";
import { tokenStorage } from "@/lib/token-storage";
import { authApi } from "./api";

export function useLogin() {
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (tokens) => tokenStorage.set(tokens),
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (tokens) => tokenStorage.set(tokens),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const refreshToken = tokenStorage.getRefreshToken();
      // Thu hồi refresh token phía server; lỗi (vd. access token hết hạn) vẫn đăng xuất local
      if (refreshToken) await authApi.logout(refreshToken).catch(() => undefined);
    },
    onSettled: () => {
      tokenStorage.clear();
      queryClient.clear();
    },
  });
}
