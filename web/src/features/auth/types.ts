import { z } from "zod";

// Khớp với server/app/modules/auth/schemes.py và users/schemas.py:UserRegister
export const loginSchema = z.object({
  email: z.string().email("Email không hợp lệ"),
  password: z.string().min(1, "Vui lòng nhập mật khẩu"),
});
export type LoginRequest = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    name: z.string().min(1, "Vui lòng nhập tên").max(100),
    email: z.string().email("Email không hợp lệ").max(100),
    password: z.string().min(8, "Mật khẩu tối thiểu 8 ký tự"),
    confirmPassword: z.string(),
  })
  .refine((v) => v.password === v.confirmPassword, {
    message: "Mật khẩu xác nhận không khớp",
    path: ["confirmPassword"],
  });
export type RegisterForm = z.infer<typeof registerSchema>;
export type RegisterRequest = Omit<RegisterForm, "confirmPassword">;
