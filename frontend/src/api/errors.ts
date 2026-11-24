import { isAxiosError } from "axios";
import toast from "react-hot-toast";

export interface ParsedError { code: string; message: string; details: unknown }

export function parseError(err: unknown): ParsedError {
  if (isAxiosError(err) && err.response?.data && typeof err.response.data === "object") {
    const d = err.response.data as Partial<ParsedError>;
    return { code: d.code ?? "error", message: d.message ?? "Request failed.", details: d.details };
  }
  return { code: "network_error", message: "Cannot reach the server.", details: null };
}

export function toastError(err: unknown) {
  const { code, message, details } = parseError(err);
  let text = message;
  if (code === "insufficient_stock" && Array.isArray(details)) {
    text += "\n" + details
      .map((d: { product: string; requested: number; available: number }) =>
        `${d.product}: requested ${d.requested}, available ${d.available}`)
      .join("\n");
  } else if (code === "validation_error" && details && typeof details === "object") {
    text += "\n" + Object.entries(details as Record<string, unknown>)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : JSON.stringify(v)}`)
      .join("\n");
  }
  toast.error(text, { duration: 7000, style: { whiteSpace: "pre-line" } });
}