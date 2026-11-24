import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import OrderDetail from "./OrderDetail";
import type { Role } from "../types";

let roles: Role[] = [];
let status = "CONFIRMED";

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ hasRole: (...r: Role[]) => r.some((x) => roles.includes(x)) }),
}));
vi.mock("../api/client", () => ({
  api: {
    get: vi.fn((url: string) =>
      Promise.resolve({
        data: url.endsWith("history/") ? [] : {
          id: 1, order_number: "ORD-2026-000001", customer: 1, customer_name: "Acme",
          order_date: "2026-11-24T10:00:00Z", status, total_amount: "40.00", created_by: 1,
          lines: [{ id: 1, product: 1, product_sku: "W-1", product_name: "Widget", quantity: 4, unit_price: "10.00", line_total: "40.00" }],
        },
      })),
    post: vi.fn(),
  },
}));

function renderDetail(r: Role[], s: string) {
  roles = r; status = s;
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/orders/1"]}>
        <Routes><Route path="/orders/:id" element={<OrderDetail />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OrderDetail actions", () => {
  beforeEach(() => vi.clearAllMocks());

  it("Inventory Manager can ship a CONFIRMED order but sees no Confirm button", async () => {
    renderDetail(["Inventory Manager"], "CONFIRMED");
    expect(await screen.findByRole("button", { name: "Ship" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Confirm" })).not.toBeInTheDocument();
  });

  it("Ship is disabled while the order is still DRAFT", async () => {
    renderDetail(["Admin"], "DRAFT");
    expect(await screen.findByRole("button", { name: "Ship" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Confirm" })).toBeEnabled();
  });

  it("Cancel is disabled for a SHIPPED order", async () => {
    renderDetail(["Admin"], "SHIPPED");
    expect(await screen.findByRole("button", { name: "Cancel" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Deliver" })).toBeEnabled();
  });
});