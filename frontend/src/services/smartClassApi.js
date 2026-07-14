import {
  aiClient,
  apiClient,
  isMockEnabled,
  joinAiUrl,
  requestData,
  unwrapResponse,
} from "./http";
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
    total: payload?.total ?? records.length,
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

function parseMaybeJson(value) {
  if (!value || typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

export function normalizeStream(item = {}) {
  const rawStatus = item.status ?? item.stream_status;
  const status = rawStatus === "enabled" ? "online" : rawStatus;
  return {
    id: optional(item.id, item.stream_id ?? item.streamId),
    stream_id: optional(item.stream_id, item.streamId || ""),
    stream_name: optional(
      item.stream_name,
      item.streamName ||
        item.name ||
        item.stream_id ||
        item.streamId ||
        "未命名视频源",
    ),
    location: optional(item.location, item.remark || ""),
    status: optional(status, "unknown"),
    rtmp_url: optional(item.rtmp_url, item.rtmpUrl || ""),
    hls_url: optional(item.hls_url, item.hlsUrl || ""),
    mjpeg_url: optional(item.mjpeg_url, item.mjpegUrl || ""),
    remark: optional(item.remark),
  };
}

export function normalizeAlert(item = {}) {
  const target = parseMaybeJson(
    item.target || item.target_info || item.targetInfo || null,
  );
  return {
    id: optional(item.id, item.event_id),
    event_id: optional(item.event_id, item.eventUid || item.event_uid || ""),
    stream_id: optional(item.stream_id, item.streamId || ""),
    stream_name: optional(item.stream_name, item.streamName || ""),
    student_id:
      item.student_id ??
      item.studentId ??
      target?.student_id ??
      target?.studentId ??
      null,
    student_name: optional(
      item.student_name,
      item.studentName || target?.student_name || target?.studentName || "",
    ),
    alert_type: optional(
      item.alert_type,
      item.alertType ||
        item.event_type ||
        item.eventType ||
        item.event_name ||
        "unknown",
    ),
    alert_name: optional(
      item.alert_name,
      item.alertName ||
        item.event_name ||
        item.eventName ||
        item.alert_type ||
        "",
    ),
    level: optional(item.level, "info"),
    status: optional(
      item.status,
      item.alert_status || item.alertStatus || item.event_status || "unhandled",
    ),
    confidence: item.confidence ?? target?.confidence ?? null,
    snapshot_url: optional(
      item.snapshot_url,
      item.snapshotUrl || item.snapshot_path || item.snapshotPath,
    ),
    record_url: optional(
      item.record_url,
      item.recordUrl ||
        item.video_path ||
        item.videoPath ||
        item.record_path ||
        item.recordPath,
    ),
    event_time_offset: item.event_time_offset ?? item.eventTimeOffset ?? null,
    occurred_at: optional(
      item.occurred_at,
      item.occurredAt || item.time || item.created_at || item.createdAt || "",
    ),
    handled_at: optional(item.handled_at, item.handledAt),
    remark: optional(item.remark, item.description || item.summary || ""),
    target,
    zone: parseMaybeJson(item.zone || null),
  };
}

export function normalizeRule(item = {}) {
  return {
    id: optional(item.id, item.rule_id),
    rule_type: optional(item.rule_type, item.ruleType || item.type || ""),
    name: optional(
      item.name,
      item.rule_name ||
        item.ruleName ||
        item.rule_type ||
        item.ruleType ||
        "未命名规则",
    ),
    enabled: item.enabled ?? item.status === "enabled",
    threshold_seconds:
      item.threshold_seconds ??
      item.thresholdSeconds ??
      item.duration_threshold ??
      1,
    confidence_threshold:
      item.confidence_threshold ??
      item.confidenceThreshold ??
      item.confidence ??
      null,
    cooldown_seconds: item.cooldown_seconds ?? item.cooldownSeconds ?? null,
    zone_type: optional(item.zone_type, item.zoneType || ""),
    summary: optional(item.summary, item.description || ""),
    level: optional(item.level, "warning"),
  };
}

export function normalizeStudent(item = {}) {
  return {
    id: optional(item.id, item.student_id ?? item.studentId),
    student_no: optional(item.student_no, item.studentNo || ""),
    name: optional(
      item.name,
      item.student_name || item.studentName || "未命名人员",
    ),
    class_name: optional(item.class_name, item.className || ""),
    status: optional(item.status, "active"),
    face_registered: Boolean(
      item.face_registered ??
      item.faceRegistered ??
      item.has_face ??
      item.hasFace ??
      item.feature_count,
    ),
    last_seen: optional(
      item.last_seen,
      item.lastSeen || item.last_seen_at || item.lastSeenAt || "",
    ),
  };
}

export function normalizeUserRecord(item = {}) {
  return {
    id: optional(item.id, item.user_id ?? item.userId),
    username: optional(item.username, ""),
    nickname: optional(item.nickname, item.name || ""),
    role: optional(item.role, "teacher"),
    status: optional(item.status, "enabled"),
    avatar_url: optional(item.avatar_url, item.avatarUrl || ""),
    last_login_at: optional(item.last_login_at, item.lastLoginAt || ""),
    created_at: optional(item.created_at, item.createdAt || ""),
  };
}

function parseCoordinates(value) {
  if (Array.isArray(value)) return value;
  if (typeof value === "string" && value.trim()) {
    try {
      return JSON.parse(value);
    } catch {
      return [];
    }
  }
  return [];
}

export function normalizeZone(item = {}) {
  return {
    id: optional(item.id, item.zone_id),
    zone_id: optional(item.zone_id, item.zoneId || item.id),
    stream_id: optional(item.stream_id, item.streamId || ""),
    zone_name: optional(
      item.zone_name,
      item.zoneName || item.name || "未命名区域",
    ),
    zone_type: optional(item.zone_type, item.zoneType || item.type || ""),
    shape_type: optional(item.shape_type, item.shapeType || "polygon"),
    coordinates: parseCoordinates(item.coordinates || item.points),
    threshold_seconds: Number(
      item.threshold_seconds ?? item.thresholdSeconds ?? 0,
    ),
    safe_distance: Number(item.safe_distance ?? item.safeDistance ?? 0),
    enabled: item.enabled ?? (item.status ? item.status === "enabled" : true),
  };
}

export function normalizeAiEvent(item = {}) {
  const target = parseMaybeJson(
    item.target || item.target_info || item.targetInfo || null,
  );
  return {
    event_id: optional(item.event_id, item.eventId || item.id || ""),
    stream_id: optional(item.stream_id, item.streamId || ""),
    event_type: optional(
      item.event_type,
      item.eventType || item.alert_type || item.alertType || "",
    ),
    event_name: optional(
      item.event_name,
      item.eventName ||
        item.alert_name ||
        item.alertName ||
        item.alert_type ||
        "",
    ),
    level: optional(item.level, "info"),
    event_status: optional(
      item.event_status,
      item.eventStatus || item.status || "",
    ),
    confidence: item.confidence ?? target?.confidence ?? null,
    occurred_at: optional(item.occurred_at, item.occurredAt || item.time || ""),
    duration_seconds: item.duration_seconds ?? item.durationSeconds ?? null,
    target,
    zone: parseMaybeJson(item.zone || null),
    snapshot_path: optional(
      item.snapshot_path,
      item.snapshotPath || item.snapshot_url || item.snapshotUrl,
    ),
  };
}

export function normalizeModelStatus(payload = {}) {
  const models = Array.isArray(payload.models) ? payload.models : [];
  const streams = Array.isArray(payload.streams) ? payload.streams : [];
  const firstLoadedModel =
    models.find((item) => item.loaded) || models[0] || {};
  const inferValues = models
    .map((item) => Number(item.avg_infer_ms ?? item.avgInferMs))
    .filter(Number.isFinite);
  return {
    service_status: optional(
      payload.service_status,
      payload.serviceStatus || (payload.loaded ? "running" : "unknown"),
    ),
    models,
    streams,
    loaded: models.length
      ? models.some((item) => item.loaded)
      : Boolean(payload.loaded),
    version: optional(firstLoadedModel.version, payload.version || ""),
    model_name: optional(
      firstLoadedModel.model_name,
      firstLoadedModel.modelName ||
        payload.model_name ||
        payload.modelName ||
        "",
    ),
    inference_ms: inferValues.length
      ? Math.round(
          inferValues.reduce((sum, value) => sum + value, 0) /
            inferValues.length,
        )
      : (payload.inference_ms ?? payload.inferenceMs),
  };
}

export function normalizeHealth(payload = {}) {
  return {
    api: optional(
      payload.api,
      payload.backend ||
        payload.service_status ||
        payload.serviceStatus ||
        "unknown",
    ),
    database: optional(payload.database, payload.mysql || "unknown"),
    ai: optional(
      payload.ai,
      payload.ai_service || payload.aiService || "unknown",
    ),
    rtmp: optional(
      payload.rtmp,
      payload.nginx || payload.nginx_rtmp || payload.nginxRtmp || "unknown",
    ),
  };
}

export async function login(payload) {
  const data = await requestData(apiClient, {
    method: "post",
    url: "/auth/login",
    data: {
      username: payload.username,
      password: payload.password,
    },
  });
  return unwrapResponse(data);
}

export async function fetchCurrentUser() {
  return requestData(apiClient, { method: "get", url: "/auth/info" });
}

export async function register(payload) {
  const data = await requestData(apiClient, {
    method: "post",
    url: "/auth/register",
    data: {
      username: payload.username,
      password: payload.password,
      nickname: payload.nickname || undefined,
    },
  });
  return unwrapResponse(data);
}

export async function logout() {
  try {
    return await requestData(apiClient, {
      method: "post",
      url: "/auth/logout",
    });
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
  return getWithMock(
    apiClient,
    "/streams/enabled",
    params,
    mockStreams,
    (payload) => {
      const records = asArray(payload).map(normalizeStream);
      return Array.isArray(payload)
        ? records
        : normalizePage(payload, normalizeStream);
    },
  );
}

export async function createStream(payload) {
  const data = await requestData(apiClient, {
    method: "post",
    url: "/streams",
    data: {
      stream_id: payload.stream_id,
      stream_name: payload.stream_name,
      rtmp_url: payload.rtmp_url,
      remark: payload.location || payload.remark || "",
    },
  });
  return normalizeStream(data);
}

export function fetchStreamStatus(streamId) {
  return getWithMock(apiClient, `/streams/${streamId}/status`, {}, null);
}

export function fetchStreamPreviewUrl(streamId) {
  return getWithMock(apiClient, `/streams/${streamId}/preview-url`, {}, null);
}

export function fetchAlerts(params = {}) {
  return getWithMock(
    apiClient,
    "/alerts",
    {
      streamId: params.streamId ?? params.stream_id,
      alertType: params.alertType ?? params.alert_type,
      status: params.status,
      level: params.level,
      page: params.page,
      pageSize: params.pageSize ?? params.page_size,
    },
    { records: mockAlerts },
    (payload) => normalizePage(payload, normalizeAlert),
  );
}

export async function updateAlertStatus(id, payload) {
  return requestData(apiClient, {
    method: "put",
    url: `/alerts/${id}/status`,
    data: {
      status: payload.status,
      remark: payload.remark || "",
    },
  });
}

export function fetchAlertStats(params = {}) {
  return getWithMock(apiClient, "/alert-stats", params, {
    today_total: mockAlerts.length,
    unhandled_count: mockAlerts.filter((item) => item.status !== "handled")
      .length,
    by_type: [],
  });
}

export function fetchRules(params = {}) {
  return getWithMock(apiClient, "/rules", params, mockRules, (payload) =>
    asArray(payload).map(normalizeRule),
  );
}

export async function toggleRule(id, enabled) {
  return requestData(apiClient, {
    method: "put",
    url: `/rules/${id}/toggle`,
    params: { enabled },
  });
}

export async function updateRule(id, data) {
  return requestData(apiClient, {
    method: "put",
    url: `/rules/${id}`,
    data,
  });
}

export async function fetchScoreConfig() {
  return requestData(apiClient, { method: "get", url: "/score-config" });
}

export async function updateScoreConfig(id, params) {
  return requestData(apiClient, {
    method: "put",
    url: `/score-config/${id}`,
    params,
  });
}

export function fetchZones(params = {}) {
  return getWithMock(apiClient, "/zones", params, [], (payload) =>
    asArray(payload).map(normalizeZone),
  );
}

export function fetchStreamZones(streamId) {
  return getWithMock(
    apiClient,
    `/streams/${streamId}/zones`,
    {},
    [],
    (payload) => asArray(payload).map(normalizeZone),
  );
}

export async function createZone(payload) {
  const data = await requestData(apiClient, {
    method: "post",
    url: "/zones",
    data: {
      stream_id: payload.stream_id,
      zone_name: payload.zone_name,
      zone_type: payload.zone_type,
      coordinates: JSON.stringify(payload.coordinates || []),
      threshold_seconds: payload.threshold_seconds,
      safe_distance: payload.safe_distance,
    },
  });
  return normalizeZone(data);
}

export async function updateZone(id, payload) {
  const data = await requestData(apiClient, {
    method: "put",
    url: `/zones/${id}`,
    data: {
      zone_name: payload.zone_name,
      zone_type: payload.zone_type,
      coordinates: payload.coordinates
        ? JSON.stringify(payload.coordinates)
        : undefined,
      threshold_seconds: payload.threshold_seconds,
      safe_distance: payload.safe_distance,
      enabled: payload.enabled,
    },
  });
  return normalizeZone(data);
}

export async function toggleZone(id, enabled) {
  return requestData(apiClient, {
    method: "put",
    url: `/zones/${id}/toggle`,
    params: { enabled },
  });
}

export async function deleteZone(id) {
  return requestData(apiClient, {
    method: "delete",
    url: `/zones/${id}`,
  });
}

export function fetchStudents(params = {}) {
  return getWithMock(
    apiClient,
    "/students",
    {
      className: params.className ?? params.class_name,
      keyword: params.keyword,
      faceRegistered: params.faceRegistered ?? params.face_registered,
      page: params.page,
      pageSize: params.pageSize ?? params.page_size,
    },
    { records: mockStudents },
    (payload) => normalizePage(payload, normalizeStudent),
  );
}

export async function createStudent(payload) {
  const data = await requestData(apiClient, {
    method: "post",
    url: "/students",
    data: {
      student_no: payload.student_no,
      name: payload.name,
      class_name: payload.class_name,
    },
  });
  return normalizeStudent(data);
}

export function fetchUsers(params = {}) {
  return getWithMock(
    apiClient,
    "/users",
    {
      role: params.role,
      status: params.status,
      page: params.page,
      pageSize: params.pageSize ?? params.page_size,
    },
    { records: [] },
    (payload) => normalizePage(payload, normalizeUserRecord),
  );
}

export async function updateUserRole(id, role) {
  return requestData(apiClient, {
    method: "put",
    url: `/users/${id}/role`,
    data: { role },
  });
}

export async function deleteUser(id) {
  return requestData(apiClient, {
    method: "delete",
    url: `/users/${id}`,
  });
}

export async function registerStudentFace(id, image) {
  return requestData(apiClient, {
    method: "post",
    url: `/students/${id}/face`,
    data: { image },
  });
}

export async function extractFaceFeature(image, studentId = "preview") {
  return requestData(aiClient, {
    method: "post",
    url: "/face/feature/extract",
    data: {
      image,
      student_id: studentId,
      image_type: "base64",
    },
  });
}

export function fetchSystemHealth() {
  return getWithMock(
    apiClient,
    "/system/health",
    {},
    mockHealth,
    normalizeHealth,
  );
}

export function fetchAnalysisEvents(params = {}) {
  return getWithMock(
    aiClient,
    "/analysis/events",
    params,
    { items: [] },
    (payload) => asArray(payload).map(normalizeAiEvent),
  );
}

export function fetchAnalysisSummary(streamId) {
  return getWithMock(
    aiClient,
    `/analysis/summary/${streamId}`,
    {},
    mockSummary,
  );
}

export function fetchModelStatus() {
  return getWithMock(
    aiClient,
    "/model/status",
    {},
    { service_status: "unknown", models: [], streams: [] },
    normalizeModelStatus,
  );
}
