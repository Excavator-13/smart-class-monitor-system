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

const AUTH_TOKEN_KEY = "smart_class_auth_token";
const AUTH_USER_KEY = "smart_class_auth_user";

export function getStoredToken() {
  return window.localStorage.getItem(AUTH_TOKEN_KEY) || window.sessionStorage.getItem(AUTH_TOKEN_KEY) || "";
}

export function getStoredUser() {
  const rawUser = window.localStorage.getItem(AUTH_USER_KEY) || window.sessionStorage.getItem(AUTH_USER_KEY);
  if (!rawUser) return null;
  try {
    return JSON.parse(rawUser);
  } catch {
    return null;
  }
}

export function storeAuthSession(token, user, remember = true) {
  const persistentStore = remember ? window.localStorage : window.sessionStorage;
  const transientStore = remember ? window.sessionStorage : window.localStorage;
  transientStore.removeItem(AUTH_TOKEN_KEY);
  transientStore.removeItem(AUTH_USER_KEY);
  persistentStore.setItem(AUTH_TOKEN_KEY, token || "");
  persistentStore.setItem(AUTH_USER_KEY, JSON.stringify(user || {}));
}

export function clearAuthSession() {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USER_KEY);
  window.sessionStorage.removeItem(AUTH_TOKEN_KEY);
  window.sessionStorage.removeItem(AUTH_USER_KEY);
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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
