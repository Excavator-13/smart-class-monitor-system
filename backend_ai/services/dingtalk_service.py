"""钉钉企业机器人 — 发消息 + Stream收回复 + 逐级上报"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any

import requests
from dingtalk_stream import (
    DingTalkStreamClient, Credential, ChatbotHandler,
    ChatbotMessage, CallbackMessage, AckMessage,
)

logger = logging.getLogger(__name__)

# ── 配置 ───────────────────────────────────────────────────

APP_KEY = "dingvd9kkjc0bofwbqhu"
APP_SECRET = "813aXbnZ6zbPM8ryKCma_8qVLzTj1D4kWSkujkjLYavI22xYHv3rhCCuxU-uYdUy"
ROBOT_CODE = "dingvd9kkjc0bofwbqhu"
GROUP_ID = "cid+kYdFkRFkyGbzYUZc/QJCQ=="

PERSONS: dict[str, dict[str, Any]] = {
    "项重善":  {"name": "项重善", "mobile": "18601033435"},
    "章志超":  {"name": "章志超", "mobile": "15270985055"},
}
PRIMARY = "项重善"

PRIMARY = "项重善"      # 第一责任人
RECOGNIZE_KEYWORDS = ["已处理", "误报"]  # 触发停止的关键词

STEP_TIMEOUT = 30  # 秒


# ── Token ──────────────────────────────────────────────────

_token = {"v": "", "exp": 0.0}
_tlock = threading.Lock()

def _get_token() -> str:
    now = time.time()
    with _tlock:
        if _token["v"] and now < _token["exp"] - 60:
            return _token["v"]
    data = requests.post("https://api.dingtalk.com/v1.0/oauth2/accessToken",
                         json={"appKey": APP_KEY, "appSecret": APP_SECRET}, timeout=10).json()
    with _tlock:
        _token["v"] = data["accessToken"]
        _token["exp"] = now + data.get("expireIn", 7200)
    return _token["v"]


# ── 发消息（Webhook — 支持蓝色 @）───────────────────────

WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=ef247487bb8129668aa09a122be9161f056afaf263488d0c9285814654b06618"


def _send(content: str, at_mobiles: list[str] | None = None, at_all: bool = False):
    at_info: dict[str, Any] = {}
    if at_all:
        at_info["isAtAll"] = True
    elif at_mobiles:
        at_info["atMobiles"] = at_mobiles

    body = {"msgtype": "text", "text": {"content": content}, "at": at_info}
    resp = requests.post(WEBHOOK, json=body, timeout=10)
    r = resp.json()
    logger.info("发送: %s → %s", content[:60], "ok" if r.get("errcode") == 0 else r)
    return r


# ── 自动查上级（钉钉组织架构）────────────────────────────

def _find_manager(name: str) -> dict | None:
    """通过钉钉通讯录 API 查直属上级"""
    mobile = PERSONS.get(name, {}).get("mobile", "")
    if not mobile:
        return None
    try:
        token = _get_token()

        # 1. 手机号 → userid (OAPI 格式)
        resp = requests.post(
            f"https://oapi.dingtalk.com/topapi/v2/user/getbymobile?access_token={token}",
            json={"mobile": mobile}, timeout=10,
        ).json()
        uid = resp.get("result", {}).get("userid", "")
        if not uid:
            return None

        # 2. userid → 直属上级
        resp2 = requests.get(
            f"https://oapi.dingtalk.com/topapi/v2/user/get?access_token={token}",
            params={"userid": uid}, timeout=10,
        ).json()
        mgr_id = resp2.get("result", {}).get("manager_userid", "")
        if not mgr_id:
            return None

        # 3. 上级 userid → 姓名
        resp3 = requests.get(
            f"https://oapi.dingtalk.com/topapi/v2/user/get?access_token={token}",
            params={"userid": mgr_id}, timeout=10,
        ).json()
        mgr_name = resp3.get("result", {}).get("name", mgr_id)
        # 从 PERSONS 取手机号（API 不返回）
        mgr_mobile = PERSONS.get(mgr_name, {}).get("mobile", "")
        return {"name": mgr_name, "mobile": mgr_mobile}
    except Exception:
        return None


def _get_chain(start_name: str) -> list[dict]:
    """自动获取上报链：start → 上级 → 上上级 → @所有人"""
    chain = [{"name": start_name, "mobile": PERSONS.get(start_name, {}).get("mobile", "")}]
    current = start_name
    seen = {start_name}
    for _ in range(3):  # 最多查 3 级
        manager = _find_manager(current)
        if not manager:
            break
        m_name = manager.get("name", "")
        if m_name in seen:
            break
        seen.add(m_name)
        chain.append({"name": m_name, "mobile": manager.get("mobile", "")})
        current = m_name
    chain.append({"name": "@全体成员", "mobile": ""})
    return chain


_timers: dict[str, threading.Timer] = {}
_stopped: set[str] = set()


def trigger_alert(msg: str, start: str | None = None):
    c = _get_chain(start or PRIMARY)
    _step(msg, c, 0)


def _step(msg: str, ch: list, idx: int):
    if idx >= len(ch): return
    p = ch[idx]
    last = idx == len(ch) - 1
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    if last:
        content = (
            f"【紧急升级】已逐级上报，无人响应\n\n"
            f"告警内容：{msg}\n"
            f"告警时间：{now}\n"
            f"当前状态：未处理\n"
            f"操作建议：请立即响应\n\n"
            f"@全体成员"
        )
        _send(content, at_all=True)
    elif idx == 0:
        content = (
            f"【告警通知】检测到异常事件\n\n"
            f"告警内容：{msg}\n"
            f"告警时间：{now}\n"
            f"接收人：{p['name']}\n"
            f"操作要求：请在 {STEP_TIMEOUT} 秒内回复「已处理」或「误报」\n"
            f"超时处理：将自动上报至直属上级"
        )
        _send(content, at_mobiles=[p["mobile"]] if p["mobile"] else None)
    else:
        prev = ch[idx - 1]["name"]
        content = (
            f"【告警升级】{prev} 未在规定时间内响应\n\n"
            f"告警内容：{msg}\n"
            f"告警时间：{now}\n"
            f"原始接收人：{ch[0]['name']}\n"
            f"当前接收人：{p['name']}\n"
            f"操作要求：请立即处理，回复「已处理」或「误报」\n"
            f"超时处理：将继续上报"
        )
        _send(content, at_mobiles=[p["mobile"]] if p["mobile"] else None)

    if idx >= len(ch) - 1: return

    key = msg + "-" + str(idx)

    def check():
        if key in _stopped:
            logger.info("已停止上报: %s", msg)
            return
        _step(msg, ch, idx + 1)

    t = threading.Timer(STEP_TIMEOUT, check)
    _timers[key] = t
    t.start()


# ── Stream 收回复 ──────────────────────────────────────────

class AlertHandler(ChatbotHandler):
    async def process(self, raw: CallbackMessage):
        data = raw.data if isinstance(raw.data, dict) else {}
        cid = data.get("conversationId", "")
        if cid != GROUP_ID:
            return AckMessage.STATUS_OK, "ok"

        bot_msg = ChatbotMessage.from_dict(data) if data else None
        text = bot_msg.text.content.strip() if bot_msg and bot_msg.text else ""
        sender = bot_msg.sender_nick if bot_msg else "?"

        logger.info("收到: %s → %s", sender, text)

        if "已处理" in text or "误报" in text:
            _stopped.clear()
            for t in _timers.values():
                t.cancel()
            _timers.clear()
            _send(sender + " 已标记为「" + text + "」，上报链停止")
            logger.info("上报链已停止")

        return AckMessage.STATUS_OK, "ok"


def start_stream():
    def _run():
        cred = Credential(APP_KEY, APP_SECRET)
        client = DingTalkStreamClient(cred)
        client.register_callback_handler("/v1.0/im/bot/messages/get", AlertHandler())
        try:
            asyncio.run(client.start())
        except Exception:
            logger.exception("Stream 退出")

    t = threading.Thread(target=_run, daemon=True, name="dd-stream")
    t.start()
    logger.info("Stream 已启动")
