import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/features/auth";
import { usersApi } from "./api";
import type { UserUpdateRequest } from "./types";

// Query keys tập trung một chỗ để invalidate chính xác
export const userKeys = {
  all: ["users"] as const,
  me: () => [...userKeys.all, "me"] as const,
  list: (params: { skip?: number; limit?: number }) => [...userKeys.all, "list", params] as const,
};

export function useCurrentUser() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery({
    queryKey: userKeys.me(),
    queryFn: usersApi.me,
    enabled: isAuthenticated,
    staleTime: 5 * 60_000,
  });
}

export function useUsers(params: { skip?: number; limit?: number } = {}) {
  return useQuery({ queryKey: userKeys.list(params), queryFn: () => usersApi.list(params) });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.all }),
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UserUpdateRequest }) => usersApi.update(id, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.all }),
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: usersApi.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.all }),
  });
}
