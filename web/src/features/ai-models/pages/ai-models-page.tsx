import { ChevronLeft, ChevronRight, Pencil, Plus, Power, PowerOff, Star } from "lucide-react";
import { useState } from "react";
import { FormError } from "@/components/common/form-field";
import { Spinner } from "@/components/common/spinner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getErrorMessage } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { AIModelFormView } from "../components/ai-model-form";
import { useAdminAIModels, useDisableAIModel, useUpdateAIModel } from "../hooks";
import type { AIModel } from "../types";

const PAGE_SIZE = 20;

function Badge({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", className)}>
      {children}
    </span>
  );
}

function formatParams(model: AIModel) {
  const p = model.default_params;
  if (!p) return "—";
  return Object.entries(p)
    .map(([k, v]) => `${k}=${Array.isArray(v) ? v.join("|") : v}`)
    .join(", ");
}

export function AIModelsPage() {
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<AIModel | null>(null);

  const { data: models, isLoading, isFetching, error } = useAdminAIModels({ page, page_size: PAGE_SIZE });
  const update = useUpdateAIModel();
  const disable = useDisableAIModel();

  const actionError = update.error ?? disable.error;
  const busy = update.isPending || disable.isPending;
  const hasNext = (models?.length ?? 0) === PAGE_SIZE;

  return (
    <div className="mx-auto grid w-full max-w-6xl gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Quản lý AI models</h1>
          <p className="text-muted-foreground text-sm">Danh mục model mà platform được phép dùng cho chat.</p>
        </div>
        {!showCreate && !editing && (
          <Button onClick={() => setShowCreate(true)}>
            <Plus /> Thêm model
          </Button>
        )}
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Model mới</CardTitle>
          </CardHeader>
          <CardContent>
            <AIModelFormView onDone={() => setShowCreate(false)} />
          </CardContent>
        </Card>
      )}

      {editing && (
        <Card>
          <CardHeader>
            <CardTitle>
              Sửa: {editing.display_name}{" "}
              <span className="text-muted-foreground font-mono text-sm font-normal">
                ({editing.provider}/{editing.model_name})
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* key để form reset khi chuyển sang sửa model khác */}
            <AIModelFormView key={editing.id} model={editing} onDone={() => setEditing(null)} />
          </CardContent>
        </Card>
      )}

      <FormError
        message={error ? getErrorMessage(error) : actionError ? getErrorMessage(actionError) : null}
      />

      <Card className="py-0">
        {isLoading ? (
          <div className="flex justify-center p-8">
            <Spinner />
          </div>
        ) : !models?.length ? (
          <p className="text-muted-foreground p-8 text-center text-sm">
            {page === 1 ? "Chưa có model nào. Bấm “Thêm model” để tạo." : "Không còn model nào ở trang này."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-muted-foreground border-b text-left">
                <tr>
                  <th className="px-4 py-3 font-medium">Model</th>
                  <th className="px-4 py-3 font-medium">Provider</th>
                  <th className="px-4 py-3 font-medium">Context</th>
                  <th className="px-4 py-3 font-medium">Capabilities</th>
                  <th className="px-4 py-3 font-medium">Tham số mặc định</th>
                  <th className="px-4 py-3 font-medium">Trạng thái</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr
                    key={m.id}
                    className={cn("border-b last:border-0", !m.is_enabled && "text-muted-foreground")}
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium">{m.display_name}</div>
                      <div className="text-muted-foreground font-mono text-xs">{m.model_name}</div>
                    </td>
                    <td className="px-4 py-3">{m.provider}</td>
                    <td className="px-4 py-3">{m.context_window?.toLocaleString("vi-VN") ?? "—"}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {m.capabilities.length
                          ? m.capabilities.map((c) => (
                              <Badge key={c} className="bg-secondary text-secondary-foreground">
                                {c}
                              </Badge>
                            ))
                          : "—"}
                      </div>
                    </td>
                    <td className="max-w-48 truncate px-4 py-3 font-mono text-xs" title={formatParams(m)}>
                      {formatParams(m)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {m.is_enabled ? (
                          <Badge className="bg-green-500/15 text-green-700 dark:text-green-400">Bật</Badge>
                        ) : (
                          <Badge className="bg-muted text-muted-foreground">Tắt</Badge>
                        )}
                        {m.is_default && (
                          <Badge className="bg-amber-500/15 text-amber-700 dark:text-amber-400">
                            Mặc định
                          </Badge>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Đặt làm mặc định"
                          aria-label={`Đặt ${m.display_name} làm mặc định`}
                          disabled={busy || m.is_default || !m.is_enabled}
                          onClick={() => update.mutate({ id: m.id, body: { is_default: true } })}
                        >
                          <Star className={cn(m.is_default && "fill-current text-amber-500")} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Sửa"
                          aria-label={`Sửa ${m.display_name}`}
                          onClick={() => {
                            setShowCreate(false);
                            setEditing(m);
                          }}
                        >
                          <Pencil />
                        </Button>
                        {m.is_enabled ? (
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Tắt model"
                            aria-label={`Tắt ${m.display_name}`}
                            disabled={busy}
                            onClick={() => {
                              if (
                                window.confirm(
                                  `Tắt model ${m.display_name}? User sẽ không chọn được model này nữa.`,
                                )
                              )
                                disable.mutate(m.id);
                            }}
                          >
                            <PowerOff />
                          </Button>
                        ) : (
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Bật lại model"
                            aria-label={`Bật ${m.display_name}`}
                            disabled={busy}
                            onClick={() => update.mutate({ id: m.id, body: { is_enabled: true } })}
                          >
                            <Power />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {(page > 1 || hasNext) && (
        <div className="flex items-center justify-end gap-2 text-sm">
          {isFetching && <Spinner />}
          <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
            <ChevronLeft /> Trước
          </Button>
          <span className="px-2">Trang {page}</span>
          <Button variant="outline" size="sm" disabled={!hasNext} onClick={() => setPage((p) => p + 1)}>
            Sau <ChevronRight />
          </Button>
        </div>
      )}
    </div>
  );
}
