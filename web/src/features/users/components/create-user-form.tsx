import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { FormError, FormField } from "@/components/common/form-field";
import { Spinner } from "@/components/common/spinner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api-client";
import { useCreateUser } from "../hooks";
import { ROLES, STATUSES, userCreateSchema, type UserCreateRequest } from "../types";

const selectClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function CreateUserForm({ onDone }: { onDone?: () => void }) {
  const create = useCreateUser();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UserCreateRequest>({
    resolver: zodResolver(userCreateSchema),
    defaultValues: { role: "user", status: "active" },
  });

  const onSubmit = handleSubmit((values) =>
    create.mutate(values, {
      onSuccess: () => {
        reset();
        onDone?.();
      },
    }),
  );

  return (
    <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2" noValidate>
      <div className="sm:col-span-2">
        <FormError message={create.isError ? getErrorMessage(create.error) : null} />
      </div>
      <FormField id="new-name" label="Họ tên" error={errors.name?.message}>
        <Input id="new-name" {...register("name")} />
      </FormField>
      <FormField id="new-email" label="Email" error={errors.email?.message}>
        <Input id="new-email" type="email" {...register("email")} />
      </FormField>
      <FormField id="new-password" label="Mật khẩu" error={errors.password?.message}>
        <Input id="new-password" type="password" autoComplete="new-password" {...register("password")} />
      </FormField>
      <div className="grid grid-cols-2 gap-4">
        <FormField id="new-role" label="Vai trò">
          <select id="new-role" className={selectClass} {...register("role")}>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </FormField>
        <FormField id="new-status" label="Trạng thái">
          <select id="new-status" className={selectClass} {...register("status")}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </FormField>
      </div>
      <div className="flex gap-2 sm:col-span-2">
        <Button type="submit" disabled={create.isPending}>
          {create.isPending && <Spinner />}
          Tạo user
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
