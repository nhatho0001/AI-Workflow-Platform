import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { FormError, FormField } from "@/components/common/form-field";
import { Spinner } from "@/components/common/spinner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api-client";
import { useLogin } from "../hooks";
import { loginSchema, type LoginRequest } from "../types";

export function LoginForm({ onSuccess }: { onSuccess?: () => void }) {
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginRequest>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit((values) => login.mutate(values, { onSuccess }));

  return (
    <form onSubmit={onSubmit} className="grid gap-4" noValidate>
      <FormError message={login.isError ? getErrorMessage(login.error) : null} />

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
          autoComplete="current-password"
          aria-invalid={!!errors.password}
          {...register("password")}
        />
      </FormField>

      <Button type="submit" disabled={login.isPending}>
        {login.isPending && <Spinner />}
        Đăng nhập
      </Button>
    </form>
  );
}
