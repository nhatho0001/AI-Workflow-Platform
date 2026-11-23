// Đọc biến môi trường một chỗ duy nhất — code khác không truy cập import.meta.env trực tiếp
export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
} as const;
