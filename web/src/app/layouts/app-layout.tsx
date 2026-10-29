import { LogOut, Workflow } from "lucide-react";
import { Link, NavLink, Outlet } from "react-router";
import { Button } from "@/components/ui/button";
import { useLogout } from "@/features/auth";
import { UserAvatar, useCurrentUser } from "@/features/users";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "../navigation";

export function AppLayout() {
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  const navItems = NAV_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  return (
    <div className="flex h-dvh">
      <aside className="flex w-16 shrink-0 flex-col items-center gap-2 border-r bg-muted/40 py-3">
        <Link to="/" className="mb-2 rounded-md p-2" aria-label="Trang chủ">
          <Workflow className="size-6" />
        </Link>

        <nav className="flex flex-1 flex-col gap-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              title={label}
              aria-label={label}
              className={({ isActive }) =>
                cn(
                  "rounded-md p-2.5 text-muted-foreground hover:bg-accent hover:text-foreground",
                  isActive && "bg-accent text-foreground",
                )
              }
            >
              <Icon className="size-5" />
            </NavLink>
          ))}
        </nav>

        {user && (
          <Link to="/profile" title={user.name} aria-label="Hồ sơ">
            <UserAvatar user={user} />
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          title="Đăng xuất"
          aria-label="Đăng xuất"
          disabled={logout.isPending}
          onClick={() => logout.mutate()}
        >
          <LogOut />
        </Button>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
