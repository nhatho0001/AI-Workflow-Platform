import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { FormError, FormField } from "@/components/common/form-field";
import { Spinner } from "@/components/common/spinner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api-client";
import { useRegister } from "../hooks";
import { registerSchema, type RegisterForm as RegisterFormValues } from "../types";

export function RegisterForm({ onSuccess }: { onSuccess?: () => void }) {
  const registerMutation = useRegister();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  const onSubmit = handleSubmit(({ confirmPassword: _, ...body }) =>
    registerMutation.mutate(body, { onSuccess }),
  );

  return (
    <form onSubmit={onSubmit} className="grid gap-4" noValidate>
      <FormError message={registerMutation.isError ? getErrorMessage(registerMutation.error) : null} />

      <FormField id="name" label="Họ tên" error={errors.name?.message}>
        <Input id="name" autoComplete="name" aria-invalid={!!errors.name} {...register("name")} />
      </FormField>

      <FormField id="email" label="Email" error={errors.email?.message}>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          aria-invalid={!!errors.email}
          {...register("email")}
        />
      </FormField>

      <FormField id="password" label="Mật khẩu" error={errors.password?.message}>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          aria-invalid={!!errors.password}
          {...register("password")}
        />
      </FormField>

      <FormField id="confirmPassword" label="Xác nhận mật khẩu" error={errors.confirmPassword?.message}>
        <Input
          id="confirmPassword"
          type="password"
          autoComplete="new-password"
          aria-invalid={!!errors.confirmPassword}
          {...register("confirmPassword")}
        />
      </FormField>

      <Button type="submit" disabled={registerMutation.isPending}>
        {registerMutation.isPending && <Spinner />}
        Tạo tài khoản
      </Button>
    </form>
  );
}
