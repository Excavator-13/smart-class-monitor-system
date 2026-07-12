"""Flask 接收 SpringBoot 推送的联系人配置"""

from __future__ import annotations

from flask import Blueprint, request

from backend_ai.services import dingtalk_service as ds
from backend_ai.utils.response import json_response

bp = Blueprint("contacts_sync", __name__)


@bp.post("/api/contacts/sync")
def sync_contacts():
    """接收 SpringBoot 推送的联系人列表"""
    body = request.get_json(silent=True) or {}
    contacts = body.get("contacts", [])
    responsible = body.get("responsible", "")

    # 更新 dingtalk_service 的人员列表
    new_persons = {}
    for c in contacts:
        name = c.get("name", "")
        mobile = c.get("mobile", "")
        if name and mobile:
            new_persons[name] = {"name": name, "mobile": mobile}
    ds.PERSONS.clear()
    ds.PERSONS.update(new_persons)
    if responsible:
        ds.PRIMARY = responsible

    # 更新上报间隔
    interval = body.get("alertInterval")
    if interval:
        ds.STEP_TIMEOUT = int(interval)

    return json_response({"ok": True, "count": len(new_persons)})
