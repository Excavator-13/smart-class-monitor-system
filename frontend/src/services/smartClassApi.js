import { aiClient, apiClient, isMockEnabled, joinAiUrl, requestData, unwrapResponse } from "./http";
import {
  mockAlerts,
  mockAnalysisEvents,
  mockHealth,
  mockRules,
  mockStreams,
  mockStudents,
  mockSummary,
} from "../data/mockData";

function asArray(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.records)) return payload.records;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.list)) return payload.list;
  return [];
}

function optional(value, fallback = "") {
  return value ?? fallback;
}

function normalizePage(payload, mapper = (item) => item) {
  const records = asArray(payload).map(mapper);
  return {
    records,
    page: payload?.page ?? 1,
    page_size: payload?.page_size ?? records.length,
    total: payload?.total ?? records.length
  };
}

async function getWithMock(client, url, params, mockPayload, mapper) {
  try {
    const payload = await requestData(client, { method: "get", url, params });
    return mapper ? mapper(payload) : payload;
  } catch (error) {
    if (isMockEnabled()) return mapper ? mapper(mockPayload) : mockPayload;
    throw error;
  }
}

export function normalizeStream(item = {}) {
  const status = item.status === "enabled" ? "online" : item.status;
  return {
    id: optional(item.id, item.stream_id),
    stream_id: optional(item.stream_id),
    stream_name: optional(item.stream_name, item.name || item.stream_id || "未命名视频源"),
    location: optional(item.location, item.remark || ""),
    status: optional(status, "unknown"),
    rtmp_url: optional(item.rtmp_url),
    hls_url: optional(item.hls_url),
    mjpeg_url: optional(item.mjpeg_url),
    remark: optional(item.remark)
  };
}

export function normalizeAlert(item = {}) {
  const target = item.target || item.target_info || null;
  return {
    id: optional(item.id, item.event_id),
    event_id: optional(item.event_id),
    stream_id: optional(item.stream_id),
    stream_name: optional(item.stream_name),
    student_id: item.student_id ?? target?.student_id ?? null,
    student_name: optional(item.student_name, target?.student_name || ""),
    alert_type: optional(item.alert_type, item.event_type || item.event_name || "unknown"),
    alert_name: optional(item.alert_name, item.event_name || item.alert_type || ""),
    level: optional(item.level, "info"),
    status: optional(item.status, item.event_status || "unhandled"),
    confidence: item.confidence ?? target?.confidence ?? null,
    snapshot_url: optional(item.snapshot_url, item.snapshot_path),
    record_url: optional(item.record_url, item.video_path || item.record_path),
    occurred_at: optional(item.occurred_at, item.time || item.created_at || ""),
    handled_at: optional(item.handled_at),
    remark: optional(item.remark, item.description || item.summary || ""),
    target,
    zone: item.zone || null
  };
}

export function normalizeRule(item = {}) {
  return {
    id: optional(item.id, item.rule_id),
    rule_type: optional(item.rule_type, item.type || ""),
    name: optional(item.name, item.rule_name || item.rule_type || "未命名规则"),
    enabled: item.enabled ?? item.status === "enabled",
    threshold_seconds: item.threshold_seconds ?? item.duration_threshold ?? 1,
    confidence_threshold: item.confidence_threshold ?? item.confidence ?? null,
    cooldown_seconds: item.cooldown_seconds ?? null,
    zone_type: optional(item.zone_type),
    summary: optional(item.summary, item.description || "")
  };
}

export function normalizeStudent(item = {}) {
  return {
    id: optional(item.id, item.student_id),
    student_no: optional(item.student_no),
    name: optional(item.name, item.student_name || "未命名人员"),
    class_name: optional(item.class_name),
    status: optional(item.status, "active"),
    face_registered: Boolean(item.face_registered ?? item.has_face ?? item.feature_count),
    last_seen: optional(item.last_seen, item.last_seen_at || "")
  };
}

export function normalizeZone(item = {}) {
  return {
    id: optional(item.id, item.zone_id),
    zone_id: optional(item.zone_id, item.id),
    stream_id: optional(item.stream_id),
    zone_name: optional(item.zone_name, item.name || "未命名区域"),
    zone_type: optional(item.zone_type, item.type || ""),
    coordinates: item.coordinates || item.points || [],
    enabled: item.enabled ?? item.status === "enabled"
  };
}

export function normalizeAiEvent(item = {}) {
  return {
    event_id: optional(item.event_id),
    stream_id: optional(item.stream_id),
    event_type: optional(item.event_type, item.alert_type || ""),
    event_name: optional(item.event_name, item.alert_name || item.alert_type || ""),
    level: optional(item.level, "info"),
    event_status: optional(item.event_status, item.status || ""),
    confidence: item.confidence ?? item.target?.confidence ?? null,
    occurred_at: optional(item.occurred_at, item.time || ""),
    duration_seconds: item.duration_seconds ?? null,
    target: item.target || item.target_info || null,
    zone: item.zone || null,
    snapshot_path: optional(item.snapshot_path, item.snapshot_url)
  };
}

export function normalizeModelStatus(payload = {}) {
  const models = Array.isArray(payload.models) ? payload.models : [];
  const streams = Array.isArray(payload.streams) ? payload.streams : [];
  const firstLoadedModel = models.find((item) => item.loaded) || models[0] || {};
  const inferValues = models.map((item) => Number(item.avg_infer_ms)).filter(Number.isFinite);
  return {
    service_status: optional(payload.service_status, payload.loaded ? "running" : "unknown"),
    models,
    streams,
    loaded: models.length ? models.some((item) => item.loaded) : Boolean(payload.loaded),
    version: optional(firstLoadedModel.version, payload.version || ""),
    model_name: optional(firstLoadedModel.model_name, payload.model_name || ""),
    inference_ms: inferValues.length ? Math.round(inferValues.reduce((sum, value) => sum + value, 0) / inferValues.length) : payload.inference_ms
  };
}

export function normalizeHealth(payload = {}) {
  return {
    api: optional(payload.api, payload.backend || payload.service_status || "unknown"),
    database: optional(payload.database, payload.mysql || "unknown"),
    ai: optional(payload.ai, payload.ai_service || "unknown"),
    rtmp: optional(payload.rtmp, payload.nginx || payload.nginx_rtmp || "unknown")
  };
}

export async function login(payload) {
  const data = await requestData(apiClient, {
    method: "post",
    url: "/auth/login",
    data: {
      username: payload.username,
      password: payload.password
    }
  });
  return unwrapResponse(data);
}

export async function fetchCurrentUser() {
  return requestData(apiClient, { method: "get", url: "/auth/info" });
}

export async function logout() {
  try {
    return await requestData(apiClient, { method: "post", url: "/auth/logout" });
  } catch {
    return { success: true, local_only: true };
  }
}

export function getVideoFeedUrl(streamId, options = {}) {
  if (!streamId) return "";
  const params = new URLSearchParams();
  if (options.annotate === false) params.set("annotate", "false");
  if (options.modules) params.set("modules", options.modules);
  const query = params.toString();
  return `${joinAiUrl(`/video_feed/${streamId}`)}${query ? `?${query}` : ""}`;
}

export function fetchStreams(params = {}) {
  return getWithMock(apiClient, "/streams/enabled", params, mockStreams, (payload) => {
    const records = asArray(payload).map(normalizeStream);
    return Array.isArray(payload) ? records : normalizePage(payload, normalizeStream);
  });
}

export function fetchStreamStatus(streamId) {
  return getWithMock(apiClient, `/streams/${streamId}/status`, {}, null);
}

export function fetchStreamPreviewUrl(streamId) {
  return getWithMock(apiClient, `/streams/${streamId}/preview-url`, {}, null);
}

export function fetchAlerts(params = {}) {
  return getWithMock(apiClient, "/alerts", params, { records: mockAlerts }, (payload) => normalizePage(payload, normalizeAlert));
}

export function fetchAlertStats(params = {}) {
  return getWithMock(
    apiClient,
    "/alert-stats",
    params,
    {
      today_total: mockAlerts.length,
      unhandled_count: mockAlerts.filter((item) => item.status !== "handled").length,
      by_type: []
    }
  );
}

export function fetchRules(params = {}) {
  return getWithMock(apiClient, "/rules", params, mockRules, (payload) => asArray(payload).map(normalizeRule));
}

export function fetchZones(params = {}) {
  return getWithMock(apiClient, "/zones", params, [], (payload) => asArray(payload).map(normalizeZone));
}

export function fetchStreamZones(streamId) {
  return getWithMock(apiClient, `/streams/${streamId}/zones`, {}, [], (payload) => asArray(payload).map(normalizeZone));
}

export function fetchStudents(params = {}) {
  return getWithMock(apiClient, "/students", params, { records: mockStudents }, (payload) => normalizePage(payload, normalizeStudent));
}

export function fetchSystemHealth() {
  return getWithMock(apiClient, "/system/health", {}, mockHealth, normalizeHealth);
}

export function fetchAnalysisEvents(params = {}) {
  return getWithMock(aiClient, "/analysis/events", params, { items: [] }, (payload) => asArray(payload).map(normalizeAiEvent));
}

export function fetchAnalysisSummary(streamId) {
  return getWithMock(aiClient, `/analysis/summary/${streamId}`, {}, mockSummary);
}

export function fetchModelStatus() {
  return getWithMock(aiClient, "/model/status", {}, { service_status: "unknown", models: [], streams: [] }, normalizeModelStatus);
}
