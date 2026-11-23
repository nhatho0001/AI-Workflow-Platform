import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { aiModelsApi } from "./api";
import type { AIModelListParams, AIModelUpdateRequest } from "./types";

export const aiModelKeys = {
  all: ["ai-models"] as const,
  enabled: () => [...aiModelKeys.all, "enabled"] as const,
  adminList: (params: AIModelListParams) => [...aiModelKeys.all, "admin", params] as const,
};

export function useEnabledAIModels() {
  return useQuery({
    queryKey: aiModelKeys.enabled(),
    queryFn: aiModelsApi.listEnabled,
    staleTime: 5 * 60_000,
  });
}

export function useAdminAIModels(params: AIModelListParams) {
  return useQuery({
    queryKey: aiModelKeys.adminList(params),
    queryFn: () => aiModelsApi.listAll(params),
    placeholderData: keepPreviousData,
  });
}

// Mọi mutation invalidate cả danh sách admin lẫn danh sách public (đổi default/bật-tắt ảnh hưởng cả hai)
export function useCreateAIModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: aiModelsApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: aiModelKeys.all }),
  });
}

export function useUpdateAIModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AIModelUpdateRequest }) => aiModelsApi.update(id, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: aiModelKeys.all }),
  });
}

export function useDisableAIModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: aiModelsApi.disable,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: aiModelKeys.all }),
  });
}
