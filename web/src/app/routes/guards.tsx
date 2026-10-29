import { Navigate, Outlet, useLocation } from "react-router";
import { FullPageSpinner } from "@/components/common/spinner";
import { useAuthStore } from "@/features/auth";
import { useCurrentUser, type Role } from "@/features/users";

/** Chỉ cho vào khi đã đăng nhập; nếu chưa thì về /login và nhớ trang đang mở */
export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const location = useLocation();
  const { isLoading } = useCurrentUser();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  if (isLoading) return <FullPageSpinner />;
  return <Outlet />;
}

/** Trang login/register — đã đăng nhập thì chuyển vào app */
export function GuestRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <Navigate to="/" replace /> : <Outlet />;
}

/** Giới hạn theo role, đặt bên trong ProtectedRoute */
export function RequireRole({ roles }: { roles: Role[] }) {
  const { data: user } = useCurrentUser();
  if (!user) return <FullPageSpinner />;
  return roles.includes(user.role) ? <Outlet /> : <Navigate to="/" replace />;
}
