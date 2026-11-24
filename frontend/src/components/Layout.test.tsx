import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Layout from "./Layout";
import type { Role } from "../types";

let roles: Role[] = [];
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 1, username: "tester", roles },
    loading: false,
    logout: vi.fn(),
    hasRole: (...r: Role[]) => r.some((x) => roles.includes(x)),
  }),
}));

function renderLayout(r: Role[]) {
  roles = r;
  render(
    <MemoryRouter initialEntries={["/products"]}>
      <Routes><Route element={<Layout />}><Route path="/products" element={<div>content</div>} /></Route></Routes>
    </MemoryRouter>,
  );
}

describe("Layout navigation", () => {
  it("shows Customers for Sales User", () => {
    renderLayout(["Sales User"]);
    expect(screen.getByText("Customers")).toBeInTheDocument();
  });

  it("hides Customers for Inventory Manager", () => {
    renderLayout(["Inventory Manager"]);
    expect(screen.queryByText("Customers")).not.toBeInTheDocument();
    expect(screen.getByText("Orders")).toBeInTheDocument();
  });

  it("shows Users only for Admin", () => {
    renderLayout(["Admin"]);
    expect(screen.getByText("Users")).toBeInTheDocument();
  });
});