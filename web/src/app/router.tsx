import { createBrowserRouter, Navigate } from "react-router";
import { LoginPage, RegisterPage } from "@/features/auth";
import { ProfilePage, UsersPage } from "@/features/users";
import { ErrorPage } from "@/pages/error-page";
import { NotFoundPage } from "@/pages/not-found-page";
import { AppLayout } from "./layouts/app-layout";
import { AuthLayout } from "./layouts/auth-layout";
import { GuestRoute, ProtectedRoute, RequireRole } from "./routes/guards";

// auth/users được import tĩnh vì layout + guard luôn cần chúng.
// Feature lớn (chat, sau này workflows/agents...) dùng `lazy` để tách thành chunk riêng.
export const router = createBrowserRouter([
  {
    errorElement: <ErrorPage />,
    children: [
      {
        element: <GuestRoute />,
        children: [
          {
            element: <AuthLayout />,
            children: [
              { path: "/login", element: <LoginPage /> },
              { path: "/register", element: <RegisterPage /> },
            ],
          },
        ],
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { index: true, element: <Navigate to="/chat" replace /> },
              {
                // Một route với param tuỳ chọn để ChatPage không bị remount khi /chat → /chat/:id
                path: "/chat/:conversationId?",
                lazy: () => import("@/features/chat").then((m) => ({ Component: m.ChatPage })),
              },
              { path: "/profile", element: <ProfilePage /> },
              {
                element: <RequireRole roles={["admin"]} />,
                children: [{ path: "/admin/users", element: <UsersPage /> }],
              },
            ],
          },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
