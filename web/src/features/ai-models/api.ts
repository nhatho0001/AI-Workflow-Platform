import { apiClient } from "@/lib/api-client";
import type {
  AIModel,
  AIModelCreateRequest,
  AIModelListParams,
  AIModelPublic,
  AIModelUpdateRequest,
} from "./types";

export const aiModelsApi = {
  /** Model đang bật — mọi user đã đăng nhập */
  listEnabled: () => apiClient.get<AIModelPublic[]>("/ai-models").then((r) => r.data),

  /** Tất cả model (kể cả đã tắt) — admin, có phân trang */
  listAll: (params: AIModelListParams) =>
    apiClient.get<AIModel[]>("/ai-models/admin", { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<AIModel>(`/ai-models/${id}`).then((r) => r.data),

  create: (body: AIModelCreateRequest) => apiClient.post<AIModel>("/ai-models", body).then((r) => r.data),

  update: (id: string, body: AIModelUpdateRequest) =>
    apiClient.patch<AIModel>(`/ai-models/${id}`, body).then((r) => r.data),

  /** Soft delete: server chỉ đặt is_enabled=false (và bỏ default) */
  disable: (id: string) => apiClient.delete<void>(`/ai-models/${id}`).then(() => undefined),
};
