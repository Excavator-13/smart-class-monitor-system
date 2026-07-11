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
  }
];

export const mockStudents = [
  { id: 1, student_no: "2026001", name: "Student Zhang", class_name: "Class 1", status: "active", face_registered: true, last_seen: "--" },
  { id: 2, student_no: "2026002", name: "Student Li", class_name: "Class 1", status: "active", face_registered: true, last_seen: "--" }
];

export const mockHealth = {
  rtmp: "online",
  ai: "online",
  api: "online",
  database: "online"
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
