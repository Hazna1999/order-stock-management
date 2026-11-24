import { NavLink, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { user, loading, logout, hasRole } = useAuth();
  if (loading) return <div className="p-8 text-gray-500">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  const link = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded text-sm ${isActive ? "bg-white/20" : "hover:bg-white/10"}`;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-slate-800 text-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-2 px-4 py-3">
          <span className="mr-4 font-semibold">Order &amp; Stock</span>
          <nav className="flex gap-1">
            <NavLink to="/products" className={link}>Products</NavLink>
            {hasRole("Admin", "Sales User") && <NavLink to="/customers" className={link}>Customers</NavLink>}
            <NavLink to="/orders" className={link}>Orders</NavLink>
            {hasRole("Admin") && <NavLink to="/users" className={link}>Users</NavLink>}
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span>{user.username} <span className="rounded bg-white/20 px-2 py-0.5 text-xs">{user.roles.join(", ") || "no role"}</span></span>
            <button onClick={logout} className="rounded bg-white/10 px-3 py-1 hover:bg-white/20">Logout</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-4"><Outlet /></main>
    </div>
  );
}
