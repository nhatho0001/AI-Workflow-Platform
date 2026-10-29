import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { FormError, FormField } from "@/components/common/form-field";
import { Spinner } from "@/components/common/spinner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api-client";
import { useUpdateUser } from "../hooks";
import { userUpdateSchema, type User, type UserUpdateForm, type UserUpdateRequest } from "../types";

export function ProfileForm({ user }: { user: User }) {
  const update = useUpdateUser();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<UserUpdateForm>({
    resolver: zodResolver(userUpdateSchema),
    defaultValues: { name: user.name, email: user.email, avatar_url: user.avatar_url ?? "", password: "" },
  });

  const onSubmit = handleSubmit((values) => {
    const body: UserUpdateRequest = {
      name: values.name,
      email: values.email,
      avatar_url: values.avatar_url || null,
      ...(values.password ? { password: values.password } : {}),
    };
    update.mutate(
      { id: user.id, body },
      { onSuccess: (u) => reset({ name: u.name, email: u.email, avatar_url: u.avatar_url ?? "", password: "" }) },
    );
  });

  return (
    <form onSubmit={onSubmit} className="grid gap-4" noValidate>
      <FormError message={update.isError ? getErrorMessage(update.error) : null} />
      {update.isSuccess && !isDirty && <p className="text-sm text-muted-foreground">Đã lưu thay đổi.</p>}

      <FormField id="name" label="Họ tên" error={errors.name?.message}>
        <Input id="name" aria-invalid={!!errors.name} {...register("name")} />
      </FormField>
      <FormField id="email" label="Email" error={errors.email?.message}>
        <Input id="email" type="email" aria-invalid={!!errors.email} {...register("email")} />
      </FormField>
      <FormField id="avatar_url" label="Ảnh đại diện (URL)" error={errors.avatar_url?.message}>
        <Input id="avatar_url" placeholder="https://..." {...register("avatar_url")} />
      </FormField>
      <FormField id="password" label="Mật khẩu mới (để trống nếu không đổi)" error={errors.password?.message}>
        <Input id="password" type="password" autoComplete="new-password" {...register("password")} />
      </FormField>

      <div>
        <Button type="submit" disabled={!isDirty || update.isPending}>
          {update.isPending && <Spinner />}
          Lưu thay đổi
        </Button>
      </div>
    </form>
  );
}
