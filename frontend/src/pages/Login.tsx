import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/products" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await login(username, password);
      navigate("/products");
    } catch {
      toast.error("Invalid username or password.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-lg bg-white p-6 shadow">
        <h1 className="text-xl font-semibold">Sign in</h1>
        <input className="w-full rounded border p-2" placeholder="Username" value={username}
          onChange={(e) => setUsername(e.target.value)} required autoFocus />
        <input className="w-full rounded border p-2" type="password" placeholder="Password" value={password}
          onChange={(e) => setPassword(e.target.value)} required />
        <button disabled={busy} className="w-full rounded bg-slate-800 py-2 text-white disabled:opacity-50">
          {busy ? "Signing in..." : "Sign in"}
        </button>
        <p className="text-xs text-gray-500">Demo: admin1, sales1, sales2, inventory1 / Pass@1234</p>
      </form>
    </div>
  );
}