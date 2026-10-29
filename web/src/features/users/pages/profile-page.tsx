import { FullPageSpinner } from "@/components/common/spinner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProfileForm } from "../components/profile-form";
import { UserAvatar } from "../components/user-avatar";
import { useCurrentUser } from "../hooks";

export function ProfilePage() {
  const { data: user, isLoading } = useCurrentUser();
  if (isLoading || !user) return <FullPageSpinner />;

  return (
    <div className="mx-auto w-full max-w-2xl p-6">
      <Card>
        <CardHeader className="flex-row items-center gap-4">
          <UserAvatar user={user} className="size-12 text-base" />
          <div className="grid gap-1">
            <CardTitle>{user.name}</CardTitle>
            <CardDescription>
              {user.email} · {user.role}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <ProfileForm user={user} />
        </CardContent>
      </Card>
    </div>
  );
}
