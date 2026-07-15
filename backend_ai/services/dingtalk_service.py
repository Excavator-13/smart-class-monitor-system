"""钉钉企业机器人 — 发消息 + Stream收回复 + 逐级上报"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import threading
import time
from datetime import datetime
from typing import Any

import requests
from dingtalk_stream import (
    DingTalkStreamClient, Credential, ChatbotHandler,
    ChatbotMessage, CallbackMessage, AckMessage,
)

logger = logging.getLogger(__name__)

# ── 配置（从环境变量读取）──────────────────────────────────

APP_KEY = os.environ.get("DINGTALK_APP_KEY", "")
APP_SECRET = os.environ.get("DINGTALK_APP_SECRET", "")
ROBOT_CODE = APP_KEY
GROUP_ID = os.environ.get("DINGTALK_GROUP_ID", "")

PERSONS: dict[str, dict[str, Any]] = {
    "项重善":  {"name": "项重善", "mobile": "18601033435"},
    "章志超":  {"name": "章志超", "mobile": "15270985055"},
}
PRIMARY = "项重善"

STEP_TIMEOUT = 45  # 秒


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

WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")


def _upload_image(file_path_or_url: str) -> str:
    """上传图片到钉钉，返回 media_id。支持本地路径和 HTTP URL。"""
    try:
        token = _get_token()
        if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
            resp = requests.get(file_path_or_url, timeout=15)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name
            try:
                with open(tmp_path, "rb") as f:
                    upload_resp = requests.post(
                        f"https://oapi.dingtalk.com/media/upload?access_token={token}&type=image",
                        files={"media": f},
                        timeout=15,
                    )
                return upload_resp.json().get("media_id", "")
            finally:
                os.unlink(tmp_path)
        else:
            with open(file_path_or_url, "rb") as f:
                resp = requests.post(
                    f"https://oapi.dingtalk.com/media/upload?access_token={token}&type=image",
                    files={"media": f},
                    timeout=15,
                )
            return resp.json().get("media_id", "")
    except Exception:
        logger.exception("上传图片失败")
        return ""


def _send_markdown(title: str, text: str, at_mobiles: list[str] | None = None, at_all: bool = False):
    """发送 Markdown 消息（支持图片 media_id）"""
    at_info: dict[str, Any] = {}
    if at_all:
        at_info["isAtAll"] = True
    elif at_mobiles:
        at_info["atMobiles"] = at_mobiles

    body = {"msgtype": "markdown", "markdown": {"title": title, "text": text}, "at": at_info}
    resp = requests.post(WEBHOOK, json=body, timeout=10)
    r = resp.json()
    logger.info("发送Markdown: %s → %s", title, "ok" if r.get("errcode") == 0 else r)
    return r


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

        resp = requests.post(
            f"https://oapi.dingtalk.com/topapi/v2/user/getbymobile?access_token={token}",
            json={"mobile": mobile}, timeout=10,
        ).json()
        uid = resp.get("result", {}).get("userid", "")
        if not uid:
            return None

        resp2 = requests.get(
            f"https://oapi.dingtalk.com/topapi/v2/user/get?access_token={token}",
            params={"userid": uid}, timeout=10,
        ).json()
        mgr_id = resp2.get("result", {}).get("manager_userid", "")
        if not mgr_id:
            return None

        resp3 = requests.get(
            f"https://oapi.dingtalk.com/topapi/v2/user/get?access_token={token}",
            params={"userid": mgr_id}, timeout=10,
        ).json()
        mgr_name = resp3.get("result", {}).get("name", mgr_id)
        mgr_mobile = PERSONS.get(mgr_name, {}).get("mobile", "")
        return {"name": mgr_name, "mobile": mgr_mobile}
    except Exception:
        return None


def _get_chain(start_name: str) -> list[dict]:
    chain = [{"name": start_name, "mobile": PERSONS.get(start_name, {}).get("mobile", "")}]
    current = start_name
    seen = {start_name}
    for _ in range(3):
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
_event_keys: dict[str, str] = {}


def _format_occurred_at(iso_str: str) -> str:
    try:
        return datetime.fromisoformat(iso_str).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return iso_str


def trigger_alert(msg: str, start: str | None = None, snapshot: str = "",
                  event_id: str | None = None, occurred_at: str | None = None):
    if not APP_KEY or not APP_SECRET or not WEBHOOK:
        logger.warning("钉钉配置不完整（APP_KEY/APP_SECRET/WEBHOOK），跳过通知")
        return
    if not event_id:
        event_id = f"evt_{int(time.time())}_{threading.get_ident()}"
    _event_keys[event_id] = msg
    _step(msg, event_id, _get_chain(start or PRIMARY), 0, snapshot, occurred_at=occurred_at)


def _step(msg: str, event_id: str, ch: list, idx: int, snapshot: str = "",
          occurred_at: str | None = None):
    if idx >= len(ch): return
    p = ch[idx]
    last = idx == len(ch) - 1
    alert_time = _format_occurred_at(occurred_at) if occurred_at else time.strftime("%Y-%m-%d %H:%M:%S")
    report_time = time.strftime("%Y-%m-%d %H:%M:%S")

    media_id = _upload_image(snapshot) if snapshot else ""

    if last:
        content = (
            f"【紧急升级】已逐级上报，无人响应\n\n"
            f"告警内容：{msg}\n"
            f"告警时间：{alert_time}\n"
            f"上报时间：{report_time}\n"
            f"当前状态：未处理\n"
            f"操作建议：请立即响应\n\n"
            f"事件ID：{event_id}\n\n"
            f"@全体成员"
        )
        _send(content, at_all=True)
    elif idx == 0:
        text_content = (
            f"【告警通知】检测到异常事件\n\n"
            f"告警内容：{msg}\n"
            f"告警时间：{alert_time}\n"
            f"接收人：{p['name']}\n"
            f"回复「已处理」停止上报\n"
            f"超时处理：将自动上报至直属上级\n\n"
            f"事件ID：{event_id}"
        )
        _send(text_content, at_mobiles=[p["mobile"]] if p["mobile"] else None)
        if media_id:
            md_title = f"告警截图 - {event_id}"
            md_text = f"## 告警截图\n\n事件ID：{event_id}\n\n![截图]({media_id})"
            _send_markdown(md_title, md_text)
    else:
        prev = ch[idx - 1]["name"]
        content = (
            f"【告警升级】{prev} 未在规定时间内响应\n\n"
            f"告警内容：{msg}\n"
            f"告警时间：{alert_time}\n"
            f"上报时间：{report_time}\n"
            f"原始接收人：{ch[0]['name']}\n"
            f"当前接收人：{p['name']}\n"
            f"请立即处理，回复「已处理」停止上报\n\n"
            f"事件ID：{event_id}"
        )
        _send(content, at_mobiles=[p["mobile"]] if p["mobile"] else None)

    if idx >= len(ch) - 1: return

    def check():
        if event_id in _stopped:
            logger.info("已停止上报: %s", msg)
            return
        _step(msg, event_id, ch, idx + 1, occurred_at=occurred_at)

    t = threading.Timer(STEP_TIMEOUT, check)
    _timers[event_id] = t
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
            # 从回复原文中找事件ID
            replied = ""
            try:
                replied = data["text"]["repliedMsg"]["content"]["text"]
            except (KeyError, TypeError):
                pass
            if not replied:
                replied = text

            matched_eid = ""
            for eid in _event_keys:
                if eid in replied:
                    matched_eid = eid
                    break
            if matched_eid and matched_eid in _timers:
                _timers[matched_eid].cancel()
                del _timers[matched_eid]
                _stopped.add(matched_eid)
                _send(f"{sender} 已标记事件 {matched_eid} ，停止上报")
            else:
                _stopped.clear()
                for t in _timers.values():
                    t.cancel()
                _timers.clear()
                _send(f"{sender} 未找到对应事件，已停止全部上报链")
            logger.info("上报链已停止")

        return AckMessage.STATUS_OK, "ok"


def start_stream():
    if not APP_KEY or not APP_SECRET:
        logger.warning("钉钉配置不完整（APP_KEY/APP_SECRET），跳过 Stream 启动")
        return
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