import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { FormError } from "@/components/common/form-field";
import { Spinner } from "@/components/common/spinner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getErrorMessage } from "@/lib/api-client";
import { CreateUserForm } from "../components/create-user-form";
import { UserAvatar } from "../components/user-avatar";
import { useCurrentUser, useDeleteUser, useUsers } from "../hooks";

export function UsersPage() {
  const [showCreate, setShowCreate] = useState(false);
  const { data: me } = useCurrentUser();
  const { data: users, isLoading, error } = useUsers();
  const deleteUser = useDeleteUser();

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Quản lý người dùng</h1>
        {!showCreate && (
          <Button onClick={() => setShowCreate(true)}>
            <Plus /> Thêm user
          </Button>
        )}
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>User mới</CardTitle>
          </CardHeader>
          <CardContent>
            <CreateUserForm onDone={() => setShowCreate(false)} />
          </CardContent>
        </Card>
      )}

      <FormError message={error ? getErrorMessage(error) : deleteUser.error ? getErrorMessage(deleteUser.error) : null} />

      <Card className="py-0">
        {isLoading ? (
          <div className="flex justify-center p-8">
            <Spinner />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b text-left text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Người dùng</th>
                  <th className="px-4 py-3 font-medium">Vai trò</th>
                  <th className="px-4 py-3 font-medium">Trạng thái</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {users?.map((u) => (
                  <tr key={u.id} className="border-b last:border-0">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <UserAvatar user={u} />
                        <div>
                          <div className="font-medium">{u.name}</div>
                          <div className="text-muted-foreground">{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">{u.role}</td>
                    <td className="px-4 py-3">{u.status}</td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Xoá ${u.name}`}
                        disabled={u.id === me?.id || deleteUser.isPending}
                        onClick={() => {
                          if (window.confirm(`Xoá user ${u.email}?`)) deleteUser.mutate(u.id);
                        }}
                      >
                        <Trash2 />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
