import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Products from "./pages/Products";
import Customers from "./pages/Customers";

const Placeholder = ({ name }: { name: string }) => <div className="text-gray-600">{name} page coming next</div>;

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/products" element={<Products />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/orders" element={<Placeholder name="Orders" />} />
      </Route>
      <Route path="*" element={<Navigate to="/products" replace />} />
    </Routes>
  );
}