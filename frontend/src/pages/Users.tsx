import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { api } from "../api/client";
import { toastError } from "../api/errors";
import { Badge, Modal, Skeleton } from "../components/ui";
import type { Page } from "../types";

interface UserRow { id: number; username: string; roles: string[]; is_active: boolean }
const ROLES = ["Admin", "Sales User", "Inventory Manager"];

export default function Users() {
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: async () => (await api.get<Page<UserRow>>("/users/")).data.results,
  });
  const patch = useMutation({
    mutationFn: ({ id, body }: { id: number; body: object }) => api.patch(`/users/${id}/`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
    onError: toastError,
  });

  return (
    <div>
      <div className="mb-3 flex items-center">
        <h1 className="mr-auto text-lg font-semibold">Users</h1>
        <button onClick={() => setCreating(true)} className="rounded bg-slate-800 px-3 py-2 text-sm text-white">+ New user</button>
      </div>
      {isLoading ? <Skeleton /> : (
        <div className="overflow-x-auto rounded bg-white shadow">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-100 text-gray-600">
              <tr><th className="p-2">Username</th><th>Role</th><th>Status</th><th className="p-2 text-right">Actions</th></tr>
            </thead>
            <tbody>
              {data?.map((u) => (
                <tr key={u.id} className="border-t">
                  <td className="p-2">{u.username}</td>
                  <td>
                    <select className="rounded border p-1" value={u.roles[0] ?? ""}
                      onChange={(e) => patch.mutate({ id: u.id, body: { role: e.target.value } })}>
                      {!u.roles[0] && <option value="">no role</option>}
                      {ROLES.map((r) => <option key={r}>{r}</option>)}
                    </select>
                  </td>
                  <td><Badge tone={u.is_active ? "green" : "gray"}>{u.is_active ? "Active" : "Inactive"}</Badge></td>
                  <td className="p-2 text-right">
                    <button className="text-red-600"
                      onClick={() => patch.mutate({ id: u.id, body: { is_active: !u.is_active } })}>
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {creating && <NewUser onClose={() => setCreating(false)} />}
    </div>
  );
}

function NewUser({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [f, setF] = useState({ username: "", password: "", role: ROLES[1] });
  const m = useMutation({
    mutationFn: () => api.post("/users/", f),
    onSuccess: () => { toast.success("User created"); qc.invalidateQueries({ queryKey: ["users"] }); onClose(); },
    onError: toastError,
  });
  const submit = (e: FormEvent) => { e.preventDefault(); m.mutate(); };
  return (
    <Modal title="New user" onClose={onClose}>
      <form onSubmit={submit} className="space-y-2">
        <input required className="w-full rounded border p-2" placeholder="Username" value={f.username}
          onChange={(e) => setF({ ...f, username: e.target.value })} />
        <input required type="password" minLength={8} className="w-full rounded border p-2" placeholder="Password (min 8)"
          value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} />
        <select className="w-full rounded border p-2" value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}>
          {ROLES.map((r) => <option key={r}>{r}</option>)}
        </select>
        <button disabled={m.isPending} className="w-full rounded bg-slate-800 py-2 text-white disabled:opacity-50">
          {m.isPending ? "Saving..." : "Create"}
        </button>
      </form>
    </Modal>
  );
}