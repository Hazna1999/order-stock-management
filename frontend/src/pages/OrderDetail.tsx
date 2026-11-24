import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { api } from "../api/client";
import { toastError } from "../api/errors";
import { useAuth } from "../auth/AuthContext";
import { Skeleton, StatusBadge } from "../components/ui";
import type { HistoryRow, Order, OrderStatus, Role } from "../types";

type Action = "confirm" | "ship" | "deliver" | "cancel";

const ACTIONS: { action: Action; label: string; from: OrderStatus[]; to: OrderStatus; roles: Role[]; danger?: boolean }[] = [
  { action: "confirm", label: "Confirm", from: ["DRAFT"], to: "CONFIRMED", roles: ["Admin", "Sales User"] },
  { action: "ship", label: "Ship", from: ["CONFIRMED"], to: "SHIPPED", roles: ["Admin", "Inventory Manager"] },
  { action: "deliver", label: "Deliver", from: ["SHIPPED"], to: "DELIVERED", roles: ["Admin"] },
  { action: "cancel", label: "Cancel", from: ["DRAFT", "CONFIRMED"], to: "CANCELLED", roles: ["Admin", "Sales User"], danger: true },
];

export default function OrderDetail() {
  const { id } = useParams();
  const { hasRole } = useAuth();
  const qc = useQueryClient();
  const key = ["order", id];

  const order = useQuery({ queryKey: key, queryFn: async () => (await api.get<Order>(`/orders/${id}/`)).data });
  const history = useQuery({
    queryKey: ["order-history", id],
    queryFn: async () => (await api.get<HistoryRow[]>(`/orders/${id}/history/`)).data,
  });

  const run = useMutation({
    mutationFn: async ({ action }: { action: Action; to: OrderStatus }) =>
      (await api.post<Order>(`/orders/${id}/${action}/`)).data,
    onMutate: async ({ to }) => {
      await qc.cancelQueries({ queryKey: key });
      const previous = qc.getQueryData<Order>(key);
      if (previous) qc.setQueryData<Order>(key, { ...previous, status: to });
      return { previous };
    },
    onError: (err, _vars, ctx) => {
      if (ctx?.previous) qc.setQueryData(key, ctx.previous);
      toastError(err);
    },
    onSuccess: (data) => { qc.setQueryData(key, data); toast.success(`Order is now ${data.status}`); },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["order-history", id] });
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["products"] });
    },
  });

  if (order.isLoading) return <Skeleton rows={6} />;
  if (order.isError || !order.data) return <div className="text-red-600">Order not found.</div>;
  const o = order.data;

  return (
    <div className="space-y-4">
      <Link to="/orders" className="text-sm text-blue-600">← Orders</Link>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-lg font-semibold">{o.order_number}</h1>
        <StatusBadge status={o.status} />
        <span className="text-sm text-gray-600">{o.customer_name}</span>
        <div className="ml-auto flex gap-2">
          {ACTIONS.filter((a) => hasRole(...a.roles)).map((a) => (
            <button key={a.action} disabled={!a.from.includes(o.status) || run.isPending}
              onClick={() => run.mutate({ action: a.action, to: a.to })}
              className={`rounded px-3 py-1.5 text-sm text-white disabled:opacity-30 ${a.danger ? "bg-red-600" : "bg-slate-800"}`}>
              {a.label}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto rounded bg-white shadow">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-100 text-gray-600">
            <tr><th className="p-2">SKU</th><th>Product</th><th className="text-right">Qty</th>
              <th className="text-right">Unit price</th><th className="p-2 text-right">Line total</th></tr>
          </thead>
          <tbody>
            {o.lines.map((l) => (
              <tr key={l.id} className="border-t">
                <td className="p-2 font-mono">{l.product_sku}</td><td>{l.product_name}</td>
                <td className="text-right">{l.quantity}</td><td className="text-right">{l.unit_price}</td>
                <td className="p-2 text-right">{l.line_total}</td>
              </tr>
            ))}
            <tr className="border-t font-semibold"><td colSpan={4} className="p-2 text-right">Total</td><td className="p-2 text-right">{o.total_amount}</td></tr>
          </tbody>
        </table>
      </div>

      <div className="rounded bg-white p-4 shadow">
        <h2 className="mb-2 font-semibold">Audit trail</h2>
        {history.isLoading ? <Skeleton rows={3} /> : (
          <ul className="space-y-1 text-sm">
            {history.data?.map((h) => (
              <li key={h.id}>
                <span className="font-medium capitalize">{h.action}</span>
                {h.from_status && <> ({h.from_status} → {h.to_status})</>} by {h.performed_by} at {new Date(h.performed_at).toLocaleString()}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}