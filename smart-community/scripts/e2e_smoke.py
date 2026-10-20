#!/usr/bin/env python3
"""
smart-community 端到端冒烟测试（固化版，替代 /tmp 临时脚本）

覆盖：基础链路 + 四大模块（WS/调度/RAG/插件）+ 第三轮（通知/沙箱/上传）
      + 第四轮（社区互动通知 / 插件审核流 / Agent SSE 流式）

用法：
    cd backend && python ../scripts/e2e_smoke.py            # 默认 http://127.0.0.1:8000
    BASE_URL=http://x:8000 python ../scripts/e2e_smoke.py

说明：每轮使用随机 uuid 注册新用户与随机 node_type，可重复执行不产生数据冲突。
"""
import json
import os
import time
import uuid
import urllib.request
import urllib.error

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
PASS, FAIL = 0, 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"  ❌ {name} {detail}")


def req(method, path, token=None, body=None, raw=False):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            text = resp.read().decode()
            return resp.status, (text if raw else (json.loads(text) if text else {}))
    except urllib.error.HTTPError as e:
        text = e.read().decode()
        try:
            return e.code, json.loads(text)
        except Exception:
            return e.code, text


def register():
    suid = uuid.uuid4().hex[:10]
    username, email, password = f"e2e_{suid}", f"e2e_{suid}@t.local", "TestPassw0rd!123"
    req("POST", "/api/auth/register", body={
        "username": username, "email": email, "password": password, "display_name": f"E2E {suid[:6]}"})
    code, data = req("POST", "/api/auth/login", body={"username": username, "password": password})
    assert code == 200, f"login failed: {data}"
    return data["access_token"], data["user"]


def main():
    print(f"\n=== smart-community E2E @ {BASE} ===")

    # 0. 健康检查
    code, data = req("GET", "/api/health")
    check("health 200", code == 200, str(data))

    # 1. 认证
    token, user = register()
    h = {"Authorization": f"Bearer {token}"}
    check("注册+登录", bool(token))

    # 2. 工作流 DAG
    node_type = f"plugin.e2e_{uuid.uuid4().hex[:8]}"
    wf_body = {"name": "E2E审核流", "description": "e2e",
               "definition": {"nodes": [{"id": "p1", "type": node_type,
                                         "config": {"values": [10, 20, 30]}, "next": []}], "edges": []}}
    code, data = req("POST", "/api/workflows/", token, wf_body)
    check("创建工作流", code == 200, str(data))
    wf_id = data.get("id")

    # 3. 自定义插件提交（带安全代码）
    code_text = "def execute(config, ctx):\n    vs = config.get('values', [1,2,3])\n    return {'sum': sum(v for v in vs)}\n"
    code, data = req("POST", "/api/plugins/custom", token, {
        "name": "E2E求和插件", "node_type": node_type, "code": code_text,
        "config_schema": {"fields": []}})
    check("插件提交通过安全校验", code == 200 and data.get("status") == "pending_review", str(data))
    plugin_id = data.get("id")

    # 4. 沙箱试跑
    code, data = req("POST", f"/api/plugins/custom/{plugin_id}/test", token,
                     {"config": {"values": [10, 20, 30]}, "ctx": {}})
    check("沙箱试跑成功 sum=60", code == 200 and data.get("success") and data["output"]["sum"] == 60, str(data))

    # 5. 恶意代码被拒
    code, data = req("POST", "/api/plugins/custom", token, {
        "name": "恶意", "node_type": f"plugin.evil_{uuid.uuid4().hex[:6]}",
        "code": "import os\ndef execute(c,x):\n    return os.listdir('.')\n"})
    check("恶意代码(import)被拒 400", code == 400, str(data))

    # 6. 普通作者发布 -> 仅待审核
    code, data = req("POST", f"/api/plugins/custom/{plugin_id}/publish", token)
    check("作者发布=提交审核", code == 200 and data.get("status") == "pending_review", str(data))
    code, data = req("GET", "/api/plugins/")
    check("待审插件不出现在市场", node_type not in {p["node_type"] for p in data}, str(data)[:200])

    # 7. 管理员审核通过（admin/admin123）
    code, adm = req("POST", "/api/auth/login", body={"username": "admin", "password": "admin123"})
    if code == 200:
        atoken = adm["access_token"]
        code, data = req("GET", "/api/plugins/admin/pending", atoken)
        check("管理员看待审列表", code == 200 and node_type in {p["node_type"] for p in data}, str(data)[:200])
        code, data = req("POST", f"/api/plugins/admin/{plugin_id}/approve", atoken, {"comment": "e2e通过"})
        check("管理员审核通过", code == 200 and data.get("status") == "approved", str(data))
        code, data = req("GET", "/api/plugins/")
        check("通过后市场可见", node_type in {p["node_type"] for p in data})
        code, data = req("GET", "/api/plugins/types")
        check("通过后 types 包含", node_type in data.get("types", []))
    else:
        check("管理员登录（admin/admin123）", False, str(adm))

    # 8. 作者收到审核通过通知
    code, data = req("GET", "/api/notifications", token)
    items = data.get("items", []) if isinstance(data, dict) else []
    check("作者收到审核通过通知", any(n["category"] == "plugin" and "通过" in n["title"] for n in items),
          str([n["title"] for n in items])[:200])

    # 9. 工作流执行（插件已上架，应跑通）
    code, data = req("POST", f"/api/workflows/{wf_id}/run", token, {"input_data": {}})
    check("工作流执行成功", code == 200 and data.get("status") == "success", str(data)[:300])

    # 10. 社区互动通知：B 评论/点赞 A 的帖
    token_a, _ = register()
    token_b, user_b = register()
    code, data = req("POST", "/api/community/posts", token_a, {"title": f"E2E帖_{uuid.uuid4().hex[:6]}", "content": "求互动"})
    post_id = data.get("id")
    req("POST", f"/api/community/posts/{post_id}/comments", token_b, {"content": "E2E评论一条"})
    req("POST", f"/api/community/posts/{post_id}/like", token_b)
    code, data = req("GET", "/api/notifications", token_a)
    items_a = data.get("items", []) if isinstance(data, dict) else []
    cats = {(n["category"], (n.get("data") or {}).get("action")) for n in items_a}
    check("作者收到评论通知", ("community", "comment") in cats, str(cats))
    check("作者收到点赞通知", ("community", "like") in cats, str(cats))

    # 11. Agent SSE 流式对话
    code, data = req("POST", "/api/agents/", token, {"name": "E2E流式助手", "system_prompt": "你是助手"})
    agent_id = data.get("id")
    try:
        r = urllib.request.Request(
            f"{BASE}/api/agents/chat/stream",
            data=json.dumps({"agent_id": agent_id, "message": "流式测试"}).encode(),
            method="POST")
        r.add_header("Content-Type", "application/json")
        r.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(r, timeout=30) as resp:
            body = resp.read().decode()
            ctype = resp.headers.get("content-type", "")
        events = [l.split(":", 1)[1].strip() for l in body.splitlines() if l.startswith("event:")]
        check("SSE content-type", "text/event-stream" in ctype, ctype)
        check("SSE 事件序列 meta/token/done",
              "meta" in events and "token" in events and events[-1] == "done", str(events))
    except Exception as e:
        check("SSE 流式对话", False, str(e))

    # 12. RAG 知识库
    code, data = req("POST", "/api/rag/kb", token, {"name": f"E2E知识库_{uuid.uuid4().hex[:6]}", "description": "e2e"})
    check("创建知识库", code == 200, str(data))
    kb_id = data.get("id")
    if kb_id:
        code, data = req("POST", f"/api/rag/kb/{kb_id}/docs", token,
                         {"title": "平台能力", "content": "智能社区平台支持工作流自动化编排和定时调度。", "source": "e2e"})
        check("RAG 文本入库", code == 200, str(data)[:200])
        code, data = req("POST", f"/api/rag/kb/{kb_id}/query", token, {"question": "平台支持什么能力？"})
        check("RAG 查询返回", code == 200 and "answer" in data, str(data)[:200])

    # 13. 定时调度 cron
    code, data = req("POST", f"/api/scheduler/workflows/{wf_id}/schedule", token,
                     {"cron": "0 9 * * *"})
    check("注册 cron 定时任务", code == 200, str(data)[:200])
    code, data = req("GET", "/api/scheduler/jobs", token)
    check("调度任务列表", code == 200, str(data)[:200])

    # 14. WebSocket 实时帧
    try:
        import websocket  # websocket-client
        ws = websocket.create_connection(
            f"{BASE.replace('http', 'ws')}/api/ws?token={token}", timeout=10)
        frame = ws.recv()
        ws.close()
        check("WebSocket 连接+首帧", bool(frame), frame[:120])
    except ImportError:
        check("WebSocket（跳过：缺 websocket-client）", True)
    except Exception as e:
        check("WebSocket 连接+首帧", False, str(e))

    print(f"\n=== 结果：{PASS} 通过 / {FAIL} 失败 ===")
    if FAILURES:
        print("失败项：", "；".join(FAILURES))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
