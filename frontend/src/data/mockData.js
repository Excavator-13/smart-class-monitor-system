export const mockStreams = [
  {
    stream_id: "A101",
    stream_name: "A101 主摄像头",
    location: "教学楼一层 A101",
    status: "online",
    latency: "1.8s",
    rtmp_url: "rtmp://media-server/live/a101",
    remark: "默认演示视频源"
  },
  {
    stream_id: "B203",
    stream_name: "B203 后排摄像头",
    location: "教学楼二层 B203",
    status: "online",
    latency: "2.4s",
    rtmp_url: "rtmp://media-server/live/b203",
    remark: "用于多路扩展"
  },
  {
    stream_id: "C305",
    stream_name: "C305 门口摄像头",
    location: "教学楼三层 C305",
    status: "offline",
    latency: "--",
    rtmp_url: "rtmp://media-server/live/c305",
    remark: "等待推流"
  }
];

export const mockAlerts = [
  {
    id: 1001,
    time: "10:28:19",
    alert_type: "明火检测",
    level: "critical",
    status: "未处理",
    stream_id: "A101",
    location: "后排右侧",
    description: "连续 3 帧置信度达标，已保留截图与片段。",
    snapshot_path: "/alerts/a101/1001/snapshot.jpg",
    video_path: "/alerts/a101/1001/record.flv"
  },
  {
    id: 1002,
    time: "10:22:41",
    alert_type: "手机违规",
    level: "high",
    status: "待确认",
    stream_id: "A101",
    location: "第三排右侧",
    description: "禁用区域内持续 5 秒，目标框已追踪。",
    snapshot_path: "/alerts/a101/1002/snapshot.jpg",
    video_path: "/alerts/a101/1002/record.flv"
  },
  {
    id: 1003,
    time: "09:58:07",
    alert_type: "陌生人",
    level: "medium",
    status: "已处理",
    stream_id: "A101",
    location: "教室门口",
    description: "人脸识别失败，已生成身份核验记录。",
    snapshot_path: "/alerts/a101/1003/snapshot.jpg",
    video_path: "/alerts/a101/1003/record.flv"
  },
  {
    id: 1004,
    time: "09:34:12",
    alert_type: "低头异常",
    level: "low",
    status: "误报",
    stream_id: "A101",
    location: "第二排中部",
    description: "管理员标记为误报，保留追溯记录。",
    snapshot_path: "/alerts/a101/1004/snapshot.jpg",
    video_path: "/alerts/a101/1004/record.flv"
  }
];

export const mockRules = [
  {
    id: 1,
    rule_type: "phone",
    name: "手机违规",
    enabled: true,
    threshold_seconds: 5,
    summary: "仅在禁用手机区域生效"
  },
  {
    id: 2,
    rule_type: "fire",
    name: "明火检测",
    enabled: true,
    threshold_seconds: 3,
    summary: "最高优先级，连续帧触发"
  },
  {
    id: 3,
    rule_type: "fall",
    name: "摔倒检测",
    enabled: true,
    threshold_seconds: 4,
    summary: "倒地持续确认后告警"
  },
  {
    id: 4,
    rule_type: "head_down",
    name: "低头 / 离座",
    enabled: true,
    threshold_seconds: 6,
    summary: "结合座位区域和时间窗口判断"
  }
];

export const mockStudents = [
  { id: 1, student_no: "2026001", name: "张同学", class_name: "高一 1 班", face_registered: true, last_seen: "10:28" },
  { id: 2, student_no: "2026002", name: "李同学", class_name: "高一 1 班", face_registered: true, last_seen: "10:24" },
  { id: 3, student_no: "VISITOR", name: "陌生人记录", class_name: "待核验", face_registered: false, last_seen: "09:58" }
];

export const mockHealth = {
  rtmp: "online",
  ai: "online",
  api: "online",
  database: "online"
};

export const mockSummary = {
  risk_score: 58,
  title: "当前风险指数中高",
  summary: "手机违规和低头行为在同一区域叠加出现，建议教师优先查看第三排右侧。",
  actions: ["自动抓拍", "等待人工确认", "保留追踪记录"],
  timeline: [
    { time: "10:22", text: "检测到手机目标进入禁用区域" },
    { time: "10:23", text: "持续低头超过阈值，触发候选事件" },
    { time: "10:24", text: "自动抓拍，等待人工确认" }
  ]
};
