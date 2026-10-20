"""
GitHub 推广器 - Star 请求、Release 通知、Issue/PR 响应、贡献者感谢
"""
import json
from datetime import datetime
from typing import Dict, List, Optional

from base import BaseAPIClient, retry, setup_logger, save_json, load_json

logger = setup_logger("github_promoter")


class GitHubClient(BaseAPIClient):
    """GitHub API 客户端"""

    def __init__(self, config: dict):
        super().__init__("github", config)
        token = config.get("credentials", {}).get("token", "")
        if token:
            self.session.headers.update({
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            })

    @retry(max_retries=3, delay=2.0)
    def get_repo_info(self, owner: str, repo: str) -> dict:
        return self.get(f"{self.api_base}/repos/{owner}/{repo}")

    @retry(max_retries=3, delay=2.0)
    def get_release(self, owner: str, repo: str, release_id: int) -> dict:
        return self.get(f"{self.api_base}/repos/{owner}/{repo}/releases/{release_id}")

    @retry(max_retries=3, delay=2.0)
    def get_latest_release(self, owner: str, repo: str) -> dict:
        return self.get(f"{self.api_base}/repos/{owner}/{repo}/releases/latest")

    @retry(max_retries=3, delay=2.0)
    def get_contributors(self, owner: str, repo: str) -> list:
        return self.get(f"{self.api_base}/repos/{owner}/{repo}/contributors")

    @retry(max_retries=3, delay=2.0)
    def list_issues(self, owner: str, repo: str, state: str = "open") -> list:
        return self.get(f"{self.api_base}/repos/{owner}/{repo}/issues", params={"state": state, "per_page": 30})

    @retry(max_retries=3, delay=2.0)
    def create_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> dict:
        return self.post(f"{self.api_base}/repos/{owner}/{repo}/issues/{issue_number}/comments", json={"body": body})

    @retry(max_retries=3, delay=2.0)
    def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> list:
        return self.get(f"{self.api_base}/repos/{owner}/{repo}/pulls", params={"state": state, "per_page": 30})

    @retry(max_retries=3, delay=2.0)
    def create_star(self, owner: str, repo: str) -> bool:
        """给仓库点 Star"""
        self.put(f"{self.api_base}/user/starred/{owner}/{repo}")
        return True

    @retry(max_retries=3, delay=2.0)
    def create_release(self, owner: str, repo: str, tag: str, name: str, body: str, draft: bool = False) -> dict:
        return self.post(f"{self.api_base}/repos/{owner}/{repo}/releases", json={
            "tag_name": tag, "name": name, "body": body, "draft": draft,
        })


class GitHubPromoter:
    """GitHub 推广管理器"""

    def __init__(self, config: dict):
        self.config = config
        self.client = GitHubClient(config.get("github", {}))
        self.promo_log: list = load_json("github_promo_log.json", [])

    def promote_release(self, repo: str, release_id: int = None) -> dict:
        """
        推广 Release
        repo: 格式 owner/repo
        release_id: 指定 release ID，None 则取 latest
        """
        owner, repo_name = repo.split("/")
        if release_id:
            release = self.client.get_release(owner, repo_name, release_id)
        else:
            release = self.client.get_latest_release(owner, repo_name)

        release_info = {
            "tag": release.get("tag_name", ""),
            "name": release.get("name", ""),
            "body": release.get("body", "")[:500],
            "url": release.get("html_url", ""),
            "published_at": release.get("published_at", ""),
        }

        # 生成推广文案
        promo_content = self._generate_release_promo(owner, repo_name, release_info)

        log_entry = {
            "action": "promote_release",
            "repo": repo,
            "release": release_info,
            "promo_content": promo_content,
            "timestamp": datetime.now().isoformat(),
        }
        self.promo_log.append(log_entry)
        save_json("github_promo_log.json", self.promo_log)
        logger.info(f"Release 推广已生成: {repo} {release_info['tag']}")
        return {"release": release_info, "promo_content": promo_content}

    def request_star(self, repo: str) -> dict:
        """请求 Star 仓库"""
        owner, repo_name = repo.split("/")
        success = self.client.create_star(owner, repo_name)
        return {"repo": repo, "starred": success}

    def thank_contributors(self, repo: str) -> dict:
        """感谢贡献者"""
        owner, repo_name = repo.split("/")
        contributors = self.client.get_contributors(owner, repo_name)
        thanked = []
        for c in contributors[:10]:
            login = c.get("login", "")
            msg = f"@{login} 感谢你对 {repo} 的贡献！🎉"
            thanked.append({"login": login, "message": msg})

        result = {"repo": repo, "contributors_thanked": thanked}
        save_json("contributor_thanks.json", result)
        return result

    def respond_to_issues(self, repo: str, response_template: str = None) -> dict:
        """自动响应 Issue"""
        owner, repo_name = repo.split("/")
        issues = self.client.list_issues(owner, repo_name, state="open")
        template = response_template or "感谢反馈！我们正在查看这个问题，会尽快回复。🙏"
        responses = []
        for issue in issues[:5]:
            num = issue.get("number")
            title = issue.get("title", "")
            # 跳过 PR
            if "pull_request" in issue:
                continue
            try:
                self.client.create_issue_comment(owner, repo_name, num, template)
                responses.append({"issue": num, "title": title, "status": "responded"})
            except Exception as e:
                responses.append({"issue": num, "title": title, "status": "error", "error": str(e)})
        return {"repo": repo, "responses": responses}

    def _generate_release_promo(self, owner: str, repo: str, release: dict) -> dict:
        """生成多平台推广文案"""
        tag = release["tag"]
        name = release["name"]
        url = release["url"]
        desc = release["body"][:200]

        return {
            "twitter": f"🚀 {name} ({tag}) 已发布！\n\n{desc}\n\n{url}\n\n#GitHub #OpenSource #{repo}",
            "weibo": f"🎉 {repo} 新版本 {tag} 发布！\n\n{desc}\n\n详情: {url}\n#开源# #GitHub#",
            "juejin": f"# {name} {tag} 发布\n\n{desc}\n\n[查看详情]({url})",
            "zhihu": f"我们的开源项目 {repo} 发布了新版本 {name}（{tag}）。\n\n{desc}\n\n项目地址：{url}",
        }

    def get_promo_history(self) -> list:
        return self.promo_log


if __name__ == "__main__":
    from config import load_config
    cfg = load_config()
    promoter = GitHubPromoter(cfg)
    print("GitHub 推广器就绪。调用 promote_release(repo, release_id) 推广。")
