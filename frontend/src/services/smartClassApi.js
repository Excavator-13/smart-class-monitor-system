import { aiClient, apiClient, joinAiUrl, safeGet } from "./http";
import {
  mockAlerts,
  mockAnalysisEvents,
  mockHealth,
  mockRules,
  mockStreams,
  mockStudents,
  mockSummary,
} from "../data/mockData";

function unwrapResponse(data) {
  return data?.data ?? data;
}

export async function login(payload) {
  const { data } = await apiClient.post("/auth/login", {
    username: payload.username,
    password: payload.password,
  });
  return unwrapResponse(data);
}

export async function fetchCurrentUser() {
  const { data } = await apiClient.get("/auth/info");
  return unwrapResponse(data);
}

export async function logout() {
  try {
    const { data } = await apiClient.post("/auth/logout");
    return unwrapResponse(data);
  } catch {
    return { success: true, local_only: true };
  }
}

export function getVideoFeedUrl(streamId) {
  return joinAiUrl(`/video_feed/${streamId}`);
}

export function fetchStreams(params = {}) {
  return safeGet(apiClient, "/streams", mockStreams, params);
}

export function fetchStreamStatus(streamId) {
  return safeGet(apiClient, `/streams/${streamId}/status`, null);
}

export function fetchAlerts(params = {}) {
  return safeGet(
    apiClient,
    "/alerts",
    { records: mockAlerts, total: mockAlerts.length },
    params,
  );
}

export function fetchAlertStats() {
  const fallback = {
    unhandled_count: 7,
    today_total: 18,
  };
  return safeGet(apiClient, "/alert-stats", fallback);
}

export function fetchRules(params = {}) {
  return safeGet(apiClient, "/rules", mockRules, params);
}

export function fetchStudents(params = {}) {
  return safeGet(
    apiClient,
    "/students",
    { records: mockStudents, total: mockStudents.length },
    params,
  );
}

export function fetchSystemHealth() {
  return safeGet(apiClient, "/system/health", mockHealth);
}

export function fetchAnalysisEvents(params = {}) {
  return safeGet(aiClient, "/analysis/events", mockAnalysisEvents, params);
}

export function fetchAnalysisSummary(streamId) {
  return safeGet(aiClient, `/analysis/summary/${streamId}`, mockSummary);
}

export async function fetchModelStatus() {
  const result = await safeGet(aiClient, "/model/status", null);
  if (!result) {
    return { service_status: "unknown", models: [], streams: [] };
  }
  return result;
}
