export type Role = "Admin" | "Sales User" | "Inventory Manager";
export type OrderStatus = "DRAFT" | "CONFIRMED" | "SHIPPED" | "DELIVERED" | "CANCELLED";

export interface Me { id: number; username: string; roles: Role[] }
export interface Page<T> { count: number; next: string | null; previous: string | null; results: T[] }

export interface Product {
  id: number; name: string; sku: string; description: string; category: string;
  unit_price: string; stock_quantity: number; reorder_level: number; is_active: boolean;
}
export interface Customer {
  id: number; name: string; email: string; phone: string; billing_address: string; is_active: boolean;
}
export interface OrderLine {
  id: number; product: number; product_sku: string; product_name: string;
  quantity: number; unit_price: string; line_total: string;
}
export interface Order {
  id: number; order_number: string; customer: number; customer_name: string;
  order_date: string; status: OrderStatus; total_amount: string; created_by: number; lines: OrderLine[];
}
export interface HistoryRow {
  id: number; action: string; from_status: string; to_status: string;
  performed_by: string; performed_at: string;
}