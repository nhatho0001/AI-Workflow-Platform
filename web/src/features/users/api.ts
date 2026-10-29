import { apiClient } from "@/lib/api-client";
import type { User, UserCreateRequest, UserUpdateRequest } from "./types";

export const usersApi = {
  me: () => apiClient.get<User>("/users/me").then((r) => r.data),

  list: (params: { skip?: number; limit?: number } = {}) =>
    apiClient.get<User[]>("/users/", { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<User>(`/users/${id}`).then((r) => r.data),

  create: (body: UserCreateRequest) => apiClient.post<User>("/users/create", body).then((r) => r.data),

  update: (id: string, body: UserUpdateRequest) =>
    apiClient.patch<User>(`/users/update/${id}`, body).then((r) => r.data),

  remove: (id: string) => apiClient.delete<void>(`/users/delete/${id}`).then(() => undefined),
};
