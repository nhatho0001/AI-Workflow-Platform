// Đọc biến môi trường một chỗ duy nhất — code khác không truy cập import.meta.env trực tiếp
export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
  defaultModelId: import.meta.env.VITE_DEFAULT_MODEL_ID ?? "00000000-0000-0000-0000-000000000001",
} as const;
