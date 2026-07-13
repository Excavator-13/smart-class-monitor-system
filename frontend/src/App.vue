<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  Bell,
  Camera,
  Clock,
  Connection,
  FullScreen,
  Lock,
  Refresh,
  Search,
  Setting,
  Switch,
  User,
  VideoCamera,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  createStream,
  createStudent,
  createZone,
  deleteZone,
  extractFaceFeature,
  fetchAlerts,
  fetchAlertStats,
  fetchAnalysisEvents,
  fetchAnalysisSummary,
  fetchCurrentUser,
  fetchModelStatus,
  fetchRules,
  fetchStreams,
  fetchStudents,
  fetchSystemHealth,
  fetchUsers,
  fetchZones,
  getVideoFeedUrl,
  login,
  logout,
  register,
  registerStudentFace,
  toggleRule,
  toggleZone,
  updateAlertStatus,
  updateUserRole,
  updateScoreConfig,
  updateZone,
  fetchScoreConfig,
} from "./services/smartClassApi";
import {
  clearAuthSession,
  getStoredToken,
  getStoredUser,
  isMockEnabled,
  joinResourceUrl,
  storeAuthSession,
} from "./services/http";
import lineDogGif from "./assets/line-dog.gif";

const activePage = ref("monitor");
const loginBackgroundVideo = `${import.meta.env.BASE_URL}auth/login-moonset.mp4`;
const authVideoReady = ref(false);
const authVideoFailed = ref(false);
const isAuthenticated = ref(Boolean(getStoredToken()));
const currentUser = ref(getStoredUser());
const authMode = ref("login");
const authLoading = ref(false);
const authNotice = ref("");
const authNoticeType = ref("info");
const canUseDeveloperLogin =
  import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEV_LOGIN === "true";
const authForm = ref({
  username: "",
  password: "",
  remember: true,
});
const registerForm = ref({
  username: "",
  password: "",
  nickname: "",
});
const personDialogVisible = ref(false);
const streamDialogVisible = ref(false);
const faceDialogVisible = ref(false);
const alertProcessDialogVisible = ref(false);
const selectedStudent = ref(null);
const selectedAlert = ref(null);
const faceImageBase64 = ref("");
const faceImageName = ref("");
const newPersonFaceImageBase64 = ref("");
const newPersonFaceImageName = ref("");
const faceValidationMessage = ref("");
const faceValidationLoading = ref(false);
const newPersonFaceValidationMessage = ref("");
const newPersonFaceValidationLoading = ref(false);
const alertProcessForm = ref({
  status: "handled",
  remark: "",
});
const replayVisible = ref(false);
const replayUrl = ref("");
const replayOffset = ref(0);
const replayVideoRef = ref(null);
const personForm = ref({
  student_no: "",
  name: "",
  class_name: "",
  face_registered: false,
});
const streamForm = ref({
  stream_id: "",
  stream_name: "",
  location: "",
  rtmp_url: "",
  status: "online",
});
const riskScoreSettings = ref([]);
const activeStreamId = ref("");
const activeAlertStatus = ref("全部");

// ── 钉钉 & AI 日报设置（存 localStorage）─────────────────
const SETTINGS_KEY = "smart_class_alert_settings";
const loadSettings = () => {
  try {
    return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {};
  } catch {
    return {};
  }
};
const saveSettings = (s) =>
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
const saved = loadSettings();
const alertSettings = ref({
  dingtalkEnabled: saved.dingtalkEnabled ?? true,
  responsible: saved.responsible ?? "项重善",
  contacts: saved.contacts ?? [
    { name: "项重善", mobile: "18601033435" },
    { name: "章志超", mobile: "15270985055" },
  ],
  aiReportEnabled: saved.aiReportEnabled ?? true,
  reportTime: saved.reportTime ?? "18:00",
  alertInterval: saved.alertInterval ?? 30,
  generating: false,
  latestReport: saved.latestReport ?? null,
  reportHistory: saved.reportHistory ?? [],
});

watch(alertSettings, saveSettings, { deep: true });

const syncContactsToBackend = async () => {
  try {
    await fetch("http://127.0.0.1:8080/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contacts: alertSettings.value.contacts,
        responsible: alertSettings.value.responsible,
        reportTime: alertSettings.value.reportTime,
        alertInterval: alertSettings.value.alertInterval,
      }),
    });
  } catch {}
};
watch(() => alertSettings.value.responsible, syncContactsToBackend);

// 联系人弹窗
const showContactModal = ref(false);
const newContact = ref({ name: "", mobile: "" });
const doAddContact = () => {
  const { name, mobile } = newContact.value;
  if (!name.trim()) {
    alert("请输入姓名");
    return;
  }
  if (!/^1\d{10}$/.test(mobile.trim())) {
    alert("请输入有效的 11 位手机号");
    return;
  }
  if (alertSettings.value.contacts.some((c) => c.name === name.trim())) {
    alert("已存在");
    return;
  }
  alertSettings.value.contacts.push({
    name: name.trim(),
    mobile: mobile.trim(),
  });
  newContact.value = { name: "", mobile: "" };
  syncContactsToBackend();
};
const removeContact = (name) => {
  if (name === "项重善" || name === "章志超") {
    alert("默认负责人不能删除");
    return;
  }
  alertSettings.value.contacts = alertSettings.value.contacts.filter(
    (c) => c.name !== name,
  );
  syncContactsToBackend();
};

// 日报
const showReportModal = ref(false);
const generateAiReport = async () => {
  alertSettings.value.generating = true;
  try {
    const alertsData = displayAlerts.value.slice(0, 50).map((a) => ({
      alertType: a.alert_type || a.type || "未知",
      level: a.level || "info",
      streamId: a.stream_id || a.location || "",
      snapshotUrl: a.snapshot_url || "",
    }));
    let report;
    try {
      const resp = await fetch("http://127.0.0.1:8080/report/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(alertsData),
      });
      if (resp.ok) report = await resp.json();
    } catch {}
    if (!report) {
      report = {
        date: new Date().toISOString().slice(0, 10),
        time: new Date().toLocaleString("zh-CN"),
        summary: "日报生成失败，请检查后端服务",
        alertsCount: 0,
      };
    }
    alertSettings.value.latestReport = report;
    alertSettings.value.reportHistory.unshift(report);
  } finally {
    alertSettings.value.generating = false;
  }
};

const exportReportPdf = () => {
  const report = alertSettings.value.latestReport;
  if (!report) return;
  const items = (report.alerts || [])
    .map((a) => {
      const snap = a.snapshot_url || a.snapshotUrl || "";
      const analysis = a.vl_analysis || a.vlAnalysis || "";
      return `<div style="page-break-inside:avoid;margin-bottom:20px;border:1px solid #ddd;padding:12px;border-radius:6px">
      <h4>${a.alertType || a.type || ""} — ${a.stream_id || a.streamId || ""}</h4>
      ${snap ? `<img src="${snap}" style="max-width:100%;max-height:300px;display:block;margin:8px 0" onerror="this.style.display='none'"/>` : ""}
      ${analysis ? `<p style="color:#555;font-size:13px">AI分析：${analysis}</p>` : ""}
    </div>`;
    })
    .join("");
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>日报_${report.date}</title><style>
    body{font-family:'Microsoft YaHei',sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#333}
    h1{text-align:center;border-bottom:2px solid #409EFF;padding-bottom:10px}
    h2{color:#409EFF;margin-top:24px}
    .summary{background:#f0f9ff;padding:16px;border-radius:8px;margin:16px 0;font-size:15px;line-height:1.8}
    @media print{body{padding:0}}
  </style></head><body>
    <h1>智慧教室安防日报 — ${report.date}</h1>
    <h2>AI 总结</h2><div class="summary">${report.summary || ""}</div>
    <h2>告警详情（${report.alertsCount || items.length} 条）</h2>${items}
    <p style="text-align:center;color:#999;margin-top:30px">智慧教室实时行为分析与安全监测系统</p>
  </body></html>`;

  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `日报_${report.date}.html`;
  a.click();
  URL.revokeObjectURL(url);
};
const alertKeyword = ref("");
const activeAlertLevel = ref("全部");
const activeAlertType = ref("全部");
const isVideoLive = ref(false);
const videoError = ref(false);
const streamSwitching = ref(false);
const isDay = ref(true);
const showAiAnnotations = ref(true);
const showRuleOverlay = ref(true);
const isVideoExpanded = ref(false);
const displayedRiskScore = ref(0);
const videoStageRef = ref(null);
const isDrawingForbiddenZone = ref(false);
const forbiddenZoneStart = ref(null);
const forbiddenZoneCurrent = ref(null);
const pendingForbiddenZone = ref(null);
const zoneSaving = ref(false);
const deletingZoneIds = ref(new Set());
const zoneDialogVisible = ref(false);
const zoneForm = ref({
  id: null,
  stream_id: "",
  zone_name: "",
  zone_type: "danger",
  coordinates: [],
  threshold_seconds: 3,
  safe_distance: 0.05,
  enabled: true,
});
const zoneFormSaving = ref(false);
const users = ref([]);
const usersLoading = ref(false);
const userRoleUpdatingId = ref(null);

const streams = ref([]);
const alerts = ref([]);
const rules = ref([]);
const zones = ref([]);
const students = ref([]);
const stats = ref({});
const health = ref({});
const summary = ref({});
const modelStatus = ref({});
const analysisEvents = ref([]);
const loadErrors = ref({});

let refreshId;
let riskScoreAnimationId;

const navItems = [
  { key: "monitor", label: "实时监控", icon: VideoCamera },
  { key: "alerts", label: "告警管理", icon: Bell },
  { key: "rules", label: "区域规则", icon: Setting },
  { key: "people", label: "人脸库", icon: User },
  { key: "users", label: "用户管理", icon: User, adminOnly: true },
  { key: "system", label: "系统状态", icon: Connection },
];

const statusOptions = [
  { label: "全部", value: "全部" },
  { label: "未处理", value: "unhandled" },
  { label: "处理中", value: "processing" },
  { label: "已处理", value: "handled" },
  { label: "误报", value: "false_alarm" },
  { label: "已忽略", value: "ignored" },
];

const zoneTypeOptions = [
  { label: "危险区", value: "danger" },
  { label: "手机禁用区", value: "phone_forbidden" },
];

const currentStream = computed(() => {
  return (
    streams.value.find((item) => item.stream_id === activeStreamId.value) ||
    streams.value[0] ||
    {}
  );
});

const videoFeedUrl = computed(() =>
  getVideoFeedUrl(activeStreamId.value, { annotate: showAiAnnotations.value }),
);

const dayTitle = computed(() => (isDay.value ? "白天模式" : "夜间模式"));
const dayHint = computed(() =>
  isDay.value ? "点击切换到护眼黑夜" : "点击切换到明亮白天",
);
const userDisplayName = computed(
  () =>
    currentUser.value?.nickname || currentUser.value?.username || "未登录用户",
);
const userRoleName = computed(() => {
  return (
    {
      admin: "管理员",
      teacher: "教师",
    }[currentUser.value?.role] || "未登录"
  );
});
const isAdmin = computed(() => currentUser.value?.role === "admin");
const visibleNavItems = computed(() =>
  navItems.filter((item) => !item.adminOnly || isAdmin.value),
);
const currentUserId = computed(
  () => currentUser.value?.user_id ?? currentUser.value?.id,
);

const confirmedForbiddenZones = computed(() =>
  zones.value
    .filter(
      (item) =>
        item.enabled !== false &&
        item.zone_type === "phone_forbidden" &&
        (!activeStreamId.value || item.stream_id === activeStreamId.value),
    )
    .map((item) => ({ ...item, rect: rectFromCoordinates(item.coordinates) }))
    .filter((item) => item.rect),
);
const hasConfirmedForbiddenZone = computed(
  () => confirmedForbiddenZones.value.length > 0,
);
const hasPendingForbiddenZone = computed(() =>
  Boolean(pendingForbiddenZone.value),
);
function isPhoneRelated(item = {}) {
  const text = [
    item.alert_type,
    item.event_type,
    item.rule_type,
    item.name,
    item.title,
    item.summary,
    item.description,
    item.text,
  ]
    .filter(Boolean)
    .join(" ");
  return /手机|phone/i.test(text);
}

const displayAlerts = computed(() => {
  return alerts.value.filter(
    (item) => !isPhoneRelated(item) || isPhoneItemInForbiddenZone(item),
  );
});

const alertLevelOptions = [
  { label: "全部等级", value: "全部" },
  { label: "最高", value: "critical" },
  { label: "高", value: "high" },
  { label: "警告", value: "warning" },
  { label: "中", value: "medium" },
  { label: "低", value: "low" },
];

const alertTypeOptions = computed(() => {
  const seen = new Map();
  displayAlerts.value.forEach((item) => {
    const value = item.alert_type || item.event_type || "unknown";
    if (!seen.has(value))
      seen.set(value, item.alert_name || alertTypeText(value));
  });
  return [
    { label: "全部类型", value: "全部" },
    ...Array.from(seen, ([value, label]) => ({ label, value })),
  ];
});

const activeStreamZones = computed(() =>
  zones.value.filter(
    (item) => !activeStreamId.value || item.stream_id === activeStreamId.value,
  ),
);

const zoneRows = computed(() => {
  return [...activeStreamZones.value];
});

const pendingAlertCount = computed(() => {
  return displayAlerts.value.filter((item) =>
    ["unhandled", "processing"].includes(item.status),
  ).length;
});
const criticalAlertCount = computed(
  () => displayAlerts.value.filter((item) => item.level === "critical").length,
);
const confirmedAlertCount = computed(
  () => displayAlerts.value.filter((item) => item.status === "handled").length,
);
const highAlertCount = computed(
  () => displayAlerts.value.filter((item) => item.level === "high").length,
);
const enabledRuleCount = computed(() => {
  return rules.value.filter(
    (item) =>
      item.enabled &&
      (hasConfirmedForbiddenZone.value || !isPhoneRelated(item)),
  ).length;
});
const registeredStudentCount = computed(
  () => students.value.filter((item) => item.face_registered).length,
);
const strangerCount = computed(
  () => students.value.filter((item) => !item.face_registered).length,
);
const adminUserCount = computed(
  () => users.value.filter((item) => item.role === "admin").length,
);
const enabledUserCount = computed(
  () => users.value.filter((item) => item.status === "enabled").length,
);
const userPageCards = computed(() => [
  { label: "用户总数", value: users.value.length, tone: "brand" },
  { label: "管理员", value: adminUserCount.value, tone: "danger" },
  {
    label: "教师账号",
    value: users.value.length - adminUserCount.value,
    tone: "warn",
  },
  { label: "已启用", value: enabledUserCount.value, tone: "ok" },
]);
const modelStreamStatusRecords = computed(() => {
  return Array.isArray(modelStatus.value?.streams)
    ? modelStatus.value.streams
    : [];
});
const allStreamStatusRecords = computed(() => {
  const records = [...streams.value];
  modelStreamStatusRecords.value.forEach((item) => {
    const streamId = item.stream_id || item.streamId;
    if (!streamId || records.some((stream) => stream.stream_id === streamId))
      return;
    records.push({
      stream_id: streamId,
      stream_name: item.stream_name || item.name || streamId,
      status:
        item.status ||
        item.stream_status ||
        item.online_status ||
        (item.online ? "online" : "unknown"),
    });
  });
  return records;
});
const onlineStreamCount = computed(
  () =>
    allStreamStatusRecords.value.filter((item) => isOnlineStatus(item.status))
      .length,
);

const healthItems = computed(() => [
  { label: "RTMP 流媒体", value: health.value.rtmp || "unknown" },
  { label: "AI 分析服务", value: health.value.ai || "unknown" },
  { label: "业务后端", value: health.value.api || "unknown" },
  { label: "MySQL 数据库", value: health.value.database || "unknown" },
]);

const metricCards = computed(() => [
  { label: "当前视频源", value: activeStreamId.value || "--", icon: Camera },
  {
    label: "平均延迟",
    value: currentStream.value.latency || stats.value.avg_latency || "--",
    icon: Clock,
  },
  {
    label: "今日识别人数",
    value: stats.value.recognized_count ?? stats.value.recognized_total ?? "--",
    icon: User,
  },
  { label: "待处理告警", value: pendingAlertCount.value, icon: Bell },
]);

const filteredAlerts = computed(() => {
  const keyword = alertKeyword.value.trim().toLowerCase();
  return displayAlerts.value.filter((item) => {
    if (
      activeAlertStatus.value !== "全部" &&
      item.status !== activeAlertStatus.value
    )
      return false;
    if (
      activeAlertLevel.value !== "全部" &&
      item.level !== activeAlertLevel.value
    )
      return false;
    if (
      activeAlertType.value !== "全部" &&
      item.alert_type !== activeAlertType.value
    )
      return false;
    if (!keyword) return true;
    return [
      item.alert_type,
      item.alert_name,
      item.stream_id,
      item.stream_name,
      item.student_name,
      item.remark,
      item.event_id,
      statusText(item.status),
      levelText(item.level),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(keyword);
  });
});

const highPriorityAlerts = computed(() => {
  return displayAlerts.value
    .filter((item) => item.level === "high")
    .slice(0, 4);
});

const activeRiskEvents = computed(() => {
  return deduplicateCrossSourceEvents(
    uniqueEvents([...alerts.value, ...analysisEvents.value])
      .filter((item) => {
        if (!isPhoneRelated(item)) return true;
        return isPhoneItemInForbiddenZone(item);
      })
      .map((item) => ({
        ...item,
        risk_type: classifyRiskType(item),
        risk_score: calculateEventRiskScore(item),
      })),
  )
    .filter((item) => item.risk_score > 0)
    .sort((a, b) => b.risk_score - a.risk_score)
    .slice(0, 8);
});

const hasActiveRiskEvents = computed(() => activeRiskEvents.value.length > 0);

const activeSummary = computed(() => {
  if (!activeRiskEvents.value.length) {
    return {
      risk_score: 0,
      title: "当前暂无高风险告警",
      summary: hasConfirmedForbiddenZone.value
        ? "当前禁用区内未发现手机违规，也没有明火、摔倒等高危告警命中。"
        : "当前未确认手机禁用区，手机违规检测暂不启用；明火、摔倒等高危告警会独立参与综合评分。",
      actions: hasConfirmedForbiddenZone.value
        ? ["持续监测", "保留禁用区", "等待 AI 命中"]
        : ["绘制禁用区", "确认坐标", "持续监测"],
      timeline: [
        {
          time: "当前",
          text: hasConfirmedForbiddenZone.value
            ? "区域规则已确认"
            : "手机规则等待禁用区坐标",
        },
        { time: "说明", text: "综合评分按告警类型、等级和置信度动态计算" },
      ],
    };
  }

  const topEvent = activeRiskEvents.value[0];
  const combinedScore = calculateCombinedRiskScore(activeRiskEvents.value);
  const topRiskText = riskTypeText(topEvent.risk_type);
  return {
    risk_score: combinedScore,
    title: `${topRiskText}风险：${topEvent.alert_name || topEvent.event_name || topEvent.alert_type || topEvent.event_type || "AI 告警"}`,
    summary: `综合 ${activeRiskEvents.value.length} 条有效告警计算，当前最高风险为${topRiskText}，分数由告警危急程度、等级和置信度共同决定。`,
    actions: buildRiskActions(activeRiskEvents.value),
    timeline: activeRiskEvents.value.slice(0, 3).map((item) => ({
      time: formatEventTime(item.occurred_at),
      text: `${riskTypeText(item.risk_type)} ${item.risk_score} 分：${item.alert_name || item.event_name || item.alert_type || item.event_type || "AI 告警"}`,
    })),
  };
});

const actionItems = computed(() => {
  return activeSummary.value.actions?.length
    ? activeSummary.value.actions
    : ["持续监测", "等待 AI 命中", "保留追踪记录"];
});

const targetRiskScore = computed(() => {
  if (!hasActiveRiskEvents.value) return 0;
  const score = Number(activeSummary.value?.risk_score ?? 0);
  return Math.min(100, Math.max(0, Number.isFinite(score) ? score : 0));
});

const alertPageCards = computed(() => [
  { label: "待处置事件", value: pendingAlertCount.value, tone: "danger" },
  { label: "高危事件", value: highAlertCount.value, tone: "warn" },
  { label: "已闭环", value: confirmedAlertCount.value, tone: "ok" },
  {
    label: "证据留存",
    value: `${displayAlerts.value.length} 条`,
    tone: "brand",
  },
]);

const rulePageCards = computed(() => [
  {
    label: "启用规则",
    value: `${enabledRuleCount.value}/${rules.value.length || 0}`,
    tone: "ok",
  },
  {
    label: "禁用区",
    value: hasConfirmedForbiddenZone.value
      ? `${confirmedForbiddenZones.value.length} 个已启用`
      : pendingForbiddenZone.value
        ? "待确认"
        : "未绘制",
    tone: "brand",
  },
  { label: "最高优先级", value: "按接口规则", tone: "danger" },
  { label: "复核窗口", value: "按规则阈值", tone: "warn" },
]);

const peoplePageCards = computed(() => [
  { label: "人员档案", value: students.value.length, tone: "brand" },
  { label: "已注册人脸", value: registeredStudentCount.value, tone: "ok" },
  { label: "待核验身份", value: strangerCount.value, tone: "warn" },
  {
    label: "最近出现",
    value: students.value[0]?.last_seen || "--",
    tone: "brand",
  },
]);

const systemPageCards = computed(() => [
  {
    label: "在线视频源",
    value: `${onlineStreamCount.value}/${allStreamStatusRecords.value.length || 0}`,
    tone: "ok",
  },
  {
    label: "模型版本",
    value: modelStatus.value.version || modelStatus.value.model_name || "--",
    tone: "brand",
  },
  {
    label: "推理耗时",
    value: modelStatus.value.inference_ms
      ? `${modelStatus.value.inference_ms} ms`
      : "--",
    tone: "warn",
  },
  {
    label: "服务状态",
    value: healthItems.value.every((item) => item.value === "online")
      ? "正常"
      : "需关注",
    tone: "ok",
  },
]);

const activeForbiddenRect = computed(() => {
  if (
    isDrawingForbiddenZone.value &&
    forbiddenZoneStart.value &&
    forbiddenZoneCurrent.value
  ) {
    return buildRectFromPoints(
      forbiddenZoneStart.value,
      forbiddenZoneCurrent.value,
    );
  }
  return pendingForbiddenZone.value?.rect || null;
});

const forbiddenZoneStyle = computed(() => {
  if (!activeForbiddenRect.value) return {};
  const rect = activeForbiddenRect.value;
  return {
    left: `${rect.x * 100}%`,
    top: `${rect.y * 100}%`,
    width: `${rect.width * 100}%`,
    height: `${rect.height * 100}%`,
  };
});

const forbiddenZoneCoordinates = computed(
  () => pendingForbiddenZone.value?.coordinates || [],
);

const phoneDetectionSources = computed(() => {
  return [...analysisEvents.value, ...alerts.value]
    .filter(isPhoneRelated)
    .map((item) => ({ item, rect: normalizeDetectionRect(item) }))
    .filter(({ rect }) => rect);
});

const phoneDetectionsInForbiddenZone = computed(() => {
  if (!confirmedForbiddenZones.value.length) return [];
  return phoneDetectionSources.value.filter(({ rect }) =>
    confirmedForbiddenZones.value.some((zone) =>
      rectsIntersect(zone.rect, rect),
    ),
  );
});

const isPhoneViolationInForbiddenZone = computed(() => {
  return phoneDetectionsInForbiddenZone.value.length > 0;
});

function isPhoneItemInForbiddenZone(item) {
  return phoneDetectionsInForbiddenZone.value.some(
    ({ item: source }) => source === item,
  );
}

function levelText(level) {
  return (
    {
      critical: "最高",
      high: "高",
      warning: "警告",
      medium: "中",
      info: "信息",
      low: "低",
    }[level] || "普通"
  );
}

function levelType(level) {
  return (
    {
      critical: "danger",
      high: "danger",
      warning: "warning",
      medium: "warning",
      info: "info",
      low: "info",
    }[level] || "info"
  );
}

function zoneTypeText(type) {
  return (
    {
      danger: "危险区",
      phone_forbidden: "手机禁用区",
    }[type] ||
    type ||
    "未分类"
  );
}

function zoneCoordinateText(zone = {}) {
  const points = Array.isArray(zone.coordinates) ? zone.coordinates : [];
  if (!points.length) return "暂无坐标";
  return points
    .slice(0, 4)
    .map((point) => {
      if (Array.isArray(point)) {
        return `(${formatCoord(point[0])}, ${formatCoord(point[1])})`;
      }
      return `(${formatCoord(point.x)}, ${formatCoord(point.y)})`;
    })
    .join(" / ");
}

function evidenceSummary(row = {}) {
  const hasSnapshot = !!row.snapshot_url;
  const hasRecord = !!row.record_url;
  if (hasSnapshot && hasRecord) return "截图 + 录像";
  if (hasSnapshot) return "已保存截图";
  if (hasRecord) return "仅录像";
  return "证据生成中";
}

function statusType(status) {
  return (
    {
      unhandled: "danger",
      processing: "warning",
      handled: "success",
      false_alarm: "info",
      ignored: "info",
      online: "success",
      enabled: "success",
      running: "success",
      active: "success",
      connected: "success",
      offline: "danger",
      disabled: "info",
      unknown: "info",
    }[status] || "info"
  );
}

function isOnlineStatus(status) {
  return ["online", "enabled", "running", "active", "connected", true].includes(
    status,
  );
}

function statusText(status) {
  return (
    {
      unhandled: "未处理",
      processing: "处理中",
      handled: "已处理",
      false_alarm: "误报",
      ignored: "已忽略",
      online: "在线",
      running: "运行中",
      active: "活跃",
      connected: "已连接",
      offline: "离线",
      enabled: "已启用",
      disabled: "已停用",
      unknown: "未知",
    }[status] ||
    status ||
    "--"
  );
}

function alertTypeText(type) {
  return (
    {
      fire_detected: "明火检测",
      smoke_detected: "烟雾检测",
      fall_detected: "摔倒检测",
      stranger_detected: "陌生人",
      phone_usage: "手机违规",
      head_down: "低头异常",
      zone_intrusion: "区域入侵",
      sleep_detected: "睡觉检测",
    }[type] ||
    type ||
    "--"
  );
}

function ruleNameText(rule) {
  const text = rule?.name || rule?.rule_name || rule?.rule_type || "";
  const mapped = {
    "Phone usage": "手机违规",
    "Fire detection": "明火检测",
    "Fall detection": "摔倒检测",
    "Head-down behavior": "低头异常",
  }[text];
  return mapped || alertTypeText(rule?.rule_type) || text || "--";
}

function ruleSummaryText(rule) {
  const summary = ruleSummary(rule);
  return (
    {
      "Enabled only after forbidden zone confirmation": "仅在确认禁用区后生效",
      "High-priority safety event": "高优先级安全事件",
      "Triggered after a sustained fall posture": "倒地持续确认后告警",
      "Evaluated by seat area and duration": "结合座位区域和时间窗口判断",
    }[summary] ||
    summary ||
    "--"
  );
}

function ruleSummary(rule) {
  if (!hasConfirmedForbiddenZone.value && isPhoneRelated(rule))
    return "等待禁用区确认后生效";
  return rule.summary;
}

function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  return (
    payload?.items || payload?.records || payload?.list || payload?.rows || []
  );
}

function normalizeHealth(payload) {
  return {
    rtmp: payload.rtmp || payload.rtmp_status || payload.media || "unknown",
    ai: payload.ai || payload.ai_status || "unknown",
    api: payload.api || payload.backend || "unknown",
    database: payload.database || payload.db || "unknown",
  };
}

function clampUnit(value) {
  return Math.min(1, Math.max(0, value));
}

function formatCoord(value) {
  return Number(value).toFixed(3);
}

function formatEventTime(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 16);
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function parseMaybeJson(value) {
  if (!value || typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function eventIdentity(item = {}) {
  const target = parseMaybeJson(
    item.target || item.target_info || item.targetInfo || {},
  );
  const bbox = target?.bbox || item.bbox || item.box || "";
  return [
    item.event_id || item.event_uid || item.id || "",
    item.alert_type || item.event_type || "",
    item.stream_id || "",
    item.occurred_at || item.time || "",
    Array.isArray(bbox) ? bbox.join(",") : JSON.stringify(bbox),
  ].join("|");
}

function uniqueEvents(items = []) {
  const seen = new Set();
  return items.filter((item) => {
    const key = eventIdentity(item);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function crossSourceEventKey(item = {}) {
  const type = item.alert_type || item.event_type || "";
  const streamId = item.stream_id || "";
  const occurredAt = item.occurred_at || item.time || "";
  const timeFloor = occurredAt
    ? new Date(occurredAt).getTime() - (new Date(occurredAt).getTime() % 5000)
    : "";
  return `${type}|${streamId}|${timeFloor}`;
}

function deduplicateCrossSourceEvents(events = []) {
  const groups = new Map();
  for (const event of events) {
    const key = crossSourceEventKey(event);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(event);
  }
  const result = [];
  for (const [, group] of groups) {
    if (group.length === 1) {
      result.push(group[0]);
      continue;
    }
    const withScore = group.filter(
      (item) => (item.risk_score ?? calculateEventRiskScore(item)) > 0,
    );
    if (withScore.length > 0) {
      withScore.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
      result.push(withScore[0]);
    } else {
      group.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
      result.push(group[0]);
    }
  }
  return result;
}

function getRiskText(item = {}) {
  return [
    item.alert_type,
    item.alert_name,
    item.event_type,
    item.event_name,
    item.rule_type,
    item.name,
    item.remark,
    item.summary,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function classifyRiskType(item = {}) {
  const text = getRiskText(item);
  if (/fire|smoke|flame|明火|烟雾|火/.test(text)) return "fire";
  if (/fall|摔倒|跌倒|倒地/.test(text)) return "fall";
  if (/stranger|unknown_person|陌生人|未登记/.test(text)) return "stranger";
  if (/phone|手机/.test(text)) return "phone";
  if (/head_down|sleep|低头|睡觉|趴桌/.test(text)) return "behavior";
  if (/zone|intrusion|越界|闯入/.test(text)) return "zone";
  return "general";
}

function riskTypeText(type) {
  return (
    {
      fire: "明火",
      fall: "摔倒",
      stranger: "陌生人",
      phone: "手机违规",
      behavior: "行为异常",
      zone: "区域入侵",
      general: "综合",
    }[type] || "综合"
  );
}

function riskBaseScore(type) {
  const matched = riskScoreSettings.value.find((item) => item.type === type);
  return Number(
    matched?.score ??
      riskScoreSettings.value.find((item) => item.type === "general")?.score ??
      0,
  );
}

async function handleScoreConfigChange(item) {
  if (!item.id) return;
  try {
    await updateScoreConfig(item.id, { score: item.score });
  } catch (e) {
    ElMessage.error("评分配置保存失败：" + (e.message || "未知错误"));
  }
}

function levelRiskBonus(level) {
  return (
    {
      critical: 8,
      high: 5,
      warning: 2,
      medium: 0,
      info: -8,
      low: -12,
    }[level] ?? 0
  );
}

function calculateEventRiskScore(item = {}) {
  const type = classifyRiskType(item);
  if (type === "phone" && !isPhoneViolationInForbiddenZone.value) return 0;
  const confidence = Number(item.confidence ?? item.target?.confidence);
  const confidenceBonus = Number.isFinite(confidence)
    ? Math.round((confidence - 0.75) * 24)
    : 0;
  const rawScore =
    riskBaseScore(type) + levelRiskBonus(item.level) + confidenceBonus;
  return Math.min(100, Math.max(1, rawScore));
}

function calculateCombinedRiskScore(events = []) {
  if (!events.length) return 0;
  const sortedScores = events
    .map((item) => item.risk_score)
    .filter(Number.isFinite)
    .sort((a, b) => b - a);
  const topScore = sortedScores[0] || 0;
  const secondaryScore = sortedScores
    .slice(1, 4)
    .reduce((sum, score) => sum + score * 0.12, 0);
  return Math.min(100, Math.round(topScore + secondaryScore));
}

function buildRiskActions(events = []) {
  const types = new Set(events.map((item) => item.risk_type));
  if (types.has("fire"))
    return ["立即人工确认", "联动现场处置", "保留截图录像"];
  if (types.has("fall"))
    return ["确认人员状态", "通知现场老师", "保留追踪记录"];
  if (types.has("phone")) return ["复核禁用区", "等待人工确认", "保留证据链"];
  if (types.has("stranger")) return ["核验身份", "查看人脸库", "登记处理结果"];
  return ["持续监测", "复核 AI 标注", "保留追踪记录"];
}

function getVideoPointerPoint(event) {
  const stage = event.currentTarget || videoStageRef.value;
  if (!stage) return null;
  const rect = stage.getBoundingClientRect();
  return {
    x: clampUnit((event.clientX - rect.left) / rect.width),
    y: clampUnit((event.clientY - rect.top) / rect.height),
  };
}

function buildRectFromPoints(start, end) {
  const x1 = Math.min(start.x, end.x);
  const y1 = Math.min(start.y, end.y);
  const x2 = Math.max(start.x, end.x);
  const y2 = Math.max(start.y, end.y);
  return {
    x: x1,
    y: y1,
    width: x2 - x1,
    height: y2 - y1,
  };
}

function buildCoordinatesFromRect(rect) {
  return [
    { x: Number(rect.x.toFixed(4)), y: Number(rect.y.toFixed(4)) },
    {
      x: Number((rect.x + rect.width).toFixed(4)),
      y: Number(rect.y.toFixed(4)),
    },
    {
      x: Number((rect.x + rect.width).toFixed(4)),
      y: Number((rect.y + rect.height).toFixed(4)),
    },
    {
      x: Number(rect.x.toFixed(4)),
      y: Number((rect.y + rect.height).toFixed(4)),
    },
  ];
}

function rectFromCoordinates(coordinates = []) {
  if (!Array.isArray(coordinates) || coordinates.length < 2) return null;
  const points = coordinates
    .map((point) => ({
      x: Number(point.x ?? point[0]),
      y: Number(point.y ?? point[1]),
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
  if (points.length < 2) return null;
  const xs = points.map((point) => clampUnit(point.x));
  const ys = points.map((point) => clampUnit(point.y));
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  const right = Math.max(...xs);
  const bottom = Math.max(...ys);
  return {
    x: left,
    y: top,
    width: right - left,
    height: bottom - top,
  };
}

function rectFromBbox(bbox = [], source = {}) {
  if (!Array.isArray(bbox) || bbox.length < 4) return null;
  const [x1, y1, x2, y2] = bbox.map(Number);
  if (![x1, y1, x2, y2].every(Number.isFinite)) return null;

  const maxValue = Math.max(x1, y1, x2, y2);
  if (maxValue <= 1) {
    return {
      x: clampUnit(Math.min(x1, x2)),
      y: clampUnit(Math.min(y1, y2)),
      width: clampUnit(Math.abs(x2 - x1)),
      height: clampUnit(Math.abs(y2 - y1)),
    };
  }

  const target = parseMaybeJson(
    source.target || source.target_info || source.targetInfo || {},
  );
  const frameWidth = Number(
    source.frame_width ||
      source.width ||
      source.video_width ||
      target?.frame_width ||
      target?.frameWidth ||
      640,
  );
  const frameHeight = Number(
    source.frame_height ||
      source.height ||
      source.video_height ||
      target?.frame_height ||
      target?.frameHeight ||
      360,
  );

  return {
    x: clampUnit(Math.min(x1, x2) / frameWidth),
    y: clampUnit(Math.min(y1, y2) / frameHeight),
    width: clampUnit(Math.abs(x2 - x1) / frameWidth),
    height: clampUnit(Math.abs(y2 - y1) / frameHeight),
  };
}

function normalizeDetectionRect(item = {}) {
  const target = parseMaybeJson(
    item.target || item.target_info || item.targetInfo || {},
  );
  const candidate =
    item.bbox ||
    target.bbox ||
    item.box ||
    target.box ||
    item.rect ||
    target.rect ||
    item.target_rect ||
    item.coordinates ||
    item.target_coordinates ||
    item.zone_coordinates;

  const parsedCandidate = parseMaybeJson(candidate);

  if (Array.isArray(parsedCandidate)) {
    return parsedCandidate.length === 4 &&
      parsedCandidate.every((value) => Number.isFinite(Number(value)))
      ? rectFromBbox(parsedCandidate, { ...item, target })
      : rectFromCoordinates(parsedCandidate);
  }

  if (parsedCandidate && typeof parsedCandidate === "object") {
    const x = Number(parsedCandidate.x ?? parsedCandidate.left);
    const y = Number(parsedCandidate.y ?? parsedCandidate.top);
    const width = Number(parsedCandidate.width ?? parsedCandidate.w);
    const height = Number(parsedCandidate.height ?? parsedCandidate.h);
    if ([x, y, width, height].every(Number.isFinite)) {
      return {
        x: clampUnit(x),
        y: clampUnit(y),
        width: clampUnit(width),
        height: clampUnit(height),
      };
    }
  }

  return null;
}

function rectsIntersect(a, b) {
  if (!a || !b) return false;
  const aRight = a.x + a.width;
  const aBottom = a.y + a.height;
  const bRight = b.x + b.width;
  const bBottom = b.y + b.height;
  const overlapWidth = Math.min(aRight, bRight) - Math.max(a.x, b.x);
  const overlapHeight = Math.min(aBottom, bBottom) - Math.max(a.y, b.y);
  return overlapWidth > 0 && overlapHeight > 0;
}

function resetForbiddenZoneDraft() {
  pendingForbiddenZone.value = null;
  cancelForbiddenZoneDraw();
}

function startForbiddenZoneDraw(event) {
  if (!showRuleOverlay.value) return;
  if (event.button !== 0) return;
  const point = getVideoPointerPoint(event);
  if (!point) return;
  isDrawingForbiddenZone.value = true;
  forbiddenZoneStart.value = point;
  forbiddenZoneCurrent.value = point;
}

function updateForbiddenZoneDraw(event) {
  if (!showRuleOverlay.value || !isDrawingForbiddenZone.value) return;
  const point = getVideoPointerPoint(event);
  if (!point) return;
  forbiddenZoneCurrent.value = point;
}

function finishForbiddenZoneDraw() {
  if (
    !isDrawingForbiddenZone.value ||
    !forbiddenZoneStart.value ||
    !forbiddenZoneCurrent.value
  )
    return;
  const rect = buildRectFromPoints(
    forbiddenZoneStart.value,
    forbiddenZoneCurrent.value,
  );
  isDrawingForbiddenZone.value = false;
  forbiddenZoneStart.value = null;
  forbiddenZoneCurrent.value = null;
  if (rect.width < 0.015 || rect.height < 0.015) return;
  const nextIndex = activeStreamZones.value.length + 1;
  pendingForbiddenZone.value = {
    rect,
    coordinates: buildCoordinatesFromRect(rect),
    zone_name: `危险区 ${nextIndex}`,
    zone_type: "danger",
  };
}

function cancelForbiddenZoneDraw() {
  isDrawingForbiddenZone.value = false;
  forbiddenZoneStart.value = null;
  forbiddenZoneCurrent.value = null;
}

async function confirmForbiddenZone() {
  if (!pendingForbiddenZone.value || !activeStreamId.value || zoneSaving.value)
    return;
  if (!pendingForbiddenZone.value.zone_name?.trim()) {
    ElMessage.warning("请填写区域名称。");
    return;
  }
  zoneSaving.value = true;
  try {
    const created = await createZone({
      stream_id: activeStreamId.value,
      zone_name: pendingForbiddenZone.value.zone_name.trim(),
      zone_type: pendingForbiddenZone.value.zone_type,
      coordinates: pendingForbiddenZone.value.coordinates,
      threshold_seconds: 3,
      safe_distance:
        pendingForbiddenZone.value.zone_type === "danger" ? 0.05 : 0,
    });
    zones.value = [
      ...zones.value.filter((item) => item.id !== created.id),
      created,
    ];
    pendingForbiddenZone.value = null;
    ElMessage.success("区域已保存，后续标注由 AI 视频流统一绘制。");
  } catch (error) {
    ElMessage.error(error?.message || "禁用区保存失败，请检查后端服务。");
  } finally {
    zoneSaving.value = false;
  }
}

function clearForbiddenZone() {
  resetForbiddenZoneDraft();
}

function toggleAiAnnotations() {
  showAiAnnotations.value = !showAiAnnotations.value;
}

function openZoneDialog(zone) {
  zoneForm.value = {
    id: zone.id ?? zone.zone_id,
    stream_id: zone.stream_id || "",
    zone_name: zone.zone_name || "",
    zone_type: zone.zone_type || "danger",
    coordinates: zone.coordinates || [],
    threshold_seconds: zone.threshold_seconds ?? 3,
    safe_distance: zone.safe_distance ?? 0.05,
    enabled: zone.enabled ?? true,
  };
  zoneDialogVisible.value = true;
}

async function saveZone() {
  const form = zoneForm.value;
  if (!form.zone_name.trim()) {
    ElMessage.warning("请填写区域名称。");
    return;
  }
  if (!form.stream_id) {
    ElMessage.warning("请选择视频源。");
    return;
  }
  zoneFormSaving.value = true;
  try {
    await updateZone(form.id, {
      zone_name: form.zone_name.trim(),
      zone_type: form.zone_type,
      coordinates: form.coordinates,
      threshold_seconds: form.threshold_seconds,
      safe_distance: form.safe_distance,
      enabled: form.enabled,
    });
    zones.value = zones.value.map((item) =>
      (item.id ?? item.zone_id) === form.id
        ? {
            ...item,
            zone_name: form.zone_name.trim(),
            zone_type: form.zone_type,
            threshold_seconds: form.threshold_seconds,
            safe_distance: form.safe_distance,
            enabled: form.enabled,
          }
        : item,
    );
    ElMessage.success("区域已更新。");
    zoneDialogVisible.value = false;
  } catch (error) {
    ElMessage.error(error?.message || "区域保存失败。");
  } finally {
    zoneFormSaving.value = false;
  }
}

async function handleDeleteZone(zone) {
  const id = zone?.id ?? zone?.zone_id;
  if (id === undefined || id === null || deletingZoneIds.value.has(id)) return;
  try {
    await ElMessageBox.confirm(
      `确定删除"${zone.zone_name || "该区域"}"吗？`,
      "删除区域",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" },
    );
  } catch {
    return;
  }
  deletingZoneIds.value = new Set([...deletingZoneIds.value, id]);
  try {
    await deleteZone(id);
    zones.value = zones.value.filter(
      (item) => (item.id ?? item.zone_id) !== id,
    );
    ElMessage.success(`${zone.zone_name || "区域"}已删除。`);
  } catch (error) {
    ElMessage.error(error?.message || "区域删除失败。");
  } finally {
    const nextIds = new Set(deletingZoneIds.value);
    nextIds.delete(id);
    deletingZoneIds.value = nextIds;
  }
}

async function handleToggleZone(zone) {
  const id = zone?.id ?? zone?.zone_id;
  const newEnabled = !zone.enabled;
  try {
    await toggleZone(id, newEnabled);
    zones.value = zones.value.map((item) =>
      (item.id ?? item.zone_id) === id
        ? { ...item, enabled: newEnabled }
        : item,
    );
  } catch (error) {
    ElMessage.error(error?.message || "切换区域开关失败。");
  }
}

async function handleToggleRule(rule) {
  const id = rule?.id;
  const newEnabled = !rule.enabled;
  try {
    await toggleRule(id, newEnabled);
    rules.value = rules.value.map((item) =>
      item.id === id ? { ...item, enabled: newEnabled } : item,
    );
  } catch (error) {
    ElMessage.error(error?.message || "切换规则开关失败。");
  }
}

async function loadUsers() {
  if (!isAdmin.value) {
    users.value = [];
    return;
  }
  usersLoading.value = true;
  try {
    const result = await fetchUsers({ page: 1, page_size: 100 });
    users.value = normalizeList(result);
    loadErrors.value.users = "";
  } catch (error) {
    users.value = [];
    loadErrors.value.users = error?.message || "用户列表接口请求失败";
    ElMessage.error(loadErrors.value.users);
  } finally {
    usersLoading.value = false;
  }
}

async function handleUserRoleChange(user, role) {
  if (!isAdmin.value || !user?.id || user.role === role) return;
  if (String(user.id) === String(currentUserId.value)) {
    ElMessage.warning("不能修改自己的角色。");
    return;
  }
  userRoleUpdatingId.value = user.id;
  try {
    await updateUserRole(user.id, role);
    users.value = users.value.map((item) =>
      item.id === user.id ? { ...item, role } : item,
    );
    ElMessage.success(`${user.username} 的权限已更新。`);
  } catch (error) {
    ElMessage.error(error?.message || "用户权限更新失败。");
  } finally {
    userRoleUpdatingId.value = null;
  }
}

function navigateToPage(page) {
  if (page === "users" && !isAdmin.value) return;
  activePage.value = page;
  if (page === "users") loadUsers();
}

function toggleRuleOverlay() {
  showRuleOverlay.value = !showRuleOverlay.value;
  if (!showRuleOverlay.value) cancelForbiddenZoneDraw();
}

function openExpandedVideo() {
  isVideoExpanded.value = true;
}

function closeExpandedVideo() {
  isVideoExpanded.value = false;
}

function animateRiskScore(nextScore) {
  window.cancelAnimationFrame(riskScoreAnimationId);
  const startScore = displayedRiskScore.value;
  const delta = nextScore - startScore;
  const duration = Math.min(1400, Math.max(520, Math.abs(delta) * 20));
  const startedAt = performance.now();

  const step = (now) => {
    const progress = Math.min(1, (now - startedAt) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    displayedRiskScore.value = Number((startScore + delta * eased).toFixed(1));
    if (progress < 1) {
      riskScoreAnimationId = window.requestAnimationFrame(step);
    }
  };

  riskScoreAnimationId = window.requestAnimationFrame(step);
}

function setAuthNotice(message, type = "info") {
  authNotice.value = message;
  authNoticeType.value = type;
}

function normalizeUser(loginPayload, username) {
  const user =
    loginPayload?.user || loginPayload?.user_info || loginPayload || {};
  return {
    user_id: user.user_id || user.id || "",
    username: user.username || username,
    nickname: user.nickname || user.name || username,
    role: user.role || "teacher",
    avatar_url: user.avatar_url || "",
  };
}

async function enterAuthenticatedApp(user, token, remember = true) {
  currentUser.value = user;
  isAuthenticated.value = true;
  activePage.value = "monitor";
  storeAuthSession(token, user, remember);
  await loadDashboard();
  startAlertRefresh();
}

async function submitLogin() {
  if (!authForm.value.username || !authForm.value.password) {
    setAuthNotice("请输入用户名和密码。", "warning");
    return;
  }

  authLoading.value = true;
  setAuthNotice("");
  try {
    const payload = await login(authForm.value);
    const token = payload?.token || payload?.access_token || payload?.jwt || "";
    const user = normalizeUser(payload, authForm.value.username);
    if (!token) {
      throw new Error("登录响应缺少 token");
    }
    await enterAuthenticatedApp(user, token, authForm.value.remember);
  } catch (error) {
    setAuthNotice(
      error?.message || "登录失败，请确认后端认证接口可用且账号密码正确。",
      "error",
    );
  } finally {
    authLoading.value = false;
  }
}

async function submitDeveloperLogin() {
  window.__SMART_CLASS_CONFIG__ = {
    ...(window.__SMART_CLASS_CONFIG__ || {}),
    USE_MOCK: true,
  };
  const user = {
    user_id: "dev-local",
    username: "dev",
    nickname: "开发者模式",
    role: "admin",
    avatar_url: "",
  };
  setAuthNotice(
    "已进入开发者模式：当前使用本地 mock 数据，不代表真实后端登录。",
    "warning",
  );
  await enterAuthenticatedApp(user, "dev-local-token", false);
}

async function submitRegister() {
  if (!registerForm.value.username || registerForm.value.username.length < 2) {
    setAuthNotice("用户名至少 2 个字符。", "warning");
    return;
  }
  if (!registerForm.value.password || registerForm.value.password.length < 6) {
    setAuthNotice("密码至少 6 个字符。", "warning");
    return;
  }
  authLoading.value = true;
  setAuthNotice("");
  try {
    const payload = await register(registerForm.value);
    const token = payload?.token || payload?.access_token || payload?.jwt || "";
    const user = normalizeUser(payload, registerForm.value.username);
    if (!token) throw new Error("注册响应缺少 token");
    await enterAuthenticatedApp(user, token, true);
  } catch (error) {
    setAuthNotice(
      error?.message || "注册请求失败，请确认后端服务可用。",
      "error",
    );
  } finally {
    authLoading.value = false;
  }
}

async function handleLogout() {
  await logout();
  clearAuthSession();
  isAuthenticated.value = false;
  currentUser.value = null;
  window.clearInterval(refreshId);
  refreshId = undefined;
  setAuthNotice("已退出登录。", "success");
}

function startAlertRefresh() {
  window.clearInterval(refreshId);
  refreshId = window.setInterval(() => {
    fetchAlerts({ stream_id: activeStreamId.value, page: 1, page_size: 20 })
      .then((payload) => {
        alerts.value = normalizeList(payload);
        loadErrors.value.alerts = "";
      })
      .catch((error) => {
        loadErrors.value.alerts = error?.message || "告警接口请求失败";
      });
  }, 5000);
}

async function loadDashboard() {
  const previousStreamId = activeStreamId.value;
  const requests = {
    streams: fetchStreams(),
    alerts: fetchAlerts({
      stream_id: activeStreamId.value,
      page: 1,
      page_size: 20,
    }),
    stats: fetchAlertStats({ stream_id: activeStreamId.value }),
    rules: fetchRules(),
    zones: fetchZones({ stream_id: activeStreamId.value }),
    scoreConfig: fetchScoreConfig(),
    students: fetchStudents({ page: 1, page_size: 10 }),
    users: isAdmin.value
      ? fetchUsers({ page: 1, page_size: 100 })
      : Promise.resolve({ records: [] }),
    health: fetchSystemHealth(),
    summary: activeStreamId.value
      ? fetchAnalysisSummary(activeStreamId.value)
      : Promise.resolve({}),
    events: activeStreamId.value
      ? fetchAnalysisEvents({ stream_id: activeStreamId.value })
      : Promise.resolve([]),
    model: fetchModelStatus(),
  };

  const entries = await Promise.all(
    Object.entries(requests).map(async ([key, promise]) => {
      try {
        return [key, { ok: true, value: await promise }];
      } catch (error) {
        return [key, { ok: false, error }];
      }
    }),
  );
  const results = Object.fromEntries(entries);
  loadErrors.value = Object.fromEntries(
    Object.entries(results)
      .filter(([, result]) => !result.ok)
      .map(([key, result]) => [key, result.error?.message || "接口请求失败"]),
  );

  streams.value = results.streams.ok
    ? normalizeList(results.streams.value)
    : [];
  alerts.value = results.alerts.ok ? normalizeList(results.alerts.value) : [];
  stats.value = results.stats.ok ? results.stats.value || {} : {};
  rules.value = results.rules.ok ? normalizeList(results.rules.value) : [];
  zones.value = results.zones.ok ? normalizeList(results.zones.value) : [];
  if (results.scoreConfig.ok && Array.isArray(results.scoreConfig.value)) {
    riskScoreSettings.value = results.scoreConfig.value.map((item) => ({
      id: item.id,
      type: item.alert_type,
      label: item.label,
      score: item.score,
      note: item.note || "",
    }));
  }
  students.value = results.students.ok
    ? normalizeList(results.students.value)
    : [];
  users.value = results.users.ok ? normalizeList(results.users.value) : [];
  health.value = results.health.ok
    ? normalizeHealth(results.health.value || {})
    : normalizeHealth({});
  summary.value = results.summary.ok ? results.summary.value || {} : {};
  analysisEvents.value = results.events.ok
    ? normalizeList(results.events.value)
    : [];
  modelStatus.value = results.model.ok ? results.model.value || {} : {};

  if (
    !streams.value.some((item) => item.stream_id === activeStreamId.value) &&
    streams.value[0]
  ) {
    activeStreamId.value = streams.value[0].stream_id;
  }

  if (!previousStreamId && activeStreamId.value) {
    try {
      const [nextSummary, nextEvents, nextZones] = await Promise.all([
        fetchAnalysisSummary(activeStreamId.value),
        fetchAnalysisEvents({ stream_id: activeStreamId.value }),
        fetchZones({ stream_id: activeStreamId.value }),
      ]);
      summary.value = nextSummary || {};
      analysisEvents.value = normalizeList(nextEvents);
      zones.value = normalizeList(nextZones);
    } catch (error) {
      loadErrors.value.summary = error?.message || "AI 分析接口请求失败";
    }
  }
}

async function switchStream(streamId) {
  activeStreamId.value = streamId;
  isVideoLive.value = false;
  videoError.value = false;
  streamSwitching.value = true;
  resetForbiddenZoneDraft();
  try {
    const [nextSummary, nextEvents, nextZones] = await Promise.all([
      fetchAnalysisSummary(streamId),
      fetchAnalysisEvents({ stream_id: streamId }),
      fetchZones({ stream_id: streamId }),
    ]);
    summary.value = nextSummary || {};
    analysisEvents.value = normalizeList(nextEvents);
    zones.value = normalizeList(nextZones);
    loadErrors.value.summary = "";
    loadErrors.value.events = "";
  } catch (error) {
    summary.value = {};
    analysisEvents.value = [];
    loadErrors.value.summary = error?.message || "AI 分析接口请求失败";
  } finally {
    streamSwitching.value = false;
  }
}

function handleVideoLoad() {
  isVideoLive.value = true;
  videoError.value = false;
}

function handleVideoError() {
  isVideoLive.value = false;
  videoError.value = true;
}

function resourceUrl(path) {
  return joinResourceUrl(path);
}

function openReplayDialog(row) {
  replayUrl.value = resourceUrl(row.record_url);
  replayOffset.value = row.event_time_offset ?? 0;
  replayVisible.value = true;
}

function onReplayReady() {
  if (replayVideoRef.value && replayOffset.value > 0) {
    replayVideoRef.value.currentTime = replayOffset.value;
  }
  if (replayVideoRef.value) {
    replayVideoRef.value.play().catch(() => {});
  }
}

function closeReplayDialog() {
  if (replayVideoRef.value) {
    replayVideoRef.value.pause();
    replayVideoRef.value.src = "";
  }
  replayVisible.value = false;
}

function toggleThemeMode() {
  isDay.value = !isDay.value;
}

function openPersonDialog() {
  personForm.value = {
    student_no: `P${String(Date.now()).slice(-6)}`,
    name: "",
    class_name: "",
    face_registered: false,
  };
  newPersonFaceImageBase64.value = "";
  newPersonFaceImageName.value = "";
  newPersonFaceValidationMessage.value = "";
  personDialogVisible.value = true;
}

async function savePerson() {
  const form = personForm.value;
  if (!form.name.trim()) {
    ElMessage.warning("请填写人员姓名。");
    return;
  }
  const localPerson = {
    id: Date.now(),
    student_no: form.student_no.trim() || `P${String(Date.now()).slice(-6)}`,
    name: form.name.trim(),
    class_name: form.class_name.trim() || "未分组",
    status: "active",
    face_registered: false,
    last_seen: "--",
  };
  let savedPerson = localPerson;
  try {
    const created = await createStudent(localPerson);
    savedPerson = {
      ...created,
      face_registered: Boolean(created.face_registered),
    };
  } catch (error) {
    if (!isMockEnabled()) {
      ElMessage.error(error?.message || "新增人员接口请求失败。");
      return;
    }
    ElMessage.warning("人员接口不可用，已在开发模式下临时新增人员。");
  }

  if (newPersonFaceImageBase64.value) {
    if (!savedPerson.id) {
      ElMessage.warning("人员已新增，但后端未返回人员 ID，暂时无法注册人脸。");
    } else {
      try {
        await registerStudentFace(
          savedPerson.id,
          newPersonFaceImageBase64.value,
        );
        savedPerson = { ...savedPerson, face_registered: true };
        ElMessage.success("人员信息和人脸图片已提交。");
      } catch (error) {
        if (!isMockEnabled()) {
          students.value = [savedPerson, ...students.value];
          personDialogVisible.value = false;
          ElMessage.error(
            error?.message || "人员已新增，但人脸注册接口请求失败。",
          );
          return;
        }
        savedPerson = { ...savedPerson, face_registered: true };
        ElMessage.warning("人脸注册接口不可用，开发模式下已临时标记为已注册。");
      }
    }
  } else {
    ElMessage.success("已新增人员，后续可在人脸库中补录人脸。");
  }
  students.value = [savedPerson, ...students.value];
  personDialogVisible.value = false;
}

function openStreamDialog() {
  streamForm.value = {
    stream_id: `stream_${String(Date.now()).slice(-5)}`,
    stream_name: "",
    location: "",
    rtmp_url: "",
    status: "online",
  };
  streamDialogVisible.value = true;
}

async function saveStream() {
  const form = streamForm.value;
  if (
    !form.stream_id.trim() ||
    !form.stream_name.trim() ||
    !form.rtmp_url.trim()
  ) {
    ElMessage.warning("请填写视频源编号、名称和 RTMP 地址。");
    return;
  }
  if (streams.value.some((item) => item.stream_id === form.stream_id.trim())) {
    ElMessage.warning("视频源编号已存在，请换一个。");
    return;
  }
  const localStream = {
    id: Date.now(),
    stream_id: form.stream_id.trim(),
    stream_name: form.stream_name.trim(),
    location: form.location.trim() || "未填写位置",
    status: form.status,
    latency: "--",
    rtmp_url: form.rtmp_url.trim(),
    remark: "前端临时新增",
  };
  try {
    const created = await createStream(localStream);
    streams.value = [created, ...streams.value];
    activeStreamId.value = created.stream_id;
    ElMessage.success("已通过接口新增视频源。");
  } catch (error) {
    if (!isMockEnabled()) {
      ElMessage.error(error?.message || "新增视频源接口请求失败。");
      return;
    }
    streams.value = [localStream, ...streams.value];
    activeStreamId.value = localStream.stream_id;
    ElMessage.warning("接口不可用，已在开发模式下临时新增视频源。");
  }
  streamDialogVisible.value = false;
}

function openFaceDialog(row) {
  selectedStudent.value = row;
  faceImageBase64.value = "";
  faceImageName.value = "";
  faceValidationMessage.value = "";
  faceDialogVisible.value = true;
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("图片读取失败，请重新选择。"));
    reader.readAsDataURL(file);
  });
}

function loadImage(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () =>
      reject(new Error("图片解析失败，请选择常见格式的人脸照片。"));
    image.src = dataUrl;
  });
}

function calculateSharpness(image) {
  const size = 180;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.drawImage(image, 0, 0, size, size);
  const { data } = context.getImageData(0, 0, size, size);
  const gray = new Float32Array(size * size);
  for (let i = 0, p = 0; i < data.length; i += 4, p += 1) {
    gray[p] = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
  }
  let sum = 0;
  let sumSquares = 0;
  let count = 0;
  for (let y = 1; y < size - 1; y += 1) {
    for (let x = 1; x < size - 1; x += 1) {
      const index = y * size + x;
      const value =
        gray[index - size] +
        gray[index - 1] -
        gray[index] * 4 +
        gray[index + 1] +
        gray[index + size];
      sum += value;
      sumSquares += value * value;
      count += 1;
    }
  }
  const mean = sum / count;
  return sumSquares / count - mean * mean;
}

async function detectFaceBox(image) {
  if (!("FaceDetector" in window)) return null;
  const detector = new window.FaceDetector({ fastMode: false });
  const faces = await detector.detect(image);
  if (faces.length !== 1) {
    throw new Error("图片中必须且只能识别到一张人脸。");
  }
  const box = faces[0].boundingBox || {};
  if ((box.width || 0) < 160 || (box.height || 0) < 160) {
    throw new Error("人脸区域像素过低，请上传更近、更清晰的正脸照片。");
  }
  return box;
}

function hasFaceFeature(payload = {}) {
  const faceCount = payload.face_count ?? payload.faceCount ?? payload.count;
  if (faceCount !== undefined && Number(faceCount) < 1) return false;
  const feature =
    payload.feature ||
    payload.face_feature ||
    payload.feature_vector ||
    payload.embedding ||
    payload.vector;
  if (Array.isArray(feature)) return feature.length > 0;
  if (payload.face_detected === true || payload.detected === true) return true;
  if (Array.isArray(payload.faces)) return payload.faces.length > 0;
  return Boolean(feature);
}

function normalizeFaceValidationError(error) {
  const status = error?.response?.status;
  const code = error?.response?.data?.code;
  const message = error?.message || "";
  if (status >= 500) {
    return "AI 人脸识别服务异常，请确认 AI 服务已启动且人脸模型加载正常。";
  }
  if (code === 40001 || message.includes("invalid image")) {
    return "图片格式无效，请重新选择清晰的人脸照片。";
  }
  if (code === 40002 || message.includes("no face")) {
    return "AI 未识别到人脸，请上传正脸清晰照片。";
  }
  if (code === 40003 || message.includes("multiple")) {
    return "图片中识别到多张人脸，请上传单人脸照片。";
  }
  if (message.includes("Network Error")) {
    return "无法连接 AI 人脸识别服务，请检查 VITE_AI_BASE 或服务端口。";
  }
  return message || "人脸图片校验失败。";
}

async function validateFaceFile(file, studentId) {
  if (!file.type.startsWith("image/")) {
    throw new Error("请选择图片文件。");
  }
  const dataUrl = await readFileAsDataUrl(file);
  const base64 = dataUrl.split(",")[1] || "";
  const image = await loadImage(dataUrl);
  const minSide = Math.min(image.naturalWidth, image.naturalHeight);
  if (minSide < 360) {
    throw new Error("图片分辨率过低，短边至少需要 360 像素。");
  }
  const sharpness = calculateSharpness(image);
  if (sharpness < 22) {
    throw new Error("图片清晰度不足，请上传无明显模糊的人脸照片。");
  }
  await detectFaceBox(image);
  let result = null;
  try {
    result = await extractFaceFeature(base64, studentId);
  } catch (error) {
    throw new Error(normalizeFaceValidationError(error));
  }
  if (!hasFaceFeature(result)) {
    throw new Error("AI 未能从图片中提取到有效人脸特征，请更换正脸高清照片。");
  }
  return { base64, name: file.name };
}

async function handleFaceFileChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  faceImageBase64.value = "";
  faceImageName.value = "";
  faceValidationMessage.value = "正在检测图片清晰度和人脸特征...";
  faceValidationLoading.value = true;
  try {
    const validated = await validateFaceFile(
      file,
      selectedStudent.value?.student_no ||
        selectedStudent.value?.id ||
        "preview",
    );
    faceImageBase64.value = validated.base64;
    faceImageName.value = validated.name;
    faceValidationMessage.value = "已识别到清晰人脸，可提交注册。";
    ElMessage.success("人脸图片校验通过。");
  } catch (error) {
    faceValidationMessage.value = error?.message || "人脸图片校验失败。";
    ElMessage.error(faceValidationMessage.value);
  } finally {
    faceValidationLoading.value = false;
    event.target.value = "";
  }
}

async function handleNewPersonFaceFileChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  newPersonFaceImageBase64.value = "";
  newPersonFaceImageName.value = "";
  newPersonFaceValidationMessage.value = "正在检测图片清晰度和人脸特征...";
  newPersonFaceValidationLoading.value = true;
  try {
    const validated = await validateFaceFile(
      file,
      personForm.value.student_no || "preview",
    );
    newPersonFaceImageBase64.value = validated.base64;
    newPersonFaceImageName.value = validated.name;
    newPersonFaceValidationMessage.value =
      "已识别到清晰人脸，保存人员后会自动注册。";
    ElMessage.success("人脸图片校验通过。");
  } catch (error) {
    newPersonFaceValidationMessage.value =
      error?.message || "人脸图片校验失败。";
    ElMessage.error(newPersonFaceValidationMessage.value);
  } finally {
    newPersonFaceValidationLoading.value = false;
    event.target.value = "";
  }
}

async function saveFaceRegistration() {
  if (!selectedStudent.value?.id) {
    ElMessage.warning("请选择需要注册人脸的人员。");
    return;
  }
  if (!faceImageBase64.value) {
    ElMessage.warning("请先选择一张单人脸图片。");
    return;
  }
  try {
    await registerStudentFace(selectedStudent.value.id, faceImageBase64.value);
    students.value = students.value.map((item) =>
      item.id === selectedStudent.value.id
        ? { ...item, face_registered: true }
        : item,
    );
    faceDialogVisible.value = false;
    ElMessage.success("人脸注册成功。");
  } catch (error) {
    if (!isMockEnabled()) {
      ElMessage.error(error?.message || "人脸注册接口请求失败。");
      return;
    }
    students.value = students.value.map((item) =>
      item.id === selectedStudent.value.id
        ? { ...item, face_registered: true }
        : item,
    );
    faceDialogVisible.value = false;
    ElMessage.warning("接口不可用，已在开发模式下标记为已注册。");
  }
}

function openAlertProcessDialog(row, status = "handled") {
  selectedAlert.value = row;
  alertProcessForm.value = {
    status,
    remark: row.remark || "",
  };
  alertProcessDialogVisible.value = true;
}

async function saveAlertProcess() {
  if (!selectedAlert.value?.id) {
    ElMessage.warning("请选择需要处理的告警。");
    return;
  }
  try {
    await updateAlertStatus(selectedAlert.value.id, alertProcessForm.value);
    alerts.value = alerts.value.map((item) =>
      item.id === selectedAlert.value.id
        ? {
            ...item,
            status: alertProcessForm.value.status,
            remark: alertProcessForm.value.remark,
            handled_at: new Date().toISOString(),
          }
        : item,
    );
    alertProcessDialogVisible.value = false;
    ElMessage.success("告警状态已更新。");
  } catch (error) {
    if (!isMockEnabled()) {
      ElMessage.error(error?.message || "告警处理接口请求失败。");
      return;
    }
    alerts.value = alerts.value.map((item) =>
      item.id === selectedAlert.value.id
        ? {
            ...item,
            status: alertProcessForm.value.status,
            remark: alertProcessForm.value.remark,
            handled_at: new Date().toISOString(),
          }
        : item,
    );
    alertProcessDialogVisible.value = false;
    ElMessage.warning("接口不可用，已在开发模式下临时更新状态。");
  }
}

onMounted(async () => {
  if (!isAuthenticated.value) return;
  try {
    currentUser.value = await fetchCurrentUser();
    storeAuthSession(getStoredToken(), currentUser.value, true);
  } catch {
    clearAuthSession();
    isAuthenticated.value = false;
    currentUser.value = null;
    setAuthNotice("登录状态已失效，请重新登录。", "warning");
    return;
  }
  activePage.value = "monitor";
  await loadDashboard();
  startAlertRefresh();
});

onBeforeUnmount(() => {
  window.clearInterval(refreshId);
  window.cancelAnimationFrame(riskScoreAnimationId);
});

watch(activeStreamId, () => {
  isVideoLive.value = false;
  videoError.value = false;
});

watch(targetRiskScore, (score) => animateRiskScore(score), { immediate: true });
</script>

<template>
  <section v-if="!isAuthenticated" class="auth-shell">
    <video
      v-if="!authVideoFailed"
      class="auth-bg-video"
      :class="{ ready: authVideoReady }"
      autoplay
      muted
      loop
      playsinline
      preload="auto"
      aria-hidden="true"
      @canplay="authVideoReady = true"
      @error="authVideoFailed = true"
    >
      <source :src="loginBackgroundVideo" type="video/mp4" />
    </video>
    <div class="auth-bg-overlay"></div>

    <div class="auth-visual">
      <div class="auth-brand">
        <div class="brand-mark">AI</div>
        <span>智慧教室安全监测</span>
      </div>
      <h1>智慧教室实时行为分析与安全监测系统</h1>
      <p>
        统一接入 SpringBoot 鉴权、AI 视频分析和 Nginx
        静态资源，为教师和管理员提供安全、清晰的值守入口。
      </p>
      <div class="auth-feature-grid">
        <article>
          <b>JWT 鉴权</b>
          <span>登录成功后访问业务接口自动携带 Token。</span>
        </article>
        <article>
          <b>角色访问</b>
          <span>初版区分 admin 与 teacher 两类角色。</span>
        </article>
        <article>
          <b>接口一致</b>
          <span>登录走 `/auth/login`，当前用户走 `/auth/info`。</span>
        </article>
      </div>
    </div>

    <div class="auth-panel">
      <div class="auth-tabs" role="tablist" aria-label="认证方式">
        <button
          :class="{ active: authMode === 'login' }"
          type="button"
          @click="authMode = 'login'"
        >
          用户登录
        </button>
        <button
          :class="{ active: authMode === 'register' }"
          type="button"
          @click="authMode = 'register'"
        >
          用户注册
        </button>
      </div>

      <div class="auth-title">
        <h2>{{ authMode === "login" ? "登录系统" : "用户注册" }}</h2>
        <p>
          {{
            authMode === "login"
              ? "使用后端已确定的 /auth/login 接口进入系统。"
              : "注册成功后自动登录，默认角色为教师。"
          }}
        </p>
      </div>

      <el-alert
        v-if="authNotice"
        class="auth-alert"
        :title="authNotice"
        :type="authNoticeType"
        :closable="false"
        show-icon
      />

      <el-form
        v-if="authMode === 'login'"
        class="auth-form"
        label-position="top"
        @submit.prevent="submitLogin"
      >
        <el-form-item label="用户名 / 工号">
          <el-input
            v-model="authForm.username"
            :prefix-icon="User"
            placeholder="例如 admin 或 teacher"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="authForm.password"
            :prefix-icon="Lock"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <div class="auth-row">
          <el-checkbox v-model="authForm.remember">记住登录状态</el-checkbox>
          <span>Token 失效时返回登录页</span>
        </div>
        <el-button
          class="auth-submit"
          type="primary"
          :loading="authLoading"
          @click="submitLogin"
          >登录</el-button
        >
        <button
          v-if="canUseDeveloperLogin"
          class="dev-login-button"
          type="button"
          @click="submitDeveloperLogin"
        >
          开发者模式临时进入
        </button>
      </el-form>

      <el-form
        v-else
        class="auth-form"
        label-position="top"
        @submit.prevent="submitRegister"
      >
        <el-form-item label="用户名">
          <el-input
            v-model="registerForm.username"
            placeholder="至少 2 个字符"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="registerForm.password"
            placeholder="至少 6 个字符"
            show-password
          />
        </el-form-item>
        <el-form-item label="昵称（可选）">
          <el-input
            v-model="registerForm.nickname"
            placeholder="显示名称，可不填"
          />
        </el-form-item>
        <el-button
          class="auth-submit"
          type="primary"
          :loading="authLoading"
          @click="submitRegister"
          >注册并登录</el-button
        >
      </el-form>

      <div class="auth-contract">
        <b>接口契约</b>
        <span
          >已确定：`POST /auth/login`、`POST /auth/register`、`GET
          /auth/info`。开发者模式仅本地调试使用，不会创建真实后端会话。</span
        >
      </div>
    </div>
  </section>

  <div v-else class="app-shell" :class="{ 'eye-care-theme': !isDay }">
    <aside class="side-nav">
      <div class="brand-block">
        <div class="brand-mark">AI</div>
        <span>智课</span>
      </div>

      <div class="nav-stack">
        <button
          v-for="item in visibleNavItems"
          :key="item.key"
          class="nav-button"
          :class="{ active: activePage === item.key }"
          :title="item.label"
          @click="navigateToPage(item.key)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </button>
      </div>

      <div class="online-block">
        <span class="live-dot"></span>
        <span>在线值守</span>
      </div>
    </aside>

    <main class="main-area">
      <header class="top-bar">
        <div>
          <h1>智慧教室实时行为分析与安全监测系统</h1>
          <p>聚焦单路实时画面，优先呈现视频流、AI 标注、实时告警和事件追踪。</p>
        </div>
        <div class="header-actions">
          <button
            class="sky-widget"
            :class="{ night: !isDay }"
            :title="dayHint"
            type="button"
            @click="toggleThemeMode"
          >
            <div
              class="sky-avatar"
              :class="isDay ? 'sun-face' : 'moon-face'"
              aria-hidden="true"
            >
              <span class="sky-eye left"></span>
              <span class="sky-eye right"></span>
              <span class="sky-mouth"></span>
              <span v-if="!isDay" class="sleep-note z1">z</span>
              <span v-if="!isDay" class="sleep-note z2">z</span>
            </div>
            <div>
              <b>{{ dayTitle }}</b>
              <span>{{ dayHint }}</span>
            </div>
          </button>
          <el-button :icon="Refresh" @click="loadDashboard">刷新</el-button>
          <div class="user-chip" :title="userRoleName">
            <el-icon><User /></el-icon>
            <span>{{ userDisplayName }}</span>
          </div>
          <el-button @click="handleLogout">退出</el-button>
          <el-select
            v-model="activeStreamId"
            class="stream-select"
            @change="switchStream"
          >
            <el-option
              v-for="stream in streams"
              :key="stream.stream_id"
              :label="stream.stream_name || stream.stream_id"
              :value="stream.stream_id"
            />
          </el-select>
        </div>
      </header>

      <section class="metrics-grid">
        <article
          v-for="item in metricCards"
          :key="item.label"
          class="metric-card"
        >
          <div class="metric-icon">
            <el-icon><component :is="item.icon" /></el-icon>
          </div>
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </section>

      <section v-if="activePage === 'monitor'" class="monitor-layout">
        <div class="left-column">
          <section class="panel video-panel">
            <div class="panel-head">
              <div>
                <h2>
                  {{ currentStream.stream_name || activeStreamId }} 实时画面
                </h2>
                <span>{{ currentStream.location || "单路实时监控" }}</span>
              </div>
              <div class="video-toolbar" aria-label="实时监控工具">
                <button class="tool-button active" title="实时画面">
                  <el-icon><VideoCamera /></el-icon>
                </button>
                <button
                  class="tool-button"
                  :class="{ active: showAiAnnotations }"
                  title="AI 标注"
                  type="button"
                  @click="toggleAiAnnotations"
                >
                  <el-icon><Search /></el-icon>
                </button>
                <button
                  class="tool-button"
                  :class="{ active: showRuleOverlay }"
                  title="区域规则"
                  type="button"
                  @click="toggleRuleOverlay"
                >
                  <el-icon><Setting /></el-icon>
                </button>
                <button
                  class="tool-button"
                  title="放大实时画面"
                  type="button"
                  @click="openExpandedVideo"
                >
                  <el-icon><FullScreen /></el-icon>
                </button>
              </div>
            </div>

            <div
              ref="videoStageRef"
              class="video-stage"
              :class="{
                drawing: isDrawingForbiddenZone,
                locked: !showRuleOverlay,
              }"
              @mousedown.left.prevent="startForbiddenZoneDraw"
              @mousemove="updateForbiddenZoneDraw"
              @mouseup="finishForbiddenZoneDraw"
              @mouseleave="finishForbiddenZoneDraw"
            >
              <img
                v-if="!videoError"
                class="video-stream"
                :src="videoFeedUrl"
                alt="AI 处理后的视频流"
                @load="handleVideoLoad"
                @error="handleVideoError"
              />
              <div
                class="classroom-fallback"
                :class="{ muted: !videoError && isVideoLive }"
              >
                <div class="board"></div>
                <div class="desk d1"></div>
                <div class="desk d2"></div>
                <div class="desk d3"></div>
              </div>

              <div class="feed-top">
                <span class="video-chip">
                  <span class="status-dot"></span>
                  {{
                    currentStream.stream_name ||
                    activeStreamId ||
                    "未选择视频源"
                  }}
                </span>
                <span class="video-chip danger">
                  <span class="status-dot red"></span>
                  {{
                    videoError
                      ? "视频不可用"
                      : streamSwitching
                        ? "切换中..."
                        : "实时联调"
                  }}
                </span>
              </div>

              <template v-if="showRuleOverlay">
                <div
                  v-if="activeForbiddenRect"
                  class="drawn-forbidden-zone drafting"
                  :style="forbiddenZoneStyle"
                >
                  <span>{{
                    isDrawingForbiddenZone
                      ? "绘制中"
                      : pendingForbiddenZone?.zone_name || "待确认区域"
                  }}</span>
                </div>
              </template>
              <div
                v-if="showRuleOverlay && !activeForbiddenRect"
                class="draw-hint"
              >
                {{ "按住鼠标左键拖拽新增区域，已保存区域由 AI 视频流标注" }}
              </div>
              <div v-if="!showRuleOverlay" class="draw-hint muted">
                区域规则层已关闭
              </div>
              <div
                v-if="showRuleOverlay && hasPendingForbiddenZone"
                class="zone-actions"
                @mousedown.stop
              >
                <input
                  v-model="pendingForbiddenZone.zone_name"
                  class="zone-draft-input"
                  aria-label="区域名称"
                  placeholder="区域名称"
                />
                <select
                  v-model="pendingForbiddenZone.zone_type"
                  class="zone-draft-select"
                  aria-label="区域类型"
                >
                  <option
                    v-for="option in zoneTypeOptions"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
                <button
                  type="button"
                  class="zone-action primary"
                  :disabled="zoneSaving"
                  @click.stop="confirmForbiddenZone"
                >
                  {{ zoneSaving ? "保存中..." : "确定并启用" }}
                </button>
                <button
                  type="button"
                  class="zone-action"
                  @click.stop="clearForbiddenZone"
                >
                  取消草稿
                </button>
              </div>
              <div v-if="showAiAnnotations" class="insight-strip">
                <article>
                  <span>AI 研判</span>
                  <b>{{ activeSummary.title || "等待 AI 研判" }}</b>
                </article>
                <article>
                  <span>行为趋势</span>
                  <div class="sparkline"><i></i><i></i><i></i><i></i></div>
                </article>
                <article>
                  <span>自动动作</span>
                  <b>{{ actionItems[0] }}</b>
                </article>
              </div>
            </div>
          </section>

          <section class="overview-grid tracking-overview">
            <div class="panel">
              <div class="panel-head compact">
                <h2>告警追踪记录</h2>
                <el-segmented
                  v-model="activeAlertStatus"
                  :options="statusOptions"
                  size="small"
                />
              </div>
              <el-table :data="filteredAlerts" height="420" class="clean-table">
                <el-table-column prop="occurred_at" label="时间" width="150" />
                <el-table-column label="类型" min-width="110">
                  <template #default="{ row }">
                    {{ row.alert_name || alertTypeText(row.alert_type) }}
                  </template>
                </el-table-column>
                <el-table-column
                  prop="stream_name"
                  label="视频源"
                  min-width="120"
                />
                <el-table-column label="等级" width="84">
                  <template #default="{ row }">
                    <el-tag
                      :type="
                        row.level === 'high'
                          ? 'danger'
                          : row.level === 'warning'
                            ? 'warning'
                            : 'info'
                      "
                      effect="light"
                    >
                      {{ levelText(row.level) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="92">
                  <template #default="{ row }">
                    <el-tag :type="statusType(row.status)" effect="plain">{{
                      statusText(row.status)
                    }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </section>
        </div>

        <aside class="right-column">
          <section class="panel featured-ai">
            <div class="panel-head compact">
              <h2>AI 研判助手</h2>
              <el-tag effect="dark" type="danger">重点关注</el-tag>
            </div>
            <div class="ai-card">
              <div class="score-row">
                <div
                  class="risk-score"
                  :class="{ idle: !hasActiveRiskEvents }"
                  :style="{ '--score': `${displayedRiskScore}%` }"
                >
                  <span v-if="!hasActiveRiskEvents">--</span>
                  <template v-else>{{
                    Math.round(displayedRiskScore)
                  }}</template>
                </div>
                <div>
                  <b>{{ activeSummary.title || "暂无 AI 风险摘要" }}</b>
                  <p>
                    {{
                      activeSummary.summary || "等待 AI 服务返回实时分析结果。"
                    }}
                  </p>
                </div>
              </div>
              <div class="action-pills">
                <span v-for="action in actionItems" :key="action">{{
                  action
                }}</span>
              </div>
              <div class="timeline">
                <div
                  v-for="item in activeSummary.timeline || []"
                  :key="item.time"
                >
                  <time>{{ item.time }}</time>
                  <span>{{ item.text }}</span>
                </div>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head compact">
              <h2>实时告警</h2>
              <el-tag type="danger" effect="dark">优先处理</el-tag>
            </div>
            <div class="alert-list">
              <article
                v-for="alert in highPriorityAlerts"
                :key="alert.id"
                class="alert-card"
                :class="alert.level"
              >
                <div>
                  <b>{{
                    alert.alert_name || alertTypeText(alert.alert_type)
                  }}</b>
                  <el-tag :type="statusType(alert.status)" size="small">{{
                    statusText(alert.status)
                  }}</el-tag>
                </div>
                <p>
                  {{ alert.stream_name || alert.stream_id }}，{{
                    alert.remark || alert.event_id || "暂无说明"
                  }}
                </p>
              </article>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head compact">
              <h2>规则概览</h2>
            </div>
            <div class="rule-list">
              <article class="zone-coordinate-card">
                <div>
                  <b>实时画面禁用区</b>
                  <span v-if="forbiddenZoneCoordinates.length">
                    待确认：{{
                      forbiddenZoneCoordinates
                        .map(
                          (point) =>
                            `(${formatCoord(point.x)}, ${formatCoord(point.y)})`,
                        )
                        .join(" / ")
                    }}
                  </span>
                  <span v-else-if="confirmedForbiddenZones.length">
                    已启用
                    {{ confirmedForbiddenZones.length }}
                    个区域，可在实时画面列表中逐个删除
                  </span>
                  <span v-else>尚未绘制，拖拽实时画面生成四角坐标</span>
                </div>
              </article>
              <article v-for="rule in rules" :key="rule.id">
                <div>
                  <b>{{ ruleNameText(rule) }}</b>
                  <span
                    >{{ ruleSummaryText(rule) }}，阈值
                    {{ rule.threshold_seconds }} 秒</span
                  >
                </div>
                <el-switch
                  :model-value="rule.enabled"
                  :disabled="!hasConfirmedForbiddenZone && isPhoneRelated(rule)"
                  @change="handleToggleRule(rule)"
                />
              </article>
            </div>
          </section>

          <div class="monitor-dog-zone">
            <div class="monitor-dog" aria-label="值守小狗动图">
              <img
                class="monitor-dog-gif"
                :src="lineDogGif"
                alt="值守小狗动图"
              />
            </div>
          </div>
        </aside>
      </section>

      <section
        v-else-if="activePage === 'alerts'"
        class="page-grid module-page"
      >
        <div class="page-kpis">
          <article
            v-for="item in alertPageCards"
            :key="item.label"
            class="kpi-card"
            :class="item.tone"
          >
            <span>{{ item.label }}</span>
            <b>{{ item.value }}</b>
          </article>
        </div>

        <!-- 通知 & 日报 紧凑栏 -->
        <div class="module-board" style="margin-bottom: 6px">
          <section
            class="panel span-12"
            style="
              padding: 8px 20px;
              display: flex;
              gap: 50px;
              align-items: center;
            "
          >
            <label style="display: flex; align-items: center; gap: 10px">
              <el-switch v-model="alertSettings.dingtalkEnabled" />
              <b>钉钉通知</b>
              <span
                v-if="alertSettings.dingtalkEnabled"
                style="font-size: 13px; color: #67c23a"
                >● {{ alertSettings.responsible }}</span
              >
              <span
                v-if="alertSettings.dingtalkEnabled"
                style="font-size: 12px; color: #909399; margin-left: 8px"
              >
                间隔
                <input
                  v-model.number="alertSettings.alertInterval"
                  type="number"
                  min="10"
                  max="600"
                  style="
                    width: 50px;
                    padding: 2px 4px;
                    border: 1px solid #dcdfe6;
                    border-radius: 4px;
                    text-align: center;
                  "
                  @change="syncContactsToBackend"
                />
                秒
              </span>
              <el-button
                v-if="alertSettings.dingtalkEnabled"
                size="small"
                @click="showContactModal = true"
                >管理联系人</el-button
              >
            </label>
            <label style="display: flex; align-items: center; gap: 10px">
              <el-switch v-model="alertSettings.aiReportEnabled" />
              <b>AI日报</b>
              <el-time-select
                v-if="alertSettings.aiReportEnabled"
                v-model="alertSettings.reportTime"
                start="00:00"
                end="23:59"
                step="00:30"
                size="small"
                style="width: 100px"
              />
              <el-button
                v-if="alertSettings.aiReportEnabled"
                size="small"
                type="primary"
                :loading="alertSettings.generating"
                @click="generateAiReport"
                >生成日报</el-button
              >
              <el-button
                v-if="alertSettings.latestReport"
                size="small"
                type="success"
                @click="exportReportPdf"
                >导出 PDF</el-button
              >
              <el-button
                v-if="alertSettings.latestReport"
                size="small"
                @click="showReportModal = true"
                >往期日报</el-button
              >
            </label>
          </section>
        </div>

        <!-- 最新日报卡片 -->
        <div
          v-if="alertSettings.latestReport"
          class="module-board"
          style="margin-bottom: 6px"
        >
          <section
            class="panel span-12"
            style="
              padding: 12px 20px;
              background: #f0f9ff;
              border-left: 3px solid #409eff;
            "
          >
            <div
              style="
                display: flex;
                justify-content: space-between;
                align-items: center;
              "
            >
              <b>最新日报 — {{ alertSettings.latestReport.date }}</b>
              <span style="font-size: 12px; color: #909399">{{
                alertSettings.latestReport.time
              }}</span>
            </div>
            <p
              style="
                margin: 6px 0 0;
                font-size: 14px;
                line-height: 1.7;
                white-space: pre-wrap;
              "
            >
              {{ alertSettings.latestReport.summary }}
            </p>
          </section>
        </div>

        <!-- 联系人弹窗 -->
        <div
          v-if="showContactModal"
          style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.45);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
          "
          @click.self="showContactModal = false"
        >
          <div
            style="
              background: #fff;
              padding: 28px;
              border-radius: 10px;
              width: 550px;
              max-height: 75vh;
              overflow-y: auto;
              box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
            "
          >
            <h2 style="margin: 0 0 20px; font-size: 18px">联系人管理</h2>
            <div
              v-for="c in alertSettings.contacts"
              style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid #f0f0f0;
              "
            >
              <div>
                <span
                  v-if="c.name === alertSettings.responsible"
                  style="color: #67c23a; margin-right: 6px"
                  >●</span
                >
                <b>{{ c.name }}</b>
                <span
                  style="color: #909399; font-size: 13px; margin-left: 8px"
                  >{{ c.mobile }}</span
                >
              </div>
              <div style="display: flex; gap: 8px">
                <el-button
                  v-if="c.name !== alertSettings.responsible"
                  size="small"
                  type="primary"
                  plain
                  @click="alertSettings.responsible = c.name"
                  >设为负责人</el-button
                >
                <el-button
                  v-if="c.name !== '项重善' && c.name !== '章志超'"
                  size="small"
                  type="danger"
                  plain
                  @click="removeContact(c.name)"
                  >删除</el-button
                >
              </div>
            </div>
            <div
              style="
                display: flex;
                gap: 10px;
                margin-top: 16px;
                align-items: center;
              "
            >
              <input
                v-model="newContact.name"
                placeholder="姓名"
                style="
                  flex: 1;
                  padding: 8px 12px;
                  border: 1px solid #dcdfe6;
                  border-radius: 6px;
                  font-size: 14px;
                "
              />
              <input
                v-model="newContact.mobile"
                placeholder="手机号"
                style="
                  flex: 2;
                  padding: 8px 12px;
                  border: 1px solid #dcdfe6;
                  border-radius: 6px;
                  font-size: 14px;
                "
              />
              <el-button type="primary" size="default" @click="doAddContact"
                >添加</el-button
              >
            </div>
            <div style="text-align: right; margin-top: 20px">
              <el-button @click="showContactModal = false">关闭</el-button>
            </div>
          </div>
        </div>

        <!-- 往期日报弹窗 -->
        <div
          v-if="showReportModal"
          style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.45);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
          "
          @click.self="showReportModal = false"
        >
          <div
            style="
              background: #fff;
              padding: 28px;
              border-radius: 10px;
              width: 650px;
              max-height: 80vh;
              overflow-y: auto;
              box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
            "
          >
            <h2 style="margin: 0 0 20px; font-size: 18px">
              往期日报（{{ alertSettings.reportHistory.length }} 条）
            </h2>
            <div
              v-if="alertSettings.reportHistory.length === 0"
              style="color: #909399; text-align: center; padding: 40px"
            >
              暂无日报
            </div>
            <div
              v-for="(r, i) in alertSettings.reportHistory"
              style="padding: 14px 0; border-bottom: 1px solid #f0f0f0"
            >
              <div style="font-size: 12px; color: #909399; margin-bottom: 4px">
                {{ r.date }} {{ r.time?.slice(11, 16) || "" }}
              </div>
              <div
                style="font-size: 14px; line-height: 1.7; white-space: pre-wrap"
              >
                {{ r.summary }}
              </div>
            </div>
            <div style="text-align: right; margin-top: 20px">
              <el-button type="primary" size="small" @click="exportReportPdf"
                >导出 PDF</el-button
              >
              <el-button @click="showReportModal = false">关闭</el-button>
            </div>
          </div>
        </div>

        <div class="module-board">
          <section class="panel span-12">
            <div class="panel-head">
              <div>
                <h2>告警管理</h2>
                <span
                  >来自 SpringBoot `/alerts`，截图和录像路径由 Nginx
                  静态服务访问。</span
                >
              </div>
              <div class="alert-filter-bar">
                <el-input
                  v-model="alertKeyword"
                  class="search-box"
                  :prefix-icon="Search"
                  clearable
                  placeholder="搜索类型、说明或视频源"
                />
                <el-select
                  v-model="activeAlertType"
                  class="filter-select"
                  placeholder="告警类型"
                >
                  <el-option
                    v-for="item in alertTypeOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <el-select
                  v-model="activeAlertLevel"
                  class="filter-select"
                  placeholder="告警等级"
                >
                  <el-option
                    v-for="item in alertLevelOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <el-select
                  v-model="activeAlertStatus"
                  class="filter-select"
                  placeholder="处理状态"
                >
                  <el-option
                    v-for="item in statusOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </div>
            </div>
            <el-table :data="filteredAlerts" height="360" class="clean-table">
              <el-table-column prop="occurred_at" label="时间" width="150" />
              <el-table-column label="告警类型" width="130">
                <template #default="{ row }">
                  {{ row.alert_name || alertTypeText(row.alert_type) }}
                </template>
              </el-table-column>
              <el-table-column prop="stream_id" label="视频源" width="100" />
              <el-table-column prop="stream_name" label="名称" width="130" />
              <el-table-column prop="remark" label="说明" min-width="240" />
              <el-table-column label="等级" width="92">
                <template #default="{ row }">
                  <el-tag :type="levelType(row.level)" effect="light">
                    {{ levelText(row.level) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="评分" width="92">
                <template #default="{ row }">
                  <el-tag
                    effect="plain"
                    :type="
                      calculateEventRiskScore(row) >= 80
                        ? 'danger'
                        : calculateEventRiskScore(row) >= 60
                          ? 'warning'
                          : 'info'
                    "
                  >
                    {{ calculateEventRiskScore(row) || "--" }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="statusType(row.status)">{{
                    statusText(row.status)
                  }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="证据" width="210">
                <template #default="{ row }">
                  <div class="evidence-actions">
                    <span>{{ evidenceSummary(row) }}</span>
                    <div>
                      <el-button
                        size="small"
                        text
                        tag="a"
                        target="_blank"
                        :disabled="!row.snapshot_url"
                        :href="
                          row.snapshot_url
                            ? resourceUrl(row.snapshot_url)
                            : undefined
                        "
                        >截图</el-button
                      >
                      <el-button
                        size="small"
                        text
                        :disabled="!row.record_url"
                        @click="openReplayDialog(row)"
                        >录像</el-button
                      >
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="处理" width="190" fixed="right">
                <template #default="{ row }">
                  <el-button
                    size="small"
                    type="primary"
                    text
                    @click="openAlertProcessDialog(row, 'handled')"
                    >处理</el-button
                  >
                  <el-button
                    size="small"
                    text
                    @click="openAlertProcessDialog(row, 'false_alarm')"
                    >误报</el-button
                  >
                  <el-button
                    size="small"
                    text
                    @click="openAlertProcessDialog(row, 'ignored')"
                    >忽略</el-button
                  >
                </template>
              </el-table-column>
            </el-table>
          </section>

          <section class="panel span-12">
            <div class="panel-head compact">
              <h2>告警评分配置</h2>
            </div>
            <div class="score-config-list">
              <article v-for="item in riskScoreSettings" :key="item.type">
                <div>
                  <b>{{ item.label }}</b>
                  <span>{{ item.note }}</span>
                </div>
                <el-input-number
                  v-model="item.score"
                  :min="0"
                  :max="100"
                  :step="1"
                  size="small"
                  :disabled="!isAdmin"
                  @change="handleScoreConfigChange(item)"
                />
              </article>
              <el-empty
                v-if="!riskScoreSettings.length"
                description="评分配置接口暂无数据"
              />
            </div>
          </section>
        </div>
      </section>

      <section
        v-else-if="activePage === 'rules'"
        class="page-grid module-page centered-module-page"
      >
        <div class="page-kpis">
          <article
            v-for="item in rulePageCards"
            :key="item.label"
            class="kpi-card"
            :class="item.tone"
          >
            <span>{{ item.label }}</span>
            <b>{{ item.value }}</b>
          </article>
        </div>

        <div class="module-board">
          <section class="panel span-6">
            <div class="panel-head">
              <div>
                <h2>区域规则配置</h2>
                <span
                  >规则来自 `/rules`，区域来自
                  `/zones`；数值表示触发前需要持续命中的秒数。</span
                >
              </div>
            </div>
            <div class="rule-editor">
              <article v-for="rule in rules" :key="rule.id">
                <div>
                  <b>{{ ruleNameText(rule) }}</b>
                  <span>{{ ruleSummaryText(rule) }}</span>
                </div>
                <div class="rule-threshold-control">
                  <span>持续阈值（秒）</span>
                  <el-input-number
                    v-model="rule.threshold_seconds"
                    :min="1"
                    :max="30"
                    size="small"
                    :disabled="!isAdmin"
                  />
                </div>
                <el-switch
                  :model-value="rule.enabled"
                  :disabled="!hasConfirmedForbiddenZone && isPhoneRelated(rule)"
                  @change="handleToggleRule(rule)"
                />
              </article>
            </div>
          </section>

          <section class="panel span-6">
            <div class="panel-head">
              <div>
                <h2>区域管理</h2>
                <span
                  >区域从实时监控画面拖拽新增；此处通过 `/zones`
                  查询、编辑、启停和删除。</span
                >
              </div>
            </div>
            <el-table :data="zoneRows" height="390" class="clean-table">
              <el-table-column label="区域名称" min-width="110">
                <template #default="{ row }">
                  {{ row.zone_name || "未命名区域" }}
                </template>
              </el-table-column>
              <el-table-column label="类型" width="110">
                <template #default="{ row }">
                  <el-tag effect="plain">{{
                    zoneTypeText(row.zone_type)
                  }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="阈值(秒)" width="80">
                <template #default="{ row }">
                  {{ row.threshold_seconds ?? "--" }}
                </template>
              </el-table-column>
              <el-table-column label="预警距离" width="80">
                <template #default="{ row }">
                  {{
                    row.safe_distance
                      ? (row.safe_distance * 100).toFixed(1) + "%"
                      : "--"
                  }}
                </template>
              </el-table-column>
              <el-table-column label="开关" width="70">
                <template #default="{ row }">
                  <el-switch
                    :model-value="row.enabled"
                    size="small"
                    @change="handleToggleZone(row)"
                  />
                </template>
              </el-table-column>
              <el-table-column label="坐标" min-width="140">
                <template #default="{ row }">
                  <span class="coord-text">{{ zoneCoordinateText(row) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button
                    size="small"
                    type="primary"
                    text
                    @click="openZoneDialog(row)"
                    >编辑</el-button
                  >
                  <el-button
                    size="small"
                    type="danger"
                    text
                    @click="handleDeleteZone(row)"
                    >删除</el-button
                  >
                </template>
              </el-table-column>
            </el-table>
          </section>
        </div>
      </section>

      <section
        v-else-if="activePage === 'people'"
        class="page-grid module-page centered-module-page"
      >
        <div class="page-kpis">
          <article
            v-for="item in peoplePageCards"
            :key="item.label"
            class="kpi-card"
            :class="item.tone"
          >
            <span>{{ item.label }}</span>
            <b>{{ item.value }}</b>
          </article>
        </div>

        <div class="module-board">
          <section class="panel span-12">
            <div class="panel-head">
              <div>
                <h2>人员与人脸库</h2>
                <span
                  >人员基础信息来自 `/students`，人脸注册提交到
                  `/students/{id}/face`。</span
                >
              </div>
              <el-button
                v-if="isAdmin"
                type="primary"
                :icon="User"
                @click="openPersonDialog"
                >新增人员</el-button
              >
            </div>
            <el-table :data="students" height="480" class="clean-table">
              <el-table-column prop="student_no" label="编号" width="110" />
              <el-table-column prop="name" label="姓名" width="120" />
              <el-table-column
                prop="class_name"
                label="班级/身份"
                min-width="130"
              />
              <el-table-column label="人脸状态" width="110">
                <template #default="{ row }">
                  <el-tag :type="row.face_registered ? 'success' : 'warning'">
                    {{ row.face_registered ? "已注册" : "待注册" }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="last_seen" label="最近出现" width="110" />
              <el-table-column
                v-if="isAdmin"
                label="操作"
                width="130"
                fixed="right"
              >
                <template #default="{ row }">
                  <el-button
                    size="small"
                    type="primary"
                    text
                    @click="openFaceDialog(row)"
                  >
                    {{ row.face_registered ? "重新注册" : "注册人脸" }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </section>
        </div>
      </section>

      <section
        v-else-if="activePage === 'users' && isAdmin"
        class="page-grid module-page centered-module-page"
      >
        <div class="page-kpis">
          <article
            v-for="item in userPageCards"
            :key="item.label"
            class="kpi-card"
            :class="item.tone"
          >
            <span>{{ item.label }}</span>
            <b>{{ item.value }}</b>
          </article>
        </div>

        <div class="module-board">
          <section class="panel span-12">
            <div class="panel-head">
              <div>
                <h2>用户管理</h2>
                <span
                  >用户信息来自 `/users`，角色修改提交到
                  `/users/{id}/role`。不能修改自己的角色。</span
                >
              </div>
              <el-button
                :icon="Refresh"
                :loading="usersLoading"
                @click="loadUsers"
                >刷新用户</el-button
              >
            </div>
            <el-table
              v-loading="usersLoading"
              :data="users"
              height="520"
              class="clean-table"
            >
              <el-table-column prop="username" label="用户名" min-width="130" />
              <el-table-column label="昵称" min-width="130">
                <template #default="{ row }">
                  {{ row.nickname || "--" }}
                </template>
              </el-table-column>
              <el-table-column label="角色" width="150">
                <template #default="{ row }">
                  <el-select
                    :model-value="row.role"
                    size="small"
                    :disabled="
                      String(row.id) === String(currentUserId) ||
                      userRoleUpdatingId === row.id
                    "
                    :loading="userRoleUpdatingId === row.id"
                    @change="(role) => handleUserRoleChange(row, role)"
                  >
                    <el-option label="管理员" value="admin" />
                    <el-option label="教师" value="teacher" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'enabled' ? 'success' : 'info'">
                    {{ row.status === "enabled" ? "启用" : "停用" }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                prop="last_login_at"
                label="最近登录"
                min-width="170"
              />
              <el-table-column
                prop="created_at"
                label="创建时间"
                min-width="170"
              />
            </el-table>
          </section>
        </div>
      </section>

      <section
        v-else-if="activePage === 'system'"
        class="page-grid module-page centered-module-page"
      >
        <div class="page-kpis">
          <article
            v-for="item in systemPageCards"
            :key="item.label"
            class="kpi-card"
            :class="item.tone"
          >
            <span>{{ item.label }}</span>
            <b>{{ item.value }}</b>
          </article>
        </div>

        <div class="module-board">
          <section class="panel span-8">
            <div class="panel-head">
              <div>
                <h2>视频源与服务状态</h2>
                <span
                  >对应 `/streams`、`/model/status`、`/system/health`。</span
                >
              </div>
              <el-button v-if="isAdmin" :icon="Switch" @click="openStreamDialog"
                >新增视频源</el-button
              >
            </div>
            <div class="stream-list">
              <article
                v-for="stream in allStreamStatusRecords"
                :key="stream.stream_id"
              >
                <div>
                  <b>{{ stream.stream_name }}</b>
                  <span>{{ stream.rtmp_url }}</span>
                </div>
                <el-tag :type="statusType(stream.status)">{{
                  statusText(stream.status)
                }}</el-tag>
              </article>
            </div>
          </section>

          <section class="panel span-4">
            <div class="panel-head compact">
              <h2>运行概览</h2>
            </div>
            <div class="health-grid">
              <article v-for="item in healthItems" :key="item.label">
                <span>{{ item.label }}</span>
                <b :class="item.value">{{ item.value }}</b>
              </article>
              <article>
                <span>模型版本</span>
                <b>{{
                  modelStatus.version || modelStatus.model_name || "--"
                }}</b>
              </article>
              <article>
                <span>推理耗时</span>
                <b>{{
                  modelStatus.inference_ms
                    ? `${modelStatus.inference_ms} ms`
                    : "--"
                }}</b>
              </article>
            </div>
          </section>
        </div>
      </section>
      <section v-else class="page-grid module-page centered-module-page">
        <div class="module-board">
          <section class="panel span-12">
            <el-empty description="页面未找到，请从左侧导航选择" />
          </section>
        </div>
      </section>
    </main>

    <teleport to="body">
      <el-dialog
        v-model="personDialogVisible"
        title="新增人员"
        width="460px"
        class="local-edit-dialog"
      >
        <el-form class="local-edit-form" label-position="top">
          <el-form-item label="人员编号">
            <el-input
              v-model="personForm.student_no"
              placeholder="例如 2026001"
            />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="personForm.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="班级 / 身份">
            <el-input
              v-model="personForm.class_name"
              placeholder="例如 高一 1 班 / 访客"
            />
          </el-form-item>
          <el-form-item label="人脸图片">
            <label class="file-picker">
              <input
                type="file"
                accept="image/*"
                :disabled="newPersonFaceValidationLoading"
                @change="handleNewPersonFaceFileChange"
              />
              <span>{{
                newPersonFaceValidationLoading
                  ? "正在检测人脸图片..."
                  : newPersonFaceImageName || "选择单人脸图片，可稍后补录"
              }}</span>
            </label>
          </el-form-item>
          <p
            v-if="newPersonFaceValidationMessage"
            class="dialog-hint"
            :class="{ success: newPersonFaceImageBase64 }"
          >
            {{ newPersonFaceValidationMessage }}
          </p>
          <p class="dialog-hint">
            图片需通过清晰度校验和 `/face/feature/extract`
            人脸特征提取后才会被使用。
          </p>
        </el-form>
        <template #footer>
          <el-button @click="personDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :disabled="newPersonFaceValidationLoading"
            @click="savePerson"
            >确定新增</el-button
          >
        </template>
      </el-dialog>

      <el-dialog
        v-model="streamDialogVisible"
        title="新增视频源"
        width="520px"
        class="local-edit-dialog"
      >
        <el-form class="local-edit-form" label-position="top">
          <el-form-item label="视频源编号">
            <el-input
              v-model="streamForm.stream_id"
              placeholder="例如 classroom_03"
            />
          </el-form-item>
          <el-form-item label="视频源名称">
            <el-input
              v-model="streamForm.stream_name"
              placeholder="例如 三号教室主摄像头"
            />
          </el-form-item>
          <el-form-item label="位置">
            <el-input
              v-model="streamForm.location"
              placeholder="例如 教学楼三层 C305"
            />
          </el-form-item>
          <el-form-item label="RTMP 地址">
            <el-input
              v-model="streamForm.rtmp_url"
              placeholder="rtmp://media-server/live/classroom_03"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-segmented
              v-model="streamForm.status"
              :options="[
                { label: '在线', value: 'online' },
                { label: '离线', value: 'offline' },
              ]"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="streamDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveStream">确定新增</el-button>
        </template>
      </el-dialog>

      <el-dialog
        v-model="alertProcessDialogVisible"
        title="处理告警"
        width="480px"
        class="local-edit-dialog"
      >
        <el-form class="local-edit-form" label-position="top">
          <el-form-item label="告警">
            <el-input
              :model-value="
                selectedAlert
                  ? `${selectedAlert.alert_name || alertTypeText(selectedAlert.alert_type)} / ${selectedAlert.stream_name || selectedAlert.stream_id}`
                  : ''
              "
              disabled
            />
          </el-form-item>
          <el-form-item label="处理状态">
            <el-segmented
              v-model="alertProcessForm.status"
              :options="[
                { label: '已处理', value: 'handled' },
                { label: '误报', value: 'false_alarm' },
                { label: '忽略', value: 'ignored' },
                { label: '处理中', value: 'processing' },
              ]"
            />
          </el-form-item>
          <el-form-item label="处理备注">
            <el-input
              v-model="alertProcessForm.remark"
              type="textarea"
              :rows="3"
              placeholder="填写复核结论、处理人或现场处置说明"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="alertProcessDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveAlertProcess"
            >保存处理结果</el-button
          >
        </template>
      </el-dialog>

      <el-dialog
        v-model="replayVisible"
        title="事件回放"
        width="640px"
        class="local-edit-dialog"
        @close="closeReplayDialog"
      >
        <video
          ref="replayVideoRef"
          :src="replayUrl"
          controls
          style="width: 100%; max-height: 480px; background: #000"
          @loadedmetadata="onReplayReady"
        />
      </el-dialog>

      <el-dialog
        v-model="faceDialogVisible"
        title="注册人脸"
        width="480px"
        class="local-edit-dialog"
      >
        <el-form class="local-edit-form" label-position="top">
          <el-form-item label="人员">
            <el-input
              :model-value="
                selectedStudent
                  ? `${selectedStudent.name} / ${selectedStudent.student_no}`
                  : ''
              "
              disabled
            />
          </el-form-item>
          <el-form-item label="人脸图片">
            <label class="file-picker">
              <input
                type="file"
                accept="image/*"
                :disabled="faceValidationLoading"
                @change="handleFaceFileChange"
              />
              <span>{{
                faceValidationLoading
                  ? "正在检测人脸图片..."
                  : faceImageName || "选择单人脸图片"
              }}</span>
            </label>
          </el-form-item>
          <p
            v-if="faceValidationMessage"
            class="dialog-hint"
            :class="{ success: faceImageBase64 }"
          >
            {{ faceValidationMessage }}
          </p>
          <p class="dialog-hint">
            图片需先通过 `/face/feature/extract` 识别出清晰人脸，再提交到
            `/students/{id}/face`。
          </p>
        </el-form>
        <template #footer>
          <el-button @click="faceDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :disabled="faceValidationLoading || !faceImageBase64"
            @click="saveFaceRegistration"
            >提交注册</el-button
          >
        </template>
      </el-dialog>

      <el-dialog
        v-model="zoneDialogVisible"
        title="编辑区域"
        width="520px"
        class="local-edit-dialog"
      >
        <el-form class="local-edit-form" label-position="top">
          <el-form-item label="视频源">
            <el-select
              v-model="zoneForm.stream_id"
              disabled
              placeholder="选择视频源"
              style="width: 100%"
            >
              <el-option
                v-for="stream in streams"
                :key="stream.stream_id"
                :label="stream.stream_name || stream.stream_id"
                :value="stream.stream_id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="区域名称">
            <el-input
              v-model="zoneForm.zone_name"
              placeholder="例如 一号教室危险区"
            />
          </el-form-item>
          <el-form-item label="区域类型">
            <el-select v-model="zoneForm.zone_type" style="width: 100%">
              <el-option label="危险区" value="danger" />
              <el-option label="手机禁用区" value="phone_forbidden" />
            </el-select>
          </el-form-item>
          <el-form-item label="停留阈值（秒）">
            <el-input-number
              v-model="zoneForm.threshold_seconds"
              :min="1"
              :max="60"
            />
            <span style="margin-left: 8px; color: #909399; font-size: 12px"
              >目标在区域内持续停留超过此时长后触发告警</span
            >
          </el-form-item>
          <el-form-item label="预警距离（归一化比例）">
            <el-input-number
              v-model="zoneForm.safe_distance"
              :min="0"
              :max="0.5"
              :step="0.01"
              :precision="2"
            />
            <span style="margin-left: 8px; color: #909399; font-size: 12px"
              >实际判定框比显示框向外扩展此比例，0 表示严格按框判定</span
            >
          </el-form-item>
          <el-form-item label="启用状态">
            <el-switch v-model="zoneForm.enabled" />
          </el-form-item>
          <p class="dialog-hint">
            坐标由实时监控页面拖拽生成；此处修改名称、类型和阈值，不重复绘制。
            当前坐标：{{
              zoneForm.coordinates.length
                ? zoneCoordinateText(zoneForm)
                : "暂无"
            }}
          </p>
        </el-form>
        <template #footer>
          <el-button @click="zoneDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :disabled="zoneFormSaving"
            @click="saveZone"
          >
            {{ zoneFormSaving ? "保存中..." : "确定" }}
          </el-button>
        </template>
      </el-dialog>

      <div
        v-if="isVideoExpanded"
        class="video-expanded-mask"
        @click.self="closeExpandedVideo"
      >
        <section class="video-expanded-panel">
          <header class="video-expanded-head">
            <div>
              <h2>
                {{ currentStream.stream_name || activeStreamId }} 放大实时画面
              </h2>
              <span
                >AI 标注：{{ showAiAnnotations ? "开启" : "关闭" }} /
                区域规则：{{ showRuleOverlay ? "开启" : "关闭" }}</span
              >
            </div>
            <button
              type="button"
              class="zone-action"
              @click="closeExpandedVideo"
            >
              关闭
            </button>
          </header>
          <div
            class="video-expanded-stage"
            :class="{
              drawing: isDrawingForbiddenZone,
              locked: !showRuleOverlay,
            }"
            @mousedown.left.prevent="startForbiddenZoneDraw"
            @mousemove="updateForbiddenZoneDraw"
            @mouseup="finishForbiddenZoneDraw"
            @mouseleave="finishForbiddenZoneDraw"
          >
            <img
              v-if="!videoError"
              class="video-stream"
              :src="videoFeedUrl"
              alt="放大的 AI 处理后视频流"
              @load="handleVideoLoad"
              @error="handleVideoError"
            />
            <div
              class="classroom-fallback"
              :class="{ muted: !videoError && isVideoLive }"
            >
              <div class="board"></div>
              <div class="desk d1"></div>
              <div class="desk d2"></div>
              <div class="desk d3"></div>
            </div>
            <template v-if="showRuleOverlay">
              <div
                v-if="activeForbiddenRect"
                class="drawn-forbidden-zone drafting"
                :style="forbiddenZoneStyle"
              >
                <span>{{
                  isDrawingForbiddenZone
                    ? "绘制中"
                    : pendingForbiddenZone?.zone_name || "待确认区域"
                }}</span>
              </div>
            </template>
            <div
              v-if="showRuleOverlay && hasPendingForbiddenZone"
              class="zone-actions"
              @mousedown.stop
            >
              <input
                v-model="pendingForbiddenZone.zone_name"
                class="zone-draft-input"
                aria-label="区域名称"
                placeholder="区域名称"
              />
              <select
                v-model="pendingForbiddenZone.zone_type"
                class="zone-draft-select"
                aria-label="区域类型"
              >
                <option
                  v-for="option in zoneTypeOptions"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
              <button
                type="button"
                class="zone-action primary"
                :disabled="zoneSaving"
                @click.stop="confirmForbiddenZone"
              >
                {{ zoneSaving ? "保存中..." : "确定并启用" }}
              </button>
              <button
                type="button"
                class="zone-action"
                @click.stop="clearForbiddenZone"
              >
                取消草稿
              </button>
            </div>
          </div>
        </section>
      </div>
    </teleport>
  </div>
</template>
