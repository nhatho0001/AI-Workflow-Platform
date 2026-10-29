import { MessageSquarePlus, Pin, PinOff, Trash2 } from "lucide-react";
import { Link, NavLink, useNavigate } from "react-router";
import { Spinner } from "@/components/common/spinner";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useConversations, useDeleteConversation, useTogglePin } from "../hooks";
import type { Conversation } from "../types";

export function ConversationSidebar({ activeId }: { activeId?: string }) {
  const navigate = useNavigate();
  const { data, isLoading } = useConversations({ page_size: 50 });
  const togglePin = useTogglePin();
  const deleteConversation = useDeleteConversation();

  const conversations = [...(data?.items ?? [])].sort(
    (a, b) => Number(b.is_pinned) - Number(a.is_pinned) || b.updated_at.localeCompare(a.updated_at),
  );

  const handleDelete = (c: Conversation) => {
    if (!window.confirm(`Xoá cuộc trò chuyện "${c.title || "Không tiêu đề"}"?`)) return;
    deleteConversation.mutate(c.id, {
      onSuccess: () => {
        if (c.id === activeId) navigate("/chat");
      },
    });
  };

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r">
      <div className="p-3">
        <Link to="/chat" className={cn(buttonVariants({ variant: "outline" }), "w-full justify-start")}>
          <MessageSquarePlus /> Cuộc trò chuyện mới
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 pb-3">
        {isLoading && (
          <div className="flex justify-center p-4">
            <Spinner />
          </div>
        )}
        {!isLoading && conversations.length === 0 && (
          <p className="px-2 py-4 text-sm text-muted-foreground">Chưa có cuộc trò chuyện nào.</p>
        )}
        <ul className="grid gap-0.5">
          {conversations.map((c) => (
            <li key={c.id} className="group relative">
              <NavLink
                to={`/chat/${c.id}`}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 truncate rounded-md px-2 py-2 pr-16 text-sm hover:bg-accent",
                    isActive && "bg-accent font-medium",
                  )
                }
              >
                {c.is_pinned && <Pin className="size-3 shrink-0 text-muted-foreground" />}
                <span className="truncate">{c.title || "Không tiêu đề"}</span>
              </NavLink>
              <div className="absolute top-1/2 right-1 hidden -translate-y-1/2 gap-0.5 group-focus-within:flex group-hover:flex">
                <button
                  type="button"
                  className="rounded p-1 text-muted-foreground hover:bg-background hover:text-foreground"
                  aria-label={c.is_pinned ? "Bỏ ghim" : "Ghim"}
                  onClick={() => togglePin.mutate(c.id)}
                >
                  {c.is_pinned ? <PinOff className="size-3.5" /> : <Pin className="size-3.5" />}
                </button>
                <button
                  type="button"
                  className="rounded p-1 text-muted-foreground hover:bg-background hover:text-destructive"
                  aria-label="Xoá"
                  onClick={() => handleDelete(c)}
                >
                  <Trash2 className="size-3.5" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
