import { aiClient, apiClient, joinAiUrl, safeGet } from "./http";
import {
  mockAlerts,
  mockHealth,
  mockRules,
  mockStreams,
  mockStudents,
  mockSummary
} from "../data/mockData";

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
  return safeGet(apiClient, "/alerts", { list: mockAlerts, total: mockAlerts.length }, params);
}

export function fetchAlertStats(params = {}) {
  const fallback = {
    current_stream: "A101",
    avg_latency: "1.8s",
    recognized_count: 126,
    pending_alerts: 7,
    today_alerts: 18
  };
  return safeGet(apiClient, "/alert-stats", fallback, params);
}

export function fetchRules(params = {}) {
  return safeGet(apiClient, "/rules", mockRules, params);
}

export function fetchStudents(params = {}) {
  return safeGet(apiClient, "/students", { list: mockStudents, total: mockStudents.length }, params);
}

export function fetchSystemHealth() {
  return safeGet(apiClient, "/system/health", mockHealth);
}

export function fetchAnalysisEvents(params = {}) {
  return safeGet(aiClient, "/analysis/events", mockAlerts.slice(0, 2), params);
}

export function fetchAnalysisSummary(streamId) {
  return safeGet(aiClient, `/analysis/summary/${streamId}`, mockSummary);
}

export function fetchModelStatus() {
  return safeGet(aiClient, "/model/status", {
    loaded: true,
    version: "demo-yolo-v8",
    inference_ms: 42
  });
}
