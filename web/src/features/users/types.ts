import { z } from "zod";

// Khớp với server/app/modules/users/models.py (Role, Status) và schemas.py
export type Role = "admin" | "seller" | "buyer" | "user";
export type UserStatus = "active" | "inactive" | "pending";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  status: UserStatus;
  avatar_url: string | null;
}

export const ROLES: Role[] = ["admin", "seller", "buyer", "user"];
export const STATUSES: UserStatus[] = ["active", "inactive", "pending"];

export const userUpdateSchema = z.object({
  name: z.string().min(1, "Vui lòng nhập tên").max(100),
  email: z.string().email("Email không hợp lệ").max(100),
  avatar_url: z.union([z.string().url("URL không hợp lệ").max(255), z.literal("")]),
  password: z.union([z.string().min(8, "Mật khẩu tối thiểu 8 ký tự"), z.literal("")]),
});
export type UserUpdateForm = z.infer<typeof userUpdateSchema>;
export type UserUpdateRequest = Partial<{
  name: string;
  email: string;
  avatar_url: string | null;
  password: string;
}>;

export const userCreateSchema = z.object({
  name: z.string().min(1, "Vui lòng nhập tên").max(100),
  email: z.string().email("Email không hợp lệ").max(100),
  password: z.string().min(8, "Mật khẩu tối thiểu 8 ký tự"),
  role: z.enum(["admin", "seller", "buyer", "user"]),
  status: z.enum(["active", "inactive", "pending"]),
});
export type UserCreateRequest = z.infer<typeof userCreateSchema>;
