import axios from "axios";

const timeout = 4500;

function getRuntimeConfig() {
  return window.__SMART_CLASS_CONFIG__ || {};
}

function getBaseUrl(runtimeKey, envKey, fallback) {
  const runtimeValue = getRuntimeConfig()[runtimeKey];
  return runtimeValue || import.meta.env[envKey] || fallback;
}

export const apiClient = axios.create({
  baseURL: getBaseUrl("API_BASE", "VITE_API_BASE", "/api"),
  timeout
});

export const aiClient = axios.create({
  baseURL: getBaseUrl("AI_BASE", "VITE_AI_BASE", "/ai"),
  timeout
});

export const nginxBase = getBaseUrl("NGINX_BASE", "VITE_NGINX_BASE", "/media");

export function joinResourceUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${nginxBase.replace(/\/$/, "")}/${String(path).replace(/^\//, "")}`;
}

export function joinAiUrl(path) {
  const base = getBaseUrl("AI_BASE", "VITE_AI_BASE", "/ai");
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
