import { describe, expect, it } from "vitest";
import { AxiosError } from "axios";
import { parseError } from "./errors";

function axiosError(data: unknown) {
  const err = new AxiosError("fail");
  err.response = { data, status: 409, statusText: "", headers: {}, config: {} as never };
  return err;
}

describe("parseError", () => {
  it("reads the backend code, message and details", () => {
    const e = parseError(axiosError({
      code: "insufficient_stock", message: "Not enough stock",
      details: [{ product: "W-1", requested: 6, available: 1 }],
    }));
    expect(e.code).toBe("insufficient_stock");
    expect(e.message).toBe("Not enough stock");
    expect(e.details).toEqual([{ product: "W-1", requested: 6, available: 1 }]);
  });

  it("falls back for network errors", () => {
    expect(parseError(new Error("boom")).code).toBe("network_error");
  });
});