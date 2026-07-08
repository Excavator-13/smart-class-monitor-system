import axios from "axios";

const timeout = 4500;

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/api",
  timeout
});

export const aiClient = axios.create({
  baseURL: import.meta.env.VITE_AI_BASE || "/ai",
  timeout
});

export const nginxBase = import.meta.env.VITE_NGINX_BASE || "/media";

export function joinResourceUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${nginxBase.replace(/\/$/, "")}/${String(path).replace(/^\//, "")}`;
}

export function joinAiUrl(path) {
  const base = import.meta.env.VITE_AI_BASE || "/ai";
  return `${base.replace(/\/$/, "")}/${String(path).replace(/^\//, "")}`;
}

export async function safeGet(client, url, fallback, params = {}) {
  try {
    const { data } = await client.get(url, { params });
    return data?.data ?? data;
  } catch (error) {
    return fallback;
  }
}
