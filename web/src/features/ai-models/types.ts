import { z } from "zod";

// Khớp với server/app/modules/ai_models/models.py (AIModelProvider) và schemas.py
export const PROVIDERS = ["openai", "anthropic", "gemini", "openrouter", "ollama"] as const;
export type AIModelProvider = (typeof PROVIDERS)[number];

export interface ModelParams {
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  stop?: string[];
}

/** AIModelResponse — bản đầy đủ cho admin */
export interface AIModel {
  id: string;
  provider: AIModelProvider;
  model_name: string;
  display_name: string;
  default_params: ModelParams | null;
  context_window: number | null;
  capabilities: string[];
  is_enabled: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

/** AIModelPublic — GET /ai-models cho user thường (chỉ model đang bật) */
export type AIModelPublic = Pick<AIModel, "id" | "provider" | "display_name" | "capabilities" | "is_default">;

export interface AIModelCreateRequest {
  provider: AIModelProvider;
  model_name: string;
  display_name: string;
  default_params: ModelParams | null;
  context_window: number | null;
  capabilities: string[];
  is_enabled: boolean;
  is_default: boolean;
}

/** PATCH: provider/model_name không sửa được — muốn đổi thì tạo bản ghi mới */
export type AIModelUpdateRequest = Partial<Omit<AIModelCreateRequest, "provider" | "model_name">>;

export interface AIModelListParams {
  page: number;
  page_size: number;
}

// ── Form ───────────────────────────────────────────────
// Ô số để dạng string để "bỏ trống" = không đặt; chuyển sang number trong toRequest()

const optionalNumber = (check: (n: number) => boolean, message: string) =>
  z
    .string()
    .trim()
    .refine((v) => v === "" || (!Number.isNaN(Number(v)) && check(Number(v))), message);

export const aiModelFormSchema = z
  .object({
    provider: z.enum(PROVIDERS),
    model_name: z.string().trim().min(1, "Vui lòng nhập model name").max(255),
    display_name: z.string().trim().min(1, "Vui lòng nhập tên hiển thị").max(255),
    context_window: optionalNumber((n) => Number.isInteger(n) && n > 0, "Phải là số nguyên > 0"),
    capabilities: z.string(),
    temperature: optionalNumber((n) => n >= 0 && n <= 2, "Trong khoảng 0 – 2"),
    max_tokens: optionalNumber((n) => Number.isInteger(n) && n > 0, "Phải là số nguyên > 0"),
    top_p: optionalNumber((n) => n >= 0 && n <= 1, "Trong khoảng 0 – 1"),
    stop: z.string(),
    is_enabled: z.boolean(),
    is_default: z.boolean(),
  })
  .refine((v) => !v.is_default || v.is_enabled, {
    message: "Model mặc định phải đang bật",
    path: ["is_default"],
  });
export type AIModelForm = z.infer<typeof aiModelFormSchema>;

const splitList = (value: string) =>
  value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

const toNumberOrUndefined = (value: string) => (value.trim() === "" ? undefined : Number(value));

export function toRequest(form: AIModelForm): AIModelCreateRequest {
  const params: ModelParams = {
    temperature: toNumberOrUndefined(form.temperature),
    max_tokens: toNumberOrUndefined(form.max_tokens),
    top_p: toNumberOrUndefined(form.top_p),
    stop: splitList(form.stop),
  };
  if (!params.stop?.length) delete params.stop;
  const cleaned = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined),
  ) as ModelParams;

  return {
    provider: form.provider,
    model_name: form.model_name.trim(),
    display_name: form.display_name.trim(),
    default_params: Object.keys(cleaned).length ? cleaned : null,
    context_window: toNumberOrUndefined(form.context_window) ?? null,
    capabilities: splitList(form.capabilities),
    is_enabled: form.is_enabled,
    is_default: form.is_default,
  };
}

export function toForm(model?: AIModel): AIModelForm {
  const p = model?.default_params ?? {};
  return {
    provider: model?.provider ?? "openai",
    model_name: model?.model_name ?? "",
    display_name: model?.display_name ?? "",
    context_window: model?.context_window?.toString() ?? "",
    capabilities: model?.capabilities.join(", ") ?? "",
    temperature: p.temperature?.toString() ?? "",
    max_tokens: p.max_tokens?.toString() ?? "",
    top_p: p.top_p?.toString() ?? "",
    stop: p.stop?.join(", ") ?? "",
    is_enabled: model?.is_enabled ?? true,
    is_default: model?.is_default ?? false,
  };
}
