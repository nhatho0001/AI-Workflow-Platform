import { MessageSquare, Users, type LucideIcon } from "lucide-react";
import type { Role } from "@/features/users";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  /** Chỉ hiển thị cho các role này; bỏ trống = mọi user đã đăng nhập */
  roles?: Role[];
}

// Thêm feature mới (Workflows, Agents, Knowledge Base...) → thêm một dòng ở đây + một route trong router.tsx
export const NAV_ITEMS: NavItem[] = [
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/admin/users", label: "Người dùng", icon: Users, roles: ["admin"] },
];
