import { useState, type FormEvent } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { api } from "../api/client";
import { toastError } from "../api/errors";
import { useAuth } from "../auth/AuthContext";
import { Badge, Modal, Pager, Skeleton } from "../components/ui";
import type { Page, Product } from "../types";

export default function Products() {
  const { hasRole } = useAuth();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [active, setActive] = useState("");
  const [page, setPage] = useState(1);
  const [adjusting, setAdjusting] = useState<Product | null>(null);
  const [editing, setEditing] = useState<Product | "new" | null>(null);

  const params = { search, category, is_active: active, page };
  const { data, isLoading } = useQuery({
    queryKey: ["products", params],
    queryFn: async () => (await api.get<Page<Product>>("/products/", { params })).data,
    placeholderData: keepPreviousData,
  });
  const { data: categories } = useQuery({
    queryKey: ["product-categories"],
    queryFn: async () => (await api.get<string[]>("/products/categories/")).data,
  });

  const deactivate = useMutation({
    mutationFn: (id: number) => api.post(`/products/${id}/deactivate/`),
    onSuccess: () => { toast.success("Product deactivated"); qc.invalidateQueries({ queryKey: ["products"] }); },
    onError: toastError,
  });

  const isAdmin = hasRole("Admin");
  const canAdjust = hasRole("Admin", "Inventory Manager");

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h1 className="mr-auto text-lg font-semibold">Products</h1>
        <input className="rounded border p-2 text-sm" placeholder="Search name or SKU" value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        <select className="rounded border p-2 text-sm" value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1); }}>
          <option value="">All categories</option>
          {categories?.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        {isAdmin && (
          <select className="rounded border p-2 text-sm" value={active}
            onChange={(e) => { setActive(e.target.value); setPage(1); }}>
            <option value="">All</option><option value="true">Active</option><option value="false">Inactive</option>
          </select>
        )}
        {isAdmin && <button onClick={() => setEditing("new")} className="rounded bg-slate-800 px-3 py-2 text-sm text-white">+ New</button>}
      </div>

      {isLoading ? <Skeleton /> : (
        <div className="overflow-x-auto rounded bg-white shadow">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-100 text-gray-600">
              <tr><th className="p-2">SKU</th><th>Name</th><th>Category</th><th className="text-right">Price</th>
                <th className="text-right">Stock</th><th>Status</th><th className="p-2 text-right">Actions</th></tr>
            </thead>
            <tbody>
              {data?.results.map((p) => (
                <tr key={p.id} className="border-t">
                  <td className="p-2 font-mono">{p.sku}</td><td>{p.name}</td><td>{p.category}</td>
                  <td className="text-right">{p.unit_price}</td>
                  <td className="text-right">
                    {p.stock_quantity} {p.stock_quantity <= p.reorder_level && <Badge tone="amber">Low</Badge>}
                  </td>
                  <td><Badge tone={p.is_active ? "green" : "gray"}>{p.is_active ? "Active" : "Inactive"}</Badge></td>
                  <td className="space-x-2 p-2 text-right">
                    {canAdjust && <button onClick={() => setAdjusting(p)} className="text-blue-600">Adjust</button>}
                    {isAdmin && <button onClick={() => setEditing(p)} className="text-blue-600">Edit</button>}
                    {isAdmin && p.is_active && (
                      <button onClick={() => deactivate.mutate(p.id)} className="text-red-600">Deactivate</button>
                    )}
                  </td>
                </tr>
              ))}
              {data?.results.length === 0 && <tr><td colSpan={7} className="p-4 text-center text-gray-500">No products</td></tr>}
            </tbody>
          </table>
        </div>
      )}
      {data && <Pager page={page} count={data.count} onChange={setPage} />}
      {adjusting && <AdjustModal product={adjusting} onClose={() => setAdjusting(null)} />}
      {editing && <ProductForm product={editing === "new" ? null : editing} onClose={() => setEditing(null)} />}
    </div>
  );
}

function AdjustModal({ product, onClose }: { product: Product; onClose: () => void }) {
  const qc = useQueryClient();
  const [change, setChange] = useState("");
  const [reason, setReason] = useState("");
  const m = useMutation({
    mutationFn: () => api.post(`/products/${product.id}/adjust-stock/`, { change_quantity: Number(change), reason }),
    onSuccess: () => { toast.success("Stock adjusted"); qc.invalidateQueries({ queryKey: ["products"] }); onClose(); },
    onError: toastError,
  });
  const submit = (e: FormEvent) => { e.preventDefault(); m.mutate(); };
  return (
    <Modal title={`Adjust stock: ${product.sku} (now ${product.stock_quantity})`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <input type="number" step={1} required className="w-full rounded border p-2" placeholder="Change (+ adds, - removes)"
          value={change} onChange={(e) => setChange(e.target.value)} />
        <input required className="w-full rounded border p-2" placeholder="Reason" value={reason}
          onChange={(e) => setReason(e.target.value)} />
        <button disabled={m.isPending} className="w-full rounded bg-slate-800 py-2 text-white disabled:opacity-50">
          {m.isPending ? "Saving..." : "Apply"}
        </button>
      </form>
    </Modal>
  );
}

function ProductForm({ product, onClose }: { product: Product | null; onClose: () => void }) {
  const qc = useQueryClient();
  const [f, setF] = useState({
    name: product?.name ?? "", sku: product?.sku ?? "", category: product?.category ?? "",
    description: product?.description ?? "", unit_price: product?.unit_price ?? "",
    stock_quantity: String(product?.stock_quantity ?? 0), reorder_level: String(product?.reorder_level ?? 0),
  });
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const m = useMutation({
    mutationFn: () => {
      const body: Record<string, unknown> = {
        name: f.name, sku: f.sku, category: f.category, description: f.description,
        unit_price: f.unit_price, reorder_level: Number(f.reorder_level),
      };
      if (!product) body.stock_quantity = Number(f.stock_quantity);
      return product ? api.patch(`/products/${product.id}/`, body) : api.post("/products/", body);
    },
    onSuccess: () => { toast.success("Saved"); qc.invalidateQueries({ queryKey: ["products"] }); onClose(); },
    onError: toastError,
  });
  const submit = (e: FormEvent) => { e.preventDefault(); m.mutate(); };
  return (
    <Modal title={product ? "Edit product" : "New product"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-2">
        <input required className="w-full rounded border p-2" placeholder="Name" value={f.name} onChange={set("name")} />
        <input required className="w-full rounded border p-2" placeholder="SKU" value={f.sku} onChange={set("sku")} />
        <input className="w-full rounded border p-2" placeholder="Category" value={f.category} onChange={set("category")} />
        <input className="w-full rounded border p-2" placeholder="Description" value={f.description} onChange={set("description")} />
        <input required type="number" step="0.01" min="0.01" className="w-full rounded border p-2" placeholder="Unit price"
          value={f.unit_price} onChange={set("unit_price")} />
        {!product && <input type="number" min="0" className="w-full rounded border p-2" placeholder="Opening stock"
          value={f.stock_quantity} onChange={set("stock_quantity")} />}
        <input type="number" min="0" className="w-full rounded border p-2" placeholder="Reorder level"
          value={f.reorder_level} onChange={set("reorder_level")} />
        <button disabled={m.isPending} className="w-full rounded bg-slate-800 py-2 text-white disabled:opacity-50">
          {m.isPending ? "Saving..." : "Save"}
        </button>
      </form>
    </Modal>
  );
}