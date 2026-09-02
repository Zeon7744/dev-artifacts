"""定时调度 API 测试"""
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _make_workflow(client, headers):
    definition = {
        "nodes": [
            {"id": "t", "type": "trigger", "config": {"trigger_type": "schedule"}},
            {"id": "n", "type": "notify", "config": {"channel": "log", "message": "tick"}},
        ],
        "edges": [{"from": "t", "to": "n"}],
    }
    resp = await client.post(
        "/api/workflows/",
        headers=headers,
        json={"name": "定时工作流", "definition": definition},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def test_set_cron_and_list_jobs(client, auth):
    """POST 设置合法 cron -> jobs 列表包含该任务"""
    headers = auth["headers"]
    wf_id = await _make_workflow(client, headers)

    cron = "*/30 * * * *"
    sched_resp = await client.post(
        f"/api/scheduler/workflows/{wf_id}/schedule",
        headers=headers,
        json={"cron": cron},
    )
    assert sched_resp.status_code == 200, sched_resp.text
    data = sched_resp.json()
    assert data["is_scheduled"] is True
    assert data["cron"] == cron

    jobs_resp = await client.get("/api/scheduler/jobs", headers=headers)
    assert jobs_resp.status_code == 200
    jobs = jobs_resp.json()
    job_ids = [j["id"] for j in jobs]
    assert f"workflow_{wf_id}" in job_ids, f"调度任务未注册: {job_ids}"


async def test_invalid_cron_returns_400(client, auth):
    """非法 cron 表达式返回 400"""
    headers = auth["headers"]
    wf_id = await _make_workflow(client, headers)

    resp = await client.post(
        f"/api/scheduler/workflows/{wf_id}/schedule",
        headers=headers,
        json={"cron": "not a cron expression"},
    )
    assert resp.status_code == 400, resp.text


async def test_schedule_history_endpoint(client, auth):
    """调度历史接口可正常访问（可能为空列表）"""
    resp = await client.get("/api/scheduler/history", headers=auth["headers"])
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
