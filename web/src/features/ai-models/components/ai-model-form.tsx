import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { FormError, FormField } from "@/components/common/form-field";
import { Spinner } from "@/components/common/spinner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api-client";
import { useCreateAIModel, useUpdateAIModel } from "../hooks";
import { aiModelFormSchema, PROVIDERS, toForm, toRequest, type AIModel, type AIModelForm } from "../types";

const selectClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50";

interface AIModelFormProps {
  /** Có model = chế độ sửa; không có = tạo mới */
  model?: AIModel;
  onDone?: () => void;
}

export function AIModelFormView({ model, onDone }: AIModelFormProps) {
  const isEdit = !!model;
  const create = useCreateAIModel();
  const update = useUpdateAIModel();
  const mutation = isEdit ? update : create;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<AIModelForm>({
    resolver: zodResolver(aiModelFormSchema),
    defaultValues: toForm(model),
  });

  const onSubmit = handleSubmit((values) => {
    const body = toRequest(values);
    const onSuccess = () => {
      reset(toForm());
      onDone?.();
    };
    if (model) {
      // provider/model_name không được PATCH
      const { provider: _provider, model_name: _modelName, ...patch } = body;
      update.mutate({ id: model.id, body: patch }, { onSuccess });
    } else {
      create.mutate(body, { onSuccess });
    }
  });

  const id = (name: string) => `${model?.id ?? "new"}-${name}`;

  return (
    <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2" noValidate>
      <div className="sm:col-span-2">
        <FormError message={mutation.isError ? getErrorMessage(mutation.error) : null} />
      </div>

      <FormField id={id("provider")} label="Provider" error={errors.provider?.message}>
        <select id={id("provider")} className={selectClass} disabled={isEdit} {...register("provider")}>
          {PROVIDERS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </FormField>
      <FormField
        id={id("model_name")}
        label="Model name (ID gửi cho provider)"
        error={errors.model_name?.message}
      >
        <Input
          id={id("model_name")}
          placeholder="vd: gpt-4o-mini, claude-sonnet-4-5, gemini-2.5-flash"
          disabled={isEdit}
          {...register("model_name")}
        />
      </FormField>
      <FormField id={id("display_name")} label="Tên hiển thị" error={errors.display_name?.message}>
        <Input id={id("display_name")} placeholder="vd: GPT-4o mini" {...register("display_name")} />
      </FormField>
      <FormField
        id={id("context_window")}
        label="Context window (token)"
        error={errors.context_window?.message}
      >
        <Input
          id={id("context_window")}
          inputMode="numeric"
          placeholder="Bỏ trống = không giới hạn"
          {...register("context_window")}
        />
      </FormField>
      <div className="sm:col-span-2">
        <FormField
          id={id("capabilities")}
          label="Capabilities (phân cách bằng dấu phẩy)"
          error={errors.capabilities?.message}
        >
          <Input
            id={id("capabilities")}
            placeholder="vd: chat, vision, tools"
            {...register("capabilities")}
          />
        </FormField>
      </div>

      <fieldset className="grid gap-4 rounded-md border p-4 sm:col-span-2 sm:grid-cols-4">
        <legend className="px-1 text-sm font-medium">
          Tham số mặc định (bỏ trống = dùng mặc định của provider)
        </legend>
        <FormField id={id("temperature")} label="Temperature" error={errors.temperature?.message}>
          <Input
            id={id("temperature")}
            inputMode="decimal"
            placeholder="0 – 2"
            {...register("temperature")}
          />
        </FormField>
        <FormField id={id("max_tokens")} label="Max tokens" error={errors.max_tokens?.message}>
          <Input id={id("max_tokens")} inputMode="numeric" {...register("max_tokens")} />
        </FormField>
        <FormField id={id("top_p")} label="Top P" error={errors.top_p?.message}>
          <Input id={id("top_p")} inputMode="decimal" placeholder="0 – 1" {...register("top_p")} />
        </FormField>
        <FormField id={id("stop")} label="Stop (dấu phẩy)" error={errors.stop?.message}>
          <Input id={id("stop")} {...register("stop")} />
        </FormField>
      </fieldset>

      <div className="flex flex-wrap items-center gap-6 sm:col-span-2">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" className="size-4" {...register("is_enabled")} />
          Bật (user được chọn)
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" className="size-4" {...register("is_default")} />
          Model mặc định
        </label>
        {errors.is_default && <p className="text-destructive text-sm">{errors.is_default.message}</p>}
      </div>

      <div className="flex gap-2 sm:col-span-2">
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending && <Spinner />}
          {isEdit ? "Lưu thay đổi" : "Tạo model"}
        </Button>
        {onDone && (
          <Button variant="ghost" onClick={onDone}>
            Huỷ
          </Button>
        )}
      </div>
    </form>
  );
}
