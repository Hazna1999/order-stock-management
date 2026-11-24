import { useState, type FormEvent } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { api } from "../api/client";
import { toastError } from "../api/errors";
import { Badge, Modal, Pager, Skeleton } from "../components/ui";
import type { Customer, Page } from "../types";

export default function Customers() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Customer | "new" | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["customers", search, page],
    queryFn: async () => (await api.get<Page<Customer>>("/customers/", { params: { search, page } })).data,
    placeholderData: keepPreviousData,
  });

  const toggle = useMutation({
    mutationFn: (c: Customer) => api.patch(`/customers/${c.id}/`, { is_active: !c.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["customers"] }),
    onError: toastError,
  });

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h1 className="mr-auto text-lg font-semibold">Customers</h1>
        <input className="rounded border p-2 text-sm" placeholder="Search name or email" value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        <button onClick={() => setEditing("new")} className="rounded bg-slate-800 px-3 py-2 text-sm text-white">+ New</button>
      </div>
      {isLoading ? <Skeleton /> : (
        <div className="overflow-x-auto rounded bg-white shadow">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-100 text-gray-600">
              <tr><th className="p-2">Name</th><th>Email</th><th>Phone</th><th>Status</th><th className="p-2 text-right">Actions</th></tr>
            </thead>
            <tbody>
              {data?.results.map((c) => (
                <tr key={c.id} className="border-t">
                  <td className="p-2">{c.name}</td><td>{c.email}</td><td>{c.phone}</td>
                  <td><Badge tone={c.is_active ? "green" : "gray"}>{c.is_active ? "Active" : "Inactive"}</Badge></td>
                  <td className="space-x-2 p-2 text-right">
                    <button onClick={() => setEditing(c)} className="text-blue-600">Edit</button>
                    <button onClick={() => toggle.mutate(c)} className="text-red-600">{c.is_active ? "Deactivate" : "Activate"}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && <Pager page={page} count={data.count} onChange={setPage} />}
      {editing && <CustomerForm customer={editing === "new" ? null : editing} onClose={() => setEditing(null)} />}
    </div>
  );
}

function CustomerForm({ customer, onClose }: { customer: Customer | null; onClose: () => void }) {
  const qc = useQueryClient();
  const [f, setF] = useState({
    name: customer?.name ?? "", email: customer?.email ?? "",
    phone: customer?.phone ?? "", billing_address: customer?.billing_address ?? "",
  });
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const m = useMutation({
    mutationFn: () => customer ? api.patch(`/customers/${customer.id}/`, f) : api.post("/customers/", f),
    onSuccess: () => { toast.success("Saved"); qc.invalidateQueries({ queryKey: ["customers"] }); onClose(); },
    onError: toastError,
  });
  const submit = (e: FormEvent) => { e.preventDefault(); m.mutate(); };
  return (
    <Modal title={customer ? "Edit customer" : "New customer"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-2">
        <input required className="w-full rounded border p-2" placeholder="Name" value={f.name} onChange={set("name")} />
        <input required type="email" className="w-full rounded border p-2" placeholder="Email" value={f.email} onChange={set("email")} />
        <input className="w-full rounded border p-2" placeholder="Phone" value={f.phone} onChange={set("phone")} />
        <input className="w-full rounded border p-2" placeholder="Billing address" value={f.billing_address} onChange={set("billing_address")} />
        <button disabled={m.isPending} className="w-full rounded bg-slate-800 py-2 text-white disabled:opacity-50">
          {m.isPending ? "Saving..." : "Save"}
        </button>
      </form>
    </Modal>
  );
}