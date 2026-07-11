<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  Bell,
  Camera,
  CircleCheck,
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
import { ElMessage } from "element-plus";
import {
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
  getVideoFeedUrl,
  login,
  logout,
} from "./services/smartClassApi";
import {
  clearAuthSession,
  getStoredToken,
  getStoredUser,
  joinResourceUrl,
  storeAuthSession,
} from "./services/http";
import lineDogGif from "./assets/line-dog.gif";

const activePage = ref("monitor");
const loginBackgroundVideo = `${import.meta.env.BASE_URL}auth/login-moonset.mp4`;
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
  phone: "",
  name: "",
  role: "teacher",
  password: "",
  confirmPassword: "",
  remark: "",
});
const personDialogVisible = ref(false);
const streamDialogVisible = ref(false);
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
const riskScoreSettings = ref([
  {
    type: "fire",
    label: "明火",
    score: 92,
    note: "最高危，发现后立即拉高综合分",
  },
  { type: "fall", label: "摔倒", score: 86, note: "高危，需现场确认人员状态" },
  {
    type: "stranger",
    label: "陌生人",
    score: 70,
    note: "中高风险，需核验身份",
  },
  {
    type: "phone",
    label: "手机违规",
    score: 62,
    note: "必须命中已确认禁用区后才参与评分",
  },
  {
    type: "zone",
    label: "区域入侵",
    score: 58,
    note: "按区域规则命中情况评分",
  },
  {
    type: "behavior",
    label: "行为异常",
    score: 42,
    note: "低头、睡觉等课堂行为异常",
  },
  { type: "general", label: "其他告警", score: 35, note: "未识别类型的兜底分" },
]);
const activeStreamId = ref("");
const activeAlertStatus = ref("全部");

// ── 钉钉 & AI 日报设置（存 localStorage）─────────────────
const SETTINGS_KEY = "smart_class_alert_settings";
const loadSettings = () => {
  try { return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {}; } catch { return {}; }
};
const saveSettings = (s) => localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
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
  generating: false,
  latestReport: saved.latestReport ?? null,
  reportHistory: saved.reportHistory ?? [],
});

watch(alertSettings, saveSettings, { deep: true });

// 联系人弹窗
const showContactModal = ref(false);
const newContact = ref({ name: "", mobile: "" });
const doAddContact = () => {
  const { name, mobile } = newContact.value;
  if (!name.trim()) { alert("请输入姓名"); return; }
  if (!/^1\d{10}$/.test(mobile.trim())) { alert("请输入有效的 11 位手机号"); return; }
  if (alertSettings.value.contacts.some(c => c.name === name.trim())) { alert("已存在"); return; }
  alertSettings.value.contacts.push({ name: name.trim(), mobile: mobile.trim() });
  newContact.value = { name: "", mobile: "" };
};
const removeContact = (name) => {
  if (name === "项重善" || name === "章志超") { alert("默认负责人不能删除"); return; }
  alertSettings.value.contacts = alertSettings.value.contacts.filter(c => c.name !== name);
};

// 日报
const showReportModal = ref(false);
const generateAiReport = async () => {
  alertSettings.value.generating = true;
  try {
    const alertsData = displayAlerts.value.slice(0, 50).map(a => ({
      alertType: a.alert_type || a.type || "未知",
      level: a.level || "info",
      streamId: a.stream_id || a.location || "",
    }));
    let report;
    try {
      const resp = await fetch("http://127.0.0.1:8080/report/generate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(alertsData),
      });
      if (resp.ok) report = await resp.json();
    } catch {}
    if (!report) {
      report = {
        date: new Date().toISOString().slice(0,10),
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
const isVideoLive = ref(false);
const videoError = ref(false);
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
const confirmedForbiddenZone = ref(null);

const streams = ref([]);
const alerts = ref([]);
const rules = ref([]);
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

const hasConfirmedForbiddenZone = computed(() =>
  Boolean(confirmedForbiddenZone.value),
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
const onlineStreamCount = computed(
  () => streams.value.filter((item) => item.status === "enabled").length,
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
  if (activeAlertStatus.value === "全部") return displayAlerts.value;
  return displayAlerts.value.filter(
    (item) => item.alert_status === activeAlertStatus.value,
  );
});

const highPriorityAlerts = computed(() => {
  return displayAlerts.value
    .filter((item) => item.level === "high")
    .slice(0, 4);
});

const activeRiskEvents = computed(() => {
  return [...alerts.value, ...analysisEvents.value]
    .filter((item) => {
      if (!isPhoneRelated(item)) return true;
      return isPhoneItemInForbiddenZone(item);
    })
    .map((item) => ({
      ...item,
      risk_type: classifyRiskType(item),
      risk_score: calculateEventRiskScore(item),
    }))
    .filter((item) => item.risk_score > 0)
    .sort((a, b) => b.risk_score - a.risk_score)
    .slice(0, 8);
});

const hasActiveRiskEvents = computed(() => activeRiskEvents.value.length > 0);

const aiEventFeed = computed(() => {
  return activeRiskEvents.value.slice(0, 3).map((item) => ({
    time: formatEventTime(item.occurred_at),
    text: `${riskTypeText(item.risk_type)}：${item.alert_name || item.event_name || item.alert_type || item.event_type || "AI 事件"}`,
  }));
});

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
    value: confirmedForbiddenZone.value
      ? "已确认"
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
    value: `${onlineStreamCount.value}/${streams.value.length || 0}`,
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

const activeModules = [
  {
    title: "实时视频与 AI 标注",
    text: "通过 Flask MJPEG 流展示实时画面，标注来自 AI 事件坐标。",
  },
  {
    title: "异常行为与安全告警",
    text: "告警列表来自 SpringBoot /alerts，状态按接口枚举展示。",
  },
  {
    title: "区域与规则配置",
    text: "区域坐标按 /zones 契约输出，规则来自 /rules。",
  },
  {
    title: "告警追踪与处置",
    text: "截图和录像使用后端返回的相对路径拼接 Nginx 地址。",
  },
];

const handlingGuides = [
  { title: "先看等级", text: "critical 和 high 优先进入人工确认。" },
  { title: "再看证据", text: "截图、录像片段和事件坐标用于复核目标与区域。" },
  { title: "最后闭环", text: "处理、误报或忽略后保留完整追溯记录。" },
];

const ruleTemplates = [
  { title: "课堂禁用手机", text: "先确认动态禁用区，再按阈值触发。" },
  { title: "入口陌生人", text: "绑定入口区域，识别失败后进入身份核验。" },
  { title: "危险源识别", text: "高优先级规则应缩短复核窗口并保留证据。" },
];

const registrationSteps = computed(() => [
  { title: "档案同步", value: `${students.value.length} 条人员记录` },
  { title: "人脸采集", value: `${registeredStudentCount.value} 人完成` },
  { title: "异常核验", value: `${strangerCount.value} 条待确认` },
]);

const dependencySteps = [
  { title: "摄像头推流", text: "RTMP 写入云端 Nginx 流媒体服务。" },
  { title: "AI 推理", text: "Flask 拉流并输出视频流、事件和摘要。" },
  { title: "后端入库", text: "SpringBoot 管理告警、规则、人员和视频源数据。" },
  { title: "前端展示", text: "Vue 只展示接口返回结果，不伪造业务状态。" },
];

const operationLogs = [
  "自动刷新告警列表，失败时显示接口错误。",
  "视频流不可达时展示空状态，不替换成业务结果。",
  "只有显式开启 mock 模式时才使用本地演示数据。",
];
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
  return (
    pendingForbiddenZone.value?.rect ||
    confirmedForbiddenZone.value?.rect ||
    null
  );
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

const forbiddenZoneCoordinates = computed(() => {
  return confirmedForbiddenZone.value?.coordinates || [];
});

const forbiddenZonePayload = computed(() => ({
  zone_type: "phone_forbidden",
  shape_type: "rectangle",
  stream_id: activeStreamId.value,
  coordinates: forbiddenZoneCoordinates.value,
}));

const phoneDetectionSources = computed(() => {
  return [...analysisEvents.value, ...alerts.value]
    .filter(isPhoneRelated)
    .map((item) => ({ item, rect: normalizeDetectionRect(item) }))
    .filter(({ rect }) => rect);
});

const phoneDetectionsInForbiddenZone = computed(() => {
  const zone = confirmedForbiddenZone.value?.rect;
  if (!zone) return [];
  return phoneDetectionSources.value.filter(({ rect }) =>
    rectsIntersect(zone, rect),
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

const aiOverlayTargets = computed(() => {
  return analysisEvents.value
    .filter((item) => !isPhoneRelated(item) || isPhoneItemInForbiddenZone(item))
    .map((item) => ({ item, rect: normalizeDetectionRect(item) }))
    .filter(({ rect }) => rect)
    .slice(0, 6)
    .map(({ item, rect }) => ({
      id: item.event_id || `${item.event_type}-${item.occurred_at}`,
      label: item.event_name || item.alert_name || item.event_type || "AI 目标",
      confidence: item.confidence,
      level: item.level,
      style: {
        left: `${rect.x * 100}%`,
        top: `${rect.y * 100}%`,
        width: `${Math.max(rect.width * 100, 6)}%`,
        height: `${Math.max(rect.height * 100, 6)}%`,
      },
    }));
});

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

function statusType(status) {
  return (
    {
      unhandled: "danger",
      processing: "warning",
      handled: "success",
      false_alarm: "info",
      ignored: "info",
      online: "success",
      offline: "danger",
      unknown: "info",
    }[status] || "info"
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
      35,
  );
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
  const stage = videoStageRef.value;
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

  const frameWidth = Number(
    source.frame_width ||
      source.width ||
      source.video_width ||
      source.target?.frame_width,
  );
  const frameHeight = Number(
    source.frame_height ||
      source.height ||
      source.video_height ||
      source.target?.frame_height,
  );
  if (
    !Number.isFinite(frameWidth) ||
    !Number.isFinite(frameHeight) ||
    frameWidth <= 0 ||
    frameHeight <= 0
  )
    return null;

  return {
    x: clampUnit(Math.min(x1, x2) / frameWidth),
    y: clampUnit(Math.min(y1, y2) / frameHeight),
    width: clampUnit(Math.abs(x2 - x1) / frameWidth),
    height: clampUnit(Math.abs(y2 - y1) / frameHeight),
  };
}

function normalizeDetectionRect(item = {}) {
  const target = item.target || item.target_info || {};
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

  if (Array.isArray(candidate)) {
    return candidate.length === 4 &&
      candidate.every((value) => typeof value === "number")
      ? rectFromBbox(candidate, item)
      : rectFromCoordinates(candidate);
  }

  if (candidate && typeof candidate === "object") {
    const x = Number(candidate.x ?? candidate.left);
    const y = Number(candidate.y ?? candidate.top);
    const width = Number(candidate.width ?? candidate.w);
    const height = Number(candidate.height ?? candidate.h);
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
  pendingForbiddenZone.value = {
    rect,
    coordinates: buildCoordinatesFromRect(rect),
  };
}

function cancelForbiddenZoneDraw() {
  isDrawingForbiddenZone.value = false;
  forbiddenZoneStart.value = null;
  forbiddenZoneCurrent.value = null;
}

function confirmForbiddenZone() {
  if (!pendingForbiddenZone.value) return;
  confirmedForbiddenZone.value = pendingForbiddenZone.value;
  pendingForbiddenZone.value = null;
}

function clearForbiddenZone() {
  pendingForbiddenZone.value = null;
  confirmedForbiddenZone.value = null;
  cancelForbiddenZoneDraw();
}

function toggleAiAnnotations() {
  showAiAnnotations.value = !showAiAnnotations.value;
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

function submitRegisterRequest() {
  const phonePattern = /^1[3-9]\d{9}$/;
  if (!phonePattern.test(registerForm.value.phone)) {
    setAuthNotice("请输入有效的 11 位手机号。", "warning");
    return;
  }
  if (!registerForm.value.name || !registerForm.value.password) {
    setAuthNotice("请填写姓名和密码。", "warning");
    return;
  }
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    setAuthNotice("两次输入的密码不一致。", "warning");
    return;
  }
  setAuthNotice(
    "手机号注册接口尚未在后端文档中确认，当前仅保留前端申请流程。请联系管理员创建账号。",
    "info",
  );
  authMode.value = "login";
  authForm.value.username = registerForm.value.phone;
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
    students: fetchStudents({ page: 1, page_size: 10 }),
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
  students.value = results.students.ok
    ? normalizeList(results.students.value)
    : [];
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
      const [nextSummary, nextEvents] = await Promise.all([
        fetchAnalysisSummary(activeStreamId.value),
        fetchAnalysisEvents({ stream_id: activeStreamId.value }),
      ]);
      summary.value = nextSummary || {};
      analysisEvents.value = normalizeList(nextEvents);
    } catch (error) {
      loadErrors.value.summary = error?.message || "AI 分析接口请求失败";
    }
  }
}

async function switchStream(streamId) {
  activeStreamId.value = streamId;
  isVideoLive.value = false;
  videoError.value = false;
  clearForbiddenZone();
  try {
    const [nextSummary, nextEvents] = await Promise.all([
      fetchAnalysisSummary(streamId),
      fetchAnalysisEvents({ stream_id: streamId }),
    ]);
    summary.value = nextSummary || {};
    analysisEvents.value = normalizeList(nextEvents);
    loadErrors.value.summary = "";
    loadErrors.value.events = "";
  } catch (error) {
    summary.value = {};
    analysisEvents.value = [];
    loadErrors.value.summary = error?.message || "AI 分析接口请求失败";
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
  personDialogVisible.value = true;
}

function savePerson() {
  const form = personForm.value;
  if (!form.name.trim()) {
    ElMessage.warning("请填写人员姓名。");
    return;
  }
  students.value = [
    {
      id: Date.now(),
      student_no: form.student_no.trim() || `P${String(Date.now()).slice(-6)}`,
      name: form.name.trim(),
      class_name: form.class_name.trim() || "未分组",
      status: "active",
      face_registered: Boolean(form.face_registered),
      last_seen: "--",
    },
    ...students.value,
  ];
  personDialogVisible.value = false;
  ElMessage.success("已新增人员到当前前端列表。");
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

function saveStream() {
  const form = streamForm.value;
  if (!form.stream_id.trim() || !form.stream_name.trim()) {
    ElMessage.warning("请填写视频源编号和名称。");
    return;
  }
  if (streams.value.some((item) => item.stream_id === form.stream_id.trim())) {
    ElMessage.warning("视频源编号已存在，请换一个。");
    return;
  }
  const nextStream = {
    id: Date.now(),
    stream_id: form.stream_id.trim(),
    stream_name: form.stream_name.trim(),
    location: form.location.trim() || "未填写位置",
    status: form.status,
    latency: "--",
    rtmp_url: form.rtmp_url.trim(),
    remark: "前端临时新增",
  };
  streams.value = [nextStream, ...streams.value];
  activeStreamId.value = nextStream.stream_id;
  streamDialogVisible.value = false;
  ElMessage.success("已新增视频源到当前前端列表。");
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
      class="auth-bg-video"
      autoplay
      muted
      loop
      playsinline
      preload="auto"
      aria-hidden="true"
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
          手机号注册
        </button>
      </div>

      <div class="auth-title">
        <h2>{{ authMode === "login" ? "登录系统" : "手机号注册预留" }}</h2>
        <p>
          {{
            authMode === "login"
              ? "使用后端已确定的 /auth/login 接口进入系统。"
              : "后端文档尚未确认手机号注册接口，当前仅保留前端申请流程。"
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
        @submit.prevent="submitRegisterRequest"
      >
        <el-form-item label="手机号">
          <el-input
            v-model="registerForm.phone"
            placeholder="请输入 11 位手机号"
          />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="registerForm.name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="申请角色">
          <el-segmented
            v-model="registerForm.role"
            :options="[
              { label: '教师', value: 'teacher' },
              { label: '管理员', value: 'admin' },
            ]"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="registerForm.password"
            placeholder="设置密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input
            v-model="registerForm.confirmPassword"
            placeholder="再次输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="申请说明">
          <el-input
            v-model="registerForm.remark"
            type="textarea"
            :rows="2"
            placeholder="例如任课班级、管理范围或申请原因"
          />
        </el-form-item>
        <el-button
          class="auth-submit"
          type="primary"
          @click="submitRegisterRequest"
          >提交注册申请</el-button
        >
      </el-form>

      <div class="auth-contract">
        <b>接口契约</b>
        <span
          >已确定：`POST /auth/login`、`GET
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
          v-for="item in navItems"
          :key="item.key"
          class="nav-button"
          :class="{ active: activePage === item.key }"
          :title="item.label"
          @click="activePage = item.key"
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
          <el-button :icon="Setting" @click="activePage = 'rules'"
            >规则配置</el-button
          >
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
                  {{ videoError ? "视频不可用" : "实时联调" }}
                </span>
              </div>

              <div
                v-if="showRuleOverlay && activeForbiddenRect"
                class="drawn-forbidden-zone"
                :class="{
                  drafting: isDrawingForbiddenZone || hasPendingForbiddenZone,
                  confirmed: hasConfirmedForbiddenZone,
                }"
                :style="forbiddenZoneStyle"
              >
                <span>{{
                  isDrawingForbiddenZone
                    ? "绘制中"
                    : hasPendingForbiddenZone
                      ? "待确认禁用区"
                      : "已确认禁用区"
                }}</span>
              </div>
              <div v-else-if="showRuleOverlay" class="draw-hint">
                按住鼠标左键拖拽，绘制禁用区
              </div>
              <div v-else class="draw-hint muted">区域规则层已关闭</div>
              <div
                v-if="
                  showRuleOverlay &&
                  (hasPendingForbiddenZone || hasConfirmedForbiddenZone)
                "
                class="zone-actions"
              >
                <button
                  v-if="hasPendingForbiddenZone"
                  type="button"
                  class="zone-action primary"
                  @click.stop="confirmForbiddenZone"
                >
                  确定
                </button>
                <button
                  type="button"
                  class="zone-action"
                  @click.stop="clearForbiddenZone"
                >
                  删除重新选择
                </button>
              </div>
              <template v-if="showAiAnnotations">
                <div
                  v-for="target in aiOverlayTargets"
                  :key="target.id"
                  class="person-box api-box"
                  :class="target.level"
                  :style="target.style"
                >
                  <span
                    >{{ target.label
                    }}{{
                      target.confidence
                        ? ` ${Math.round(target.confidence * 100)}%`
                        : ""
                    }}</span
                  >
                </div>
              </template>

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

          <section class="overview-grid">
            <div class="panel">
              <div class="panel-head compact">
                <h2>告警追踪记录</h2>
                <el-segmented
                  v-model="activeAlertStatus"
                  :options="statusOptions"
                  size="small"
                />
              </div>
              <el-table :data="filteredAlerts" height="248" class="clean-table">
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

            <div class="panel">
              <div class="panel-head compact">
                <h2>前端呈现模块</h2>
                <el-button
                  size="small"
                  :icon="User"
                  @click="activePage = 'people'"
                  >注册人脸</el-button
                >
              </div>
              <div class="module-grid">
                <article v-for="module in activeModules" :key="module.title">
                  <b>{{ module.title }}</b>
                  <span>{{ module.text }}</span>
                </article>
              </div>
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
              <div class="event-feed">
                <article
                  v-for="item in aiEventFeed"
                  :key="`${item.time}-${item.text}`"
                >
                  <time>{{ item.time }}</time>
                  <span>{{ item.text }}</span>
                </article>
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
                  <b>当前禁用区</b>
                  <span v-if="forbiddenZoneCoordinates.length">
                    {{
                      forbiddenZoneCoordinates
                        .map(
                          (point) =>
                            `(${formatCoord(point.x)}, ${formatCoord(point.y)})`,
                        )
                        .join(" / ")
                    }}
                  </span>
                  <span v-else-if="hasPendingForbiddenZone"
                    >区域待确认，点击确定后输出四角坐标</span
                  >
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
                  v-model="rule.enabled"
                  :disabled="!hasConfirmedForbiddenZone && isPhoneRelated(rule)"
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
        <div class="module-board" style="margin-bottom:6px">
          <section class="panel span-12" style="padding:8px 20px;display:flex;gap:50px;align-items:center">
            <label style="display:flex;align-items:center;gap:10px">
              <el-switch v-model="alertSettings.dingtalkEnabled" />
              <b>钉钉通知</b>
              <span v-if="alertSettings.dingtalkEnabled" style="font-size:13px;color:#67c23a">● {{ alertSettings.responsible }}</span>
              <el-button v-if="alertSettings.dingtalkEnabled" size="small" @click="showContactModal=true">管理联系人</el-button>
            </label>
            <label style="display:flex;align-items:center;gap:10px">
              <el-switch v-model="alertSettings.aiReportEnabled" />
              <b>AI日报</b>
              <el-time-select v-if="alertSettings.aiReportEnabled" v-model="alertSettings.reportTime" start="00:00" end="23:59" step="00:30" size="small" style="width:100px"/>
              <el-button v-if="alertSettings.aiReportEnabled" size="small" type="primary" :loading="alertSettings.generating" @click="generateAiReport">生成日报</el-button>
              <el-button v-if="alertSettings.latestReport" size="small" @click="showReportModal=true">往期日报</el-button>
            </label>
          </section>
        </div>

        <!-- 最新日报卡片 -->
        <div v-if="alertSettings.latestReport" class="module-board" style="margin-bottom:6px">
          <section class="panel span-12" style="padding:12px 20px;background:#f0f9ff;border-left:3px solid #409EFF">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <b>最新日报 — {{ alertSettings.latestReport.date }}</b>
              <span style="font-size:12px;color:#909399">{{ alertSettings.latestReport.time }}</span>
            </div>
            <p style="margin:6px 0 0;font-size:14px;line-height:1.7;white-space:pre-wrap">{{ alertSettings.latestReport.summary }}</p>
          </section>
        </div>

        <!-- 联系人弹窗 -->
        <div v-if="showContactModal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.45);z-index:9999;display:flex;justify-content:center;align-items:center" @click.self="showContactModal=false">
          <div style="background:#fff;padding:28px;border-radius:10px;width:550px;max-height:75vh;overflow-y:auto;box-shadow:0 8px 30px rgba(0,0,0,.12)">
            <h2 style="margin:0 0 20px;font-size:18px">联系人管理</h2>
            <div v-for="c in alertSettings.contacts" style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0">
              <div>
                <span v-if="c.name===alertSettings.responsible" style="color:#67c23a;margin-right:6px">●</span>
                <b>{{ c.name }}</b>
                <span style="color:#909399;font-size:13px;margin-left:8px">{{ c.mobile }}</span>
              </div>
              <div style="display:flex;gap:8px">
                <el-button v-if="c.name!==alertSettings.responsible" size="small" type="primary" plain @click="alertSettings.responsible=c.name">设为负责人</el-button>
                <el-button v-if="c.name!=='项重善'&&c.name!=='章志超'" size="small" type="danger" plain @click="removeContact(c.name)">删除</el-button>
              </div>
            </div>
            <div style="display:flex;gap:10px;margin-top:16px;align-items:center">
              <input v-model="newContact.name" placeholder="姓名" style="flex:1;padding:8px 12px;border:1px solid #dcdfe6;border-radius:6px;font-size:14px"/>
              <input v-model="newContact.mobile" placeholder="手机号" style="flex:2;padding:8px 12px;border:1px solid #dcdfe6;border-radius:6px;font-size:14px"/>
              <el-button type="primary" size="default" @click="doAddContact">添加</el-button>
            </div>
            <div style="text-align:right;margin-top:20px">
              <el-button @click="showContactModal=false">关闭</el-button>
            </div>
          </div>
        </div>

        <!-- 往期日报弹窗 -->
        <div v-if="showReportModal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.45);z-index:9999;display:flex;justify-content:center;align-items:center" @click.self="showReportModal=false">
          <div style="background:#fff;padding:28px;border-radius:10px;width:650px;max-height:80vh;overflow-y:auto;box-shadow:0 8px 30px rgba(0,0,0,.12)">
            <h2 style="margin:0 0 20px;font-size:18px">往期日报（{{ alertSettings.reportHistory.length }} 条）</h2>
            <div v-if="alertSettings.reportHistory.length===0" style="color:#909399;text-align:center;padding:40px">暂无日报</div>
            <div v-for="(r,i) in alertSettings.reportHistory" style="padding:14px 0;border-bottom:1px solid #f0f0f0">
              <div style="font-size:12px;color:#909399;margin-bottom:4px">{{ r.date }} {{ r.time?.slice(11,16)||'' }}</div>
              <div style="font-size:14px;line-height:1.7;white-space:pre-wrap">{{ r.summary }}</div>
            </div>
            <div style="text-align:right;margin-top:20px">
              <el-button @click="showReportModal=false">关闭</el-button>
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
              <el-input
                class="search-box"
                :prefix-icon="Search"
                placeholder="搜索类型、说明或视频源"
              />
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
              <el-table-column label="证据" width="150">
                <template #default="{ row }">
                  <el-button
                    size="small"
                    text
                    :disabled="!row.snapshot_url"
                    :href="resourceUrl(row.snapshot_url)"
                    >截图</el-button
                  >
                  <el-button
                    size="small"
                    text
                    :disabled="!row.record_url"
                    :href="resourceUrl(row.record_url)"
                    >片段</el-button
                  >
                </template>
              </el-table-column>
            </el-table>
          </section>

          <section class="panel span-7">
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
                />
              </article>
            </div>
          </section>

          <section class="panel span-5">
            <div class="panel-head compact">
              <h2>处置建议</h2>
            </div>
            <div class="info-list alert-guide-list">
              <article
                v-for="guide in handlingGuides"
                :key="guide.title"
                class="info-item"
              >
                <b>{{ guide.title }}</b>
                <span>{{ guide.text }}</span>
              </article>
            </div>
          </section>

          <section class="panel span-6">
            <div class="panel-head compact">
              <h2>证据链概览</h2>
            </div>
            <div class="evidence-grid">
              <article>
                <b>截图</b>
                <span>目标框、区域、时间戳</span>
              </article>
              <article>
                <b>片段</b>
                <span>触发前后短视频</span>
              </article>
              <article>
                <b>记录</b>
                <span>状态、备注、处理人</span>
              </article>
            </div>
          </section>

          <section class="panel span-6">
            <div class="panel-head compact">
              <h2>处理节奏</h2>
            </div>
            <div class="flow-steps compact-flow">
              <article>
                <b>接收</b>
                <span>AI 候选事件入队</span>
              </article>
              <article>
                <b>确认</b>
                <span>人工复核证据</span>
              </article>
              <article>
                <b>闭环</b>
                <span>状态和备注入库</span>
              </article>
            </div>
          </section>
        </div>
      </section>

      <section v-else-if="activePage === 'rules'" class="page-grid module-page">
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
                  >用于承接 `/zones` 和 `/rules`，后续可扩展为 ROI 绘制。</span
                >
              </div>
              <el-button type="primary" :icon="CircleCheck">保存规则</el-button>
            </div>
            <div class="rule-editor">
              <article v-for="rule in rules" :key="rule.id">
                <div>
                  <b>{{ ruleNameText(rule) }}</b>
                  <span>{{ ruleSummaryText(rule) }}</span>
                </div>
                <el-input-number
                  v-model="rule.threshold_seconds"
                  :min="1"
                  :max="30"
                  size="small"
                />
                <el-switch
                  v-model="rule.enabled"
                  :disabled="!hasConfirmedForbiddenZone && isPhoneRelated(rule)"
                />
              </article>
            </div>
          </section>

          <section class="panel zone-panel span-6">
            <div class="panel-head compact">
              <h2>
                {{
                  currentStream.stream_name || activeStreamId || "当前视频源"
                }}
                区域示意
              </h2>
            </div>
            <div class="zone-canvas compact-zone">
              <div class="canvas-board">讲台 / 黑板</div>
              <div class="seat-zone s1">座位区</div>
              <div class="seat-zone s2">动态禁用区</div>
              <div class="seat-zone s3">危险区</div>
            </div>
          </section>

          <section class="panel span-6">
            <div class="panel-head compact">
              <h2>实时禁用区坐标</h2>
            </div>
            <div class="coordinate-export">
              <p>后续提交给其他模块的矩形区域使用以下四角归一化坐标。</p>
              <pre>{{
                JSON.stringify(
                  hasConfirmedForbiddenZone
                    ? forbiddenZonePayload
                    : {
                        status: hasPendingForbiddenZone
                          ? "pending_confirm"
                          : "empty",
                        message: "禁用区确认后才输出坐标",
                      },
                  null,
                  2,
                )
              }}</pre>
            </div>
          </section>

          <section class="panel span-6">
            <div class="panel-head compact">
              <h2>推荐模板</h2>
            </div>
            <div class="info-list">
              <article
                v-for="item in ruleTemplates"
                :key="item.title"
                class="info-item"
              >
                <b>{{ item.title }}</b>
                <span>{{ item.text }}</span>
              </article>
            </div>
          </section>

          <section class="panel span-6">
            <div class="panel-head compact">
              <h2>规则联动</h2>
            </div>
            <div class="flow-steps compact-flow">
              <article>
                <b>区域命中</b>
                <span>目标进入 ROI</span>
              </article>
              <article>
                <b>阈值复核</b>
                <span>持续时间达标</span>
              </article>
              <article>
                <b>生成告警</b>
                <span>写入事件队列</span>
              </article>
            </div>
          </section>
        </div>
      </section>

      <section
        v-else-if="activePage === 'people'"
        class="page-grid module-page"
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
          <section class="panel span-8">
            <div class="panel-head">
              <div>
                <h2>人员与人脸库</h2>
                <span
                  >人员基础信息来自 `/students`，人脸注册提交到
                  `/students/{id}/face`。</span
                >
              </div>
              <el-button type="primary" :icon="User" @click="openPersonDialog"
                >新增人员</el-button
              >
            </div>
            <el-table :data="students" height="320" class="clean-table">
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
            </el-table>
          </section>

          <section class="panel span-4">
            <div class="panel-head compact">
              <h2>陌生人核验</h2>
            </div>
            <div class="identity-preview">
              <div class="face-placeholder">
                <el-icon><User /></el-icon>
              </div>
              <b>发现未登记人员</b>
              <p>
                系统保留最近一次截图与视频片段，等待管理员确认身份或加入访客名单。
              </p>
            </div>
          </section>

          <section class="panel span-6">
            <div class="panel-head compact">
              <h2>注册进度</h2>
            </div>
            <div class="progress-stack">
              <article v-for="item in registrationSteps" :key="item.title">
                <b>{{ item.title }}</b>
                <span>{{ item.value }}</span>
              </article>
            </div>
          </section>

          <section class="panel span-6">
            <div class="panel-head compact">
              <h2>身份策略</h2>
            </div>
            <div class="info-list two-info">
              <article class="info-item">
                <b>学生档案</b>
                <span>用于课堂识别、到场记录和行为关联。</span>
              </article>
              <article class="info-item">
                <b>访客名单</b>
                <span>经人工确认后可临时加入白名单。</span>
              </article>
            </div>
          </section>
        </div>
      </section>

      <section v-else class="page-grid module-page">
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
          <section class="panel span-7">
            <div class="panel-head">
              <div>
                <h2>视频源与服务状态</h2>
                <span
                  >对应 `/streams`、`/model/status`、`/system/health`。</span
                >
              </div>
              <el-button :icon="Switch" @click="openStreamDialog"
                >新增视频源</el-button
              >
            </div>
            <div class="stream-list">
              <article v-for="stream in streams" :key="stream.stream_id">
                <div>
                  <b>{{ stream.stream_name }}</b>
                  <span>{{ stream.rtmp_url }}</span>
                </div>
                <el-tag :type="statusType(stream.status)">{{
                  stream.status
                }}</el-tag>
              </article>
            </div>
          </section>

          <section class="panel span-5">
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

          <section class="panel span-8">
            <div class="panel-head compact">
              <h2>依赖调用链路</h2>
            </div>
            <div class="flow-steps">
              <article v-for="item in dependencySteps" :key="item.title">
                <b>{{ item.title }}</b>
                <span>{{ item.text }}</span>
              </article>
            </div>
          </section>

          <section class="panel span-4">
            <div class="panel-head compact">
              <h2>运行提示</h2>
            </div>
            <div class="info-list">
              <article
                v-for="item in operationLogs"
                :key="item"
                class="info-item"
              >
                <b>状态</b>
                <span>{{ item }}</span>
              </article>
            </div>
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
          <el-form-item label="人脸状态">
            <el-switch
              v-model="personForm.face_registered"
              active-text="已注册"
              inactive-text="待注册"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="personDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePerson">确定新增</el-button>
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
          <div class="video-expanded-stage">
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
            <div
              v-if="showRuleOverlay && activeForbiddenRect"
              class="drawn-forbidden-zone"
              :class="{
                drafting: isDrawingForbiddenZone || hasPendingForbiddenZone,
                confirmed: hasConfirmedForbiddenZone,
              }"
              :style="forbiddenZoneStyle"
            >
              <span>{{
                hasPendingForbiddenZone ? "待确认禁用区" : "已确认禁用区"
              }}</span>
            </div>
            <template v-if="showAiAnnotations">
              <div
                v-for="target in aiOverlayTargets"
                :key="target.id"
                class="person-box api-box"
                :class="target.level"
                :style="target.style"
              >
                <span
                  >{{ target.label
                  }}{{
                    target.confidence
                      ? ` ${Math.round(target.confidence * 100)}%`
                      : ""
                  }}</span
                >
              </div>
            </template>
          </div>
        </section>
      </div>
    </teleport>
  </div>
</template>
