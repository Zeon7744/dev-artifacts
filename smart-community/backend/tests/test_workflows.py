"""工作流 DAG 端到端测试：创建 -> 运行 -> success"""
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

# 简单 DAG 定义：手动触发器 -> 数据库模拟动作 -> 通知(log) 节点
# 全部节点离线可执行（无 HTTP 外呼、无 LLM 依赖）
SIMPLE_DAG_DEFINITION = {
    "nodes": [
        {
            "id": "trigger_1",
            "type": "trigger",
            "name": "手动触发",
            "config": {"trigger_type": "manual"},
        },
        {
            "id": "action_1",
            "type": "action",
            "name": "数据库模拟操作",
            "config": {"action_type": "database", "query": "SELECT 1"},
        },
        {
            "id": "notify_1",
            "type": "notify",
            "name": "日志通知",
            "config": {"channel": "log", "message": "工作流执行完成"},
        },
    ],
    "edges": [
        {"from": "trigger_1", "to": "action_1"},
        {"from": "action_1", "to": "notify_1"},
    ],
}


async def _create_workflow(client, headers):
    resp = await client.post(
        "/api/workflows/",
        headers=headers,
        json={
            "name": "测试简单DAG",
            "description": "trigger->action->notify",
            "definition": SIMPLE_DAG_DEFINITION,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "created"
    return data["id"]


async def test_workflow_create_and_run_success(client, auth):
    """创建一个 trigger->action->notify 的 DAG，运行后状态为 success"""
    headers = auth["headers"]
    wf_id = await _create_workflow(client, headers)

    # 运行工作流
    run_resp = await client.post(
        f"/api/workflows/{wf_id}/run",
        headers=headers,
        json={"input_data": {"msg": "hello"}},
    )
    assert run_resp.status_code == 200, run_resp.text
    run_data = run_resp.json()
    assert run_data["status"] == "success", f"工作流未成功: {run_data}"
    # 三个节点均应出现在 node_results
    node_ids = {nr["node_id"] for nr in run_data["node_results"]}
    assert {"trigger_1", "action_1", "notify_1"} <= node_ids
    assert all(nr["status"] == "success" for nr in run_data["node_results"])


async def test_workflow_appears_in_list(client, auth):
    """创建后可在工作流列表中看到，且运行计数更新"""
    headers = auth["headers"]
    wf_id = await _create_workflow(client, headers)
    await client.post(
        f"/api/workflows/{wf_id}/run",
        headers=headers,
        json={},
    )

    list_resp = await client.get("/api/workflows/", headers=headers)
    assert list_resp.status_code == 200
    workflows = list_resp.json()
    mine = [w for w in workflows if w["id"] == wf_id]
    assert mine, "新创建的工作流未出现在列表中"
    assert mine[0]["run_count"] >= 1


async def test_workflow_404_for_other_user(client, auth):
    """其他用户不能运行不属于自己的工作流"""
    headers = auth["headers"]
    wf_id = await _create_workflow(client, headers)

    # 另一个用户
    from tests.conftest import register_and_login
    other = await register_and_login(client, prefix="wf_other")
    run_resp = await client.post(
        f"/api/workflows/{wf_id}/run",
        headers=other["headers"],
        json={},
    )
    assert run_resp.status_code == 404, run_resp.text
