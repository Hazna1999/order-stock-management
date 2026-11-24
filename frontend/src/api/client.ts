import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

export const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshToken(): Promise<string | null> {
  const refresh = localStorage.getItem("refresh");
  if (!refresh) return null;
  try {
    const { data } = await axios.post("/api/v1/auth/refresh/", { refresh });
    localStorage.setItem("access", data.access);
    if (data.refresh) localStorage.setItem("refresh", data.refresh);
    return data.access;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const isAuthCall = original?.url?.includes("/auth/");
    if (error.response?.status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      refreshing ??= refreshToken().finally(() => { refreshing = null; });
      const token = await refreshing;
      if (token) {
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      }
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);