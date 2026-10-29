import { Link } from "react-router";
import { buttonVariants } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 text-center">
      <p className="text-5xl font-semibold">404</p>
      <p className="text-muted-foreground">Không tìm thấy trang bạn yêu cầu.</p>
      <Link to="/" className={buttonVariants({ variant: "outline" })}>
        Về trang chủ
      </Link>
    </div>
  );
}
