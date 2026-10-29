import { Workflow } from "lucide-react";
import { Outlet } from "react-router";

export function AuthLayout() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-6 bg-muted p-6">
      <div className="flex items-center gap-2 text-lg font-semibold">
        <Workflow className="size-6" /> AI Workflow Platform
      </div>
      <div className="w-full max-w-sm">
        <Outlet />
      </div>
    </div>
  );
}
