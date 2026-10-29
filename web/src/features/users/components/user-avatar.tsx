import { cn } from "@/lib/utils";
import type { User } from "../types";

export function UserAvatar({ user, className }: { user: Pick<User, "name" | "avatar_url">; className?: string }) {
  const initials = user.name
    .split(" ")
    .filter(Boolean)
    .slice(-2)
    .map((w) => w[0]?.toUpperCase())
    .join("");

  return user.avatar_url ? (
    <img src={user.avatar_url} alt={user.name} className={cn("size-8 rounded-full object-cover", className)} />
  ) : (
    <span
      className={cn(
        "inline-flex size-8 items-center justify-center rounded-full bg-secondary text-xs font-medium",
        className,
      )}
    >
      {initials || "?"}
    </span>
  );
}
