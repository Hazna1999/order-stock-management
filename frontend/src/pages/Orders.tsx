import { useState } from "react";
import { Link } from "react-router-dom";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Pager, Skeleton, StatusBadge } from "../components/ui";
import type { Order, Page } from "../types";

const STATUSES = ["DRAFT", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"];

export default function Orders() {
  const { hasRole } = useAuth();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [page, setPage] = useState(1);

  const params = { search, status, date_from: from, date_to: to, page };
  const { data, isLoading } = useQuery({
    queryKey: ["orders", params],
    queryFn: async () => (await api.get<Page<Order>>("/orders/", { params })).data,
    placeholderData: keepPreviousData,
  });
  const reset = <T,>(set: (v: T) => void) => (v: T) => { set(v); setPage(1); };

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h1 className="mr-auto text-lg font-semibold">Orders</h1>
        <input className="rounded border p-2 text-sm" placeholder="Order no, customer, email" value={search}
          onChange={(e) => reset(setSearch)(e.target.value)} />
        <select className="rounded border p-2 text-sm" value={status} onChange={(e) => reset(setStatus)(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <input type="date" className="rounded border p-2 text-sm" value={from} onChange={(e) => reset(setFrom)(e.target.value)} />
        <input type="date" className="rounded border p-2 text-sm" value={to} onChange={(e) => reset(setTo)(e.target.value)} />
        {hasRole("Admin", "Sales User") && (
          <Link to="/orders/new" className="rounded bg-slate-800 px-3 py-2 text-sm text-white">+ New order</Link>
        )}
      </div>
      {isLoading ? <Skeleton /> : (
        <div className="overflow-x-auto rounded bg-white shadow">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-100 text-gray-600">
              <tr><th className="p-2">Order</th><th>Customer</th><th>Date</th><th>Status</th><th className="p-2 text-right">Total</th></tr>
            </thead>
            <tbody>
              {data?.results.map((o) => (
                <tr key={o.id} className="border-t hover:bg-gray-50">
                  <td className="p-2"><Link className="text-blue-600" to={`/orders/${o.id}`}>{o.order_number}</Link></td>
                  <td>{o.customer_name}</td>
                  <td>{new Date(o.order_date).toLocaleDateString()}</td>
                  <td><StatusBadge status={o.status} /></td>
                  <td className="p-2 text-right">{o.total_amount}</td>
                </tr>
              ))}
              {data?.results.length === 0 && <tr><td colSpan={5} className="p-4 text-center text-gray-500">No orders</td></tr>}
            </tbody>
          </table>
        </div>
      )}
      {data && <Pager page={page} count={data.count} onChange={setPage} />}
    </div>
  );
}