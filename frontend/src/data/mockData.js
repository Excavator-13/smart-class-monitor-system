export const ALERT_LEVEL_MAP = {
  info: { label: "信息", color: "#909399" },
  warning: { label: "警告", color: "#E6A23C" },
  high: { label: "高危", color: "#F56C6C" },
};

export const ALERT_STATUS_MAP = {
  unhandled: { label: "未处理", tag: "danger" },
  processing: { label: "处理中", tag: "warning" },
  handled: { label: "已处理", tag: "success" },
  false_alarm: { label: "误报", tag: "info" },
  ignored: { label: "已忽略", tag: "info" },
};

export const ALERT_TYPE_MAP = {
  face_recognized: "已识别人员",
  stranger_detected: "陌生人出现",
  danger_zone_intrusion: "危险区域入侵",
  danger_zone_stay: "危险区域停留",
  danger_zone_approach: "危险区域接近",
  phone_usage: "使用手机",
  head_down: "长时间低头",
  leave_seat: "长时间离座",
  flame_detected: "明火检测",
  fall_detected: "人员摔倒",
  crowd_gathering: "异常人流聚集",
  stream_offline: "视频流中断",
};

export const mockStreams = [
  {
    id: 1,
    stream_id: "classroom_01",
    stream_name: "Classroom 01 Main Camera",
    location: "Teaching Building A101",
    status: "enabled",
    latency: "1.8s",
    rtmp_url: "rtmp://media-server/live/classroom_01",
    remark: "Local mock stream"
  },
  {
    id: 2,
    stream_id: "classroom_02",
    stream_name: "Classroom 02 Rear Camera",
    location: "Teaching Building B203",
    status: "enabled",
    latency: "2.4s",
    rtmp_url: "rtmp://media-server/live/classroom_02",
    remark: "Reserved stream"
  }
];

// Keep mock alerts empty by default. AI scoring should appear only after a real
// alert/event is returned by the service or injected by integration testing.
export const mockAlerts = [];

export const mockRules = [
  {
    id: 1,
    rule_type: "phone_usage",
    name: "Phone usage",
    enabled: true,
    threshold_seconds: 5,
    confidence_threshold: 0.75,
    cooldown_seconds: 30,
    zone_type: "phone_forbidden",
    summary: "Enabled only after forbidden zone confirmation"
  },
  {
    id: 2,
    rule_type: "fire_detected",
    name: "Fire detection",
    enabled: true,
    threshold_seconds: 3,
    confidence_threshold: 0.8,
    cooldown_seconds: 20,
    zone_type: "danger",
    summary: "High-priority safety event"
  },
  {
    id: 3,
    rule_type: "fall_detected",
    name: "Fall detection",
    enabled: true,
    threshold_seconds: 4,
    confidence_threshold: 0.78,
    cooldown_seconds: 20,
    zone_type: "classroom",
    summary: "Triggered after a sustained fall posture"
  },
  {
    id: 4,
    rule_type: "head_down",
    name: "Head-down behavior",
    enabled: true,
    threshold_seconds: 6,
    confidence_threshold: 0.7,
    cooldown_seconds: 60,
    zone_type: "seat",
    summary: "Evaluated by seat area and duration"
  },
  {
    id: 5,
    rule_type: "deepfake_detected",
    name: "Deepfake face detection",
    enabled: true,
    threshold_seconds: 0,
    confidence_threshold: 0.35,
    cooldown_seconds: 30,
    level: "high",
    summary: "AI-generated or manipulated face detection"
  },
  {
    id: 6,
    rule_type: "spoof_detected",
    name: "Anti-spoof detection",
    enabled: true,
    threshold_seconds: 0,
    confidence_threshold: 0.6,
    cooldown_seconds: 30,
    level: "high",
    summary: "Photo or video replay attack detection"
  }
];

export const mockStudents = [
  { id: 1, student_no: "2026001", name: "Student Zhang", class_name: "Class 1", status: "active", face_registered: true, last_seen: "--" },
  { id: 2, student_no: "2026002", name: "Student Li", class_name: "Class 1", status: "active", face_registered: true, last_seen: "--" }
];

export const mockHealth = {
  rtmp: "up",
  ai: "up",
  backend: "up",
  database: "up",
};

export const mockSummary = {
  risk_score: 0,
  title: "Waiting for risk events",
  summary: "The frontend calculates risk scores only after effective alerts or AI events are returned.",
  actions: ["Monitor", "Review AI marks", "Keep evidence"],
  timeline: [
    { time: "Now", text: "Phone risk requires a confirmed forbidden zone hit." },
    { time: "Now", text: "Fire and fall alerts can score independently once detected." }
  ]
};

export const mockAnalysisEvents = [
  {
    event_id: "evt_a1b2c3d4e5f6g7h8",
    stream_id: "classroom_01",
    event_type: "stranger_detected",
    event_name: "陌生人出现",
    level: "warning",
    event_status: "confirmed",
    confidence: 0.78,
    occurred_at: "2026-07-09T10:25:00+08:00",
    duration_seconds: 5.2,
    target: { track_id: "face_1", bbox: [100, 200, 300, 400] },
    zone: null,
    snapshot_path: null,
  },
  {
    event_id: "evt_b2c3d4e5f6g7h8i9",
    stream_id: "classroom_01",
    event_type: "phone_usage",
    event_name: "使用手机",
    level: "warning",
    event_status: "confirmed",
    confidence: 0.85,
    occurred_at: "2026-07-09T10:22:00+08:00",
    duration_seconds: 3.1,
    target: { track_id: "person_2", bbox: [150, 250, 350, 450] },
    zone: null,
    snapshot_path: null,
  },
];
