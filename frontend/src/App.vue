<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
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
import { ALERT_STATUS_MAP } from "./data/mockData";

const activePage = ref("monitor");
const loginBackgroundVideo = `${import.meta.env.BASE_URL}auth/login-moonset.mp4`;
const isAuthenticated = ref(Boolean(getStoredToken()));
const currentUser = ref(getStoredUser());
const authMode = ref("login");
const authLoading = ref(false);
const authNotice = ref("");
const authNoticeType = ref("info");
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
const activeStreamId = ref("A101");
const activeAlertStatus = ref("全部");
const isVideoLive = ref(false);
const videoError = ref(false);
const isDay = ref(true);
const showAiAnnotations = ref(true);
const showRuleOverlay = ref(true);
const isVideoExpanded = ref(false);
const planterWaterLevel = ref(0);
const isWateringPlanter = ref(false);
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

let refreshId;
let wateringTimerId;

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
];

const currentStream = computed(() => {
  return (
    streams.value.find((item) => item.stream_id === activeStreamId.value) ||
    streams.value[0] ||
    {}
  );
});

const videoFeedUrl = computed(() => getVideoFeedUrl(activeStreamId.value));

const dayTitle = computed(() => (isDay.value ? "白天模式" : "夜间模式"));
const dayHint = computed(() =>
  isDay.value ? "点击切换到护眼黑夜" : "点击切换到明亮白天",
);
const userDisplayName = computed(
  () =>
    currentUser.value?.nickname || currentUser.value?.username || "演示用户",
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
  if (hasConfirmedForbiddenZone.value) return alerts.value;
  return alerts.value.filter((item) => !isPhoneRelated(item));
});

const pendingAlertCount = computed(() => {
  return displayAlerts.value.filter((item) =>
    ["unhandled", "processing"].includes(item.alert_status),
  ).length;
});
const highAlertCount = computed(
  () => displayAlerts.value.filter((item) => item.level === "high").length,
);
const confirmedAlertCount = computed(
  () =>
    displayAlerts.value.filter((item) => item.alert_status === "handled")
      .length,
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
  () => streams.value.filter((item) => item.status === "online").length,
);

const healthItems = computed(() => [
  { label: "RTMP 流媒体", value: health.value.rtmp || "unknown" },
  { label: "AI 分析服务", value: health.value.ai || "unknown" },
  { label: "业务后端", value: health.value.api || "unknown" },
  { label: "MySQL 数据库", value: health.value.database || "unknown" },
]);

const metricCards = computed(() => [
  { label: "当前视频源", value: activeStreamId.value, icon: Camera },
  {
    label: "在线视频源",
    value: `${onlineStreamCount.value}/${streams.value.length || 0}`,
    icon: Clock,
  },
  {
    label: "今日告警",
    value: stats.value.today_alerts ?? 0,
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

const aiEventFeed = computed(() => {
  const fallback = hasConfirmedForbiddenZone.value
    ? [
        { time: "10:25", text: "行为识别模型完成第三排目标复核" },
        { time: "10:24", text: "截图、短视频和事件记录已完成关联" },
        { time: "10:23", text: "建议优先确认手机违规与低头叠加事件" },
      ]
    : [
        { time: "10:25", text: "行为识别模型完成第三排目标复核" },
        { time: "10:24", text: "当前未确认禁用区，手机违规检测未启用" },
        { time: "10:23", text: "请先拖拽并确认禁用区，再生成手机相关告警" },
      ];
  const source = analysisEvents.value.length ? analysisEvents.value : fallback;
  return source
    .filter((item) => hasConfirmedForbiddenZone.value || !isPhoneRelated(item))
    .slice(0, 3);
});

const activeSummary = computed(() => {
  if (hasConfirmedForbiddenZone.value) return summary.value || {};
  return {
    risk_score: Math.min(summary.value?.risk_score || 36, 42),
    title: "等待禁用区确认",
    summary:
      "当前未确认手机禁用区，手机违规检测和相关告警暂不启用。请在实时画面中拖拽区域并点击确定。",
    actions: ["绘制禁用区", "点击确定", "启用手机规则"],
    timeline: [
      { time: "当前", text: "手机违规规则等待禁用区坐标" },
      { time: "下一步", text: "确认禁用区后输出四角归一化坐标" },
    ],
  };
});

const actionItems = computed(() => {
  if (!hasConfirmedForbiddenZone.value)
    return ["绘制禁用区", "点击确定", "启用手机规则"];
  return activeSummary.value.actions?.length
    ? activeSummary.value.actions
    : ["自动抓拍", "等待人工确认", "保留追踪记录"];
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
  { label: "最高优先级", value: "明火", tone: "danger" },
  { label: "复核窗口", value: "3-6 秒", tone: "warn" },
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
    value:
      (modelStatus.value.models || [])
        .map((m) => `${m.model_name}@${m.version}`)
        .join(", ") || "--",
    tone: "brand",
  },
  {
    label: "推理耗时",
    value: `${(modelStatus.value.models || []).find((m) => m.avg_infer_ms)?.avg_infer_ms || "--"} ms`,
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
    text: "单路画面、身份标签、目标框、行为标注。",
  },
  {
    title: "异常行为与安全告警",
    text: "承接 AI 候选事件，展示等级、位置与处置状态。",
  },
  { title: "区域与规则配置", text: "动态禁用区、危险区和阈值开关。" },
  { title: "告警追溯与处置", text: "告警列表、截图片段、备注和状态闭环。" },
];

const handlingGuides = [
  { title: "先看等级", text: "明火、摔倒、陌生人优先进入人工确认。" },
  { title: "再看证据", text: "截图和视频片段用于确认目标、区域和持续时间。" },
  { title: "最后闭环", text: "处理、误报或转交后保留完整追溯记录。" },
];

const ruleTemplates = [
  { title: "课堂禁用手机", text: "先确认动态禁用区，再按阈值触发。" },
  { title: "门口陌生人", text: "绑定入口区域，识别失败后进入身份核验。" },
  { title: "危险源识别", text: "明火、摔倒使用较短阈值并提升优先级。" },
];

const registrationSteps = computed(() => [
  { title: "档案同步", value: "已接入学生基础信息" },
  { title: "人脸采集", value: `${registeredStudentCount.value} 人完成` },
  { title: "异常核验", value: `${strangerCount.value} 条待确认` },
]);

const dependencySteps = [
  { title: "摄像头推流", text: "RTMP 写入流媒体服务" },
  { title: "AI 推理", text: "抽帧、检测、身份识别" },
  { title: "后端入库", text: "告警、规则、人员数据落库" },
  { title: "前端展示", text: "实时画面与处置闭环" },
];

const operationLogs = [
  "自动刷新告警列表，保持 5 秒轮询。",
  "视频流不可达时展示课堂示意图。",
  "接口异常时启用本地演示数据兜底。",
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

function levelText(level) {
  return (
    {
      info: "信息",
      warning: "警告",
      high: "高危",
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
    rtmp: payload.rtmp || payload.rtmp_status || payload.media || "online",
    ai: payload.ai || payload.ai_status || "online",
    api: payload.api || payload.backend || "online",
    database: payload.database || payload.db || "online",
  };
}

function clampUnit(value) {
  return Math.min(1, Math.max(0, value));
}

function formatCoord(value) {
  return Number(value).toFixed(3);
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

function setAuthNotice(message, type = "info") {
  authNotice.value = message;
  authNoticeType.value = type;
}

function normalizeUser(loginPayload, username) {
  const user =
    loginPayload?.user || loginPayload?.user_info || loginPayload || {};
  return {
    user_id: user.user_id || user.id || "demo-user",
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
  } catch {
    const demoUser = {
      user_id: "demo-user",
      username: authForm.value.username,
      nickname: "演示教师",
      role: authForm.value.username === "admin" ? "admin" : "teacher",
    };
    setAuthNotice("后端认证接口暂不可用，已进入演示登录模式。", "warning");
    await enterAuthenticatedApp(
      demoUser,
      "demo-token",
      authForm.value.remember,
    );
  } finally {
    authLoading.value = false;
  }
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
    "手机号注册接口尚未在后端文档中确认，当前已作为前端预留申请流程展示。请联系管理员创建账号。",
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
    fetchAlerts({
      stream_id: activeStreamId.value,
      page: 1,
      page_size: 20,
    }).then((payload) => {
      alerts.value = normalizeList(payload);
    });
  }, 5000);
}

async function loadDashboard() {
  const [
    streamResult,
    alertResult,
    statsResult,
    ruleResult,
    studentResult,
    healthResult,
    summaryResult,
    eventResult,
    modelResult,
  ] = await Promise.all([
    fetchStreams(),
    fetchAlerts({ stream_id: activeStreamId.value, page: 1, page_size: 20 }),
    fetchAlertStats({ stream_id: activeStreamId.value }),
    fetchRules(),
    fetchStudents({ page: 1, page_size: 10 }),
    fetchSystemHealth(),
    fetchAnalysisSummary(activeStreamId.value),
    fetchAnalysisEvents({ stream_id: activeStreamId.value }),
    fetchModelStatus(),
  ]);

  streams.value = normalizeList(streamResult);
  alerts.value = normalizeList(alertResult);
  stats.value = statsResult || {};
  rules.value = normalizeList(ruleResult);
  students.value = normalizeList(studentResult);
  health.value = normalizeHealth(healthResult || {});
  summary.value = summaryResult || {};
  analysisEvents.value = normalizeList(eventResult);
  modelStatus.value = modelResult || {};

  if (
    !streams.value.some((item) => item.stream_id === activeStreamId.value) &&
    streams.value[0]
  ) {
    activeStreamId.value = streams.value[0].stream_id;
  }
}

async function switchStream(streamId) {
  activeStreamId.value = streamId;
  isVideoLive.value = false;
  videoError.value = false;
  clearForbiddenZone();
  summary.value = await fetchAnalysisSummary(streamId);
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

function waterPlanter() {
  planterWaterLevel.value = Math.min(planterWaterLevel.value + 1, 4);
  isWateringPlanter.value = false;
  window.clearTimeout(wateringTimerId);
  window.requestAnimationFrame(() => {
    isWateringPlanter.value = true;
    wateringTimerId = window.setTimeout(() => {
      isWateringPlanter.value = false;
    }, 900);
  });
}

onMounted(async () => {
  if (!isAuthenticated.value) return;
  try {
    currentUser.value = await fetchCurrentUser();
    storeAuthSession(getStoredToken(), currentUser.value, true);
  } catch {
    currentUser.value = currentUser.value || normalizeUser({}, "demo");
  }
  await loadDashboard();
  startAlertRefresh();
});

onBeforeUnmount(() => {
  window.clearInterval(refreshId);
  window.clearTimeout(wateringTimerId);
});
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
          >已确定：`POST /auth/login`、`GET /auth/info`。待定：`POST
          /auth/logout`。手机号注册接口等待后端确认。</span
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
          <p>聚焦单路实时画面，优先呈现视频流、AI 标注、实时告警和事件追溯。</p>
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
                  {{ currentStream.stream_name || "A101 主摄像头" }}
                </span>
                <span class="video-chip danger">
                  <span class="status-dot red"></span>
                  {{ videoError ? "演示画面" : "高风险" }}
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
                <div class="heat-point h1"></div>
                <div class="heat-point h2"></div>
                <div class="person-box p1"><span>张同学 96%</span></div>
                <div class="person-box p2"><span>低头 6.2s</span></div>
                <div v-if="hasConfirmedForbiddenZone" class="person-box p3">
                  <span>手机违规</span>
                </div>
                <div class="person-box p4"><span>陌生人</span></div>
              </template>

              <div v-if="showAiAnnotations" class="insight-strip">
                <article>
                  <span>AI 研判</span>
                  <b>{{ activeSummary.title || "当前风险指数中高" }}</b>
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
                <el-table-column prop="occurred_at" label="时间" width="160" />
                <el-table-column
                  prop="alert_type"
                  label="类型"
                  min-width="110"
                />
                <el-table-column
                  prop="stream_id"
                  label="视频源"
                  min-width="100"
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
                    <el-tag
                      :type="statusType(row.alert_status)"
                      effect="plain"
                      >{{
                        ALERT_STATUS_MAP[row.alert_status]?.label ||
                        row.alert_status
                      }}</el-tag
                    >
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
                  :style="{ '--score': `${activeSummary.risk_score || 58}%` }"
                >
                  {{ activeSummary.risk_score || 58 }}
                </div>
                <div>
                  <b>{{ activeSummary.title || "当前风险指数中高" }}</b>
                  <p>
                    {{
                      activeSummary.summary ||
                      "当前画面风险可控，系统持续监测异常行为。"
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
                  <b>{{ alert.alert_type }}</b>
                  <el-tag :type="statusType(alert.alert_status)" size="small">{{
                    ALERT_STATUS_MAP[alert.alert_status]?.label ||
                    alert.alert_status
                  }}</el-tag>
                </div>
                <p>
                  {{ alert.stream_id }} 置信度 {{ alert.confidence }}，{{
                    alert.occurred_at
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
                  <b>{{ rule.name }}</b>
                  <span
                    >{{ ruleSummary(rule) }}，阈值
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

          <button
            class="monitor-planter"
            :class="[
              `growth-${planterWaterLevel}`,
              { watering: isWateringPlanter },
            ]"
            type="button"
            title="点击给植物浇水"
            @click="waterPlanter"
          >
            <span class="water-drop drop-a"></span>
            <span class="water-drop drop-b"></span>
            <span class="water-drop drop-c"></span>
            <span class="plant-leaf leaf-a"></span>
            <span class="plant-leaf leaf-b"></span>
            <span class="plant-leaf leaf-c"></span>
            <span class="plant-leaf leaf-d"></span>
            <span class="plant-leaf leaf-e"></span>
            <span class="plant-stem stem-a"></span>
            <span class="plant-stem stem-b"></span>
            <span class="plant-pot"></span>
            <span class="plant-saucer"></span>
          </button>
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

        <div class="module-board">
          <section class="panel span-8">
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
                placeholder="搜索类型、位置或视频源"
              />
            </div>
            <el-table :data="filteredAlerts" height="360" class="clean-table">
              <el-table-column prop="occurred_at" label="时间" width="160" />
              <el-table-column prop="alert_type" label="告警类型" width="130" />
              <el-table-column prop="stream_id" label="视频源" width="100" />
              <el-table-column prop="confidence" label="置信度" width="80" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="statusType(row.alert_status)">{{
                    ALERT_STATUS_MAP[row.alert_status]?.label ||
                    row.alert_status
                  }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="证据" width="150">
                <template #default="{ row }">
                  <el-button
                    size="small"
                    text
                    :href="resourceUrl(row.snapshot_url)"
                    >截图</el-button
                  >
                  <el-button
                    size="small"
                    text
                    :href="resourceUrl(row.record_url)"
                    >片段</el-button
                  >
                </template>
              </el-table-column>
            </el-table>
          </section>

          <section class="panel span-4">
            <div class="panel-head compact">
              <h2>处置建议</h2>
            </div>
            <div class="info-list">
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
                  <b>{{ rule.name }}</b>
                  <span>{{ ruleSummary(rule) }}</span>
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
              <h2>A101 区域示意</h2>
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
              <el-button type="primary" :icon="User">新增人员</el-button>
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
                  >对应 `/streams`、`/ai/model/status`、`/system/health`。</span
                >
              </div>
              <el-button :icon="Switch">新增视频源</el-button>
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
                  (modelStatus.models || [])
                    .map((m) => `${m.model_name}@${m.version}`)
                    .join(", ") || "--"
                }}</b>
              </article>
              <article>
                <span>推理耗时</span>
                <b
                  >{{
                    (modelStatus.models || []).find((m) => m.avg_infer_ms)
                      ?.avg_infer_ms || "--"
                  }}
                  ms</b
                >
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
              <div class="heat-point h1"></div>
              <div class="heat-point h2"></div>
              <div class="person-box p1"><span>张同学 96%</span></div>
              <div class="person-box p2"><span>低头 6.2s</span></div>
              <div v-if="hasConfirmedForbiddenZone" class="person-box p3">
                <span>手机违规</span>
              </div>
              <div class="person-box p4"><span>陌生人</span></div>
            </template>
          </div>
        </section>
      </div>
    </teleport>
  </div>
</template>
