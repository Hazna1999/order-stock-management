import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { api } from "../api/client";
import { toastError } from "../api/errors";
import type { Customer, Order, Page, Product } from "../types";

interface Line { product: number; quantity: number }

export default function OrderBuilder() {
  const navigate = useNavigate();
  const [customer, setCustomer] = useState("");
  const [lines, setLines] = useState<Line[]>([{ product: 0, quantity: 1 }]);

  const customers = useQuery({
    queryKey: ["customers", "active"],
    queryFn: async () => (await api.get<Page<Customer>>("/customers/", { params: { is_active: true } })).data.results,
  });
  const products = useQuery({
    queryKey: ["products", "all-active"],
    queryFn: async () => (await api.get<Page<Product>>("/products/", { params: { is_active: true, page_size: 100 } })).data.results,
  });

  const byId = new Map(products.data?.map((p) => [p.id, p]));
  const lineTotal = (l: Line) => (Number(byId.get(l.product)?.unit_price ?? 0) * l.quantity);
  const total = lines.reduce((s, l) => s + lineTotal(l), 0);

  const update = (i: number, patch: Partial<Line>) =>
    setLines(lines.map((l, idx) => (idx === i ? { ...l, ...patch } : l)));

  const create = useMutation({
    mutationFn: () => api.post<Order>("/orders/", {
      customer: Number(customer),
      items: lines.filter((l) => l.product).map((l) => ({ product: l.product, quantity: l.quantity })),
    }),
    onSuccess: ({ data }) => { toast.success(`Created ${data.order_number}`); navigate(`/orders/${data.id}`); },
    onError: toastError,
  });

  const used = new Set(lines.map((l) => l.product));
  const valid = customer && lines.some((l) => l.product) && lines.every((l) => !l.product || l.quantity >= 1);

  return (
    <div className="max-w-3xl space-y-4">
      <h1 className="text-lg font-semibold">New order</h1>
      <select className="w-full rounded border p-2" value={customer} onChange={(e) => setCustomer(e.target.value)}>
        <option value="">Select customer...</option>
        {customers.data?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>

      <div className="space-y-2 rounded bg-white p-3 shadow">
        {lines.map((l, i) => (
          <div key={i} className="flex flex-wrap items-center gap-2">
            <select className="min-w-48 flex-1 rounded border p-2 text-sm" value={l.product}
              onChange={(e) => update(i, { product: Number(e.target.value) })}>
              <option value={0}>Select product...</option>
              {products.data?.map((p) => (
                <option key={p.id} value={p.id} disabled={used.has(p.id) && l.product !== p.id}>
                  {p.sku} - {p.name} (stock {p.stock_quantity})
                </option>
              ))}
            </select>
            <input type="number" min={1} className="w-20 rounded border p-2 text-sm" value={l.quantity}
              onChange={(e) => update(i, { quantity: Math.max(1, Number(e.target.value) || 1) })} />
            <span className="w-20 text-right text-sm text-gray-600">@ {byId.get(l.product)?.unit_price ?? "-"}</span>
            <span className="w-24 text-right text-sm font-medium">{lineTotal(l).toFixed(2)}</span>
            <button onClick={() => setLines(lines.filter((_, idx) => idx !== i))} disabled={lines.length === 1}
              className="text-red-600 disabled:opacity-30">✕</button>
          </div>
        ))}
        <button onClick={() => setLines([...lines, { product: 0, quantity: 1 }])} className="text-sm text-blue-600">+ Add item</button>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-lg font-semibold">Total: {total.toFixed(2)}</div>
        <button disabled={!valid || create.isPending} onClick={() => create.mutate()}
          className="rounded bg-slate-800 px-4 py-2 text-white disabled:opacity-50">
          {create.isPending ? "Creating..." : "Create draft order"}
        </button>
      </div>
    </div>
  );
}