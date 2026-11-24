import type { ReactNode } from "react";

export function Skeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-9 animate-pulse rounded bg-gray-200" />
      ))}
    </div>
  );
}

export function Badge({ children, tone }: { children: ReactNode; tone: "green" | "gray" | "red" | "blue" | "amber" }) {
  const colors = {
    green: "bg-green-100 text-green-800", gray: "bg-gray-200 text-gray-700",
    red: "bg-red-100 text-red-800", blue: "bg-blue-100 text-blue-800", amber: "bg-amber-100 text-amber-800",
  };
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${colors[tone]}`}>{children}</span>;
}

export function Pager({ page, count, pageSize = 20, onChange }:
  { page: number; count: number; pageSize?: number; onChange: (p: number) => void }) {
  const pages = Math.max(1, Math.ceil(count / pageSize));
  return (
    <div className="mt-3 flex items-center justify-between text-sm">
      <span className="text-gray-500">{count} total</span>
      <div className="flex items-center gap-2">
        <button disabled={page <= 1} onClick={() => onChange(page - 1)} className="rounded border px-3 py-1 disabled:opacity-40">Prev</button>
        <span>Page {page} of {pages}</span>
        <button disabled={page >= pages} onClick={() => onChange(page + 1)} className="rounded border px-3 py-1 disabled:opacity-40">Next</button>
      </div>
    </div>
  );
}

export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow" onClick={(e) => e.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} className="text-gray-500">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}