"""
定时发布器 - 内容日历、最佳时间建议、自动发布
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from base import setup_logger, save_json, load_json

logger = setup_logger("post_scheduler")

# 各平台最佳发布时间（基于通用运营经验）
BEST_POSTING_TIMES = {
    "juejin": {"weekday": ["08:00", "12:00", "20:00"], "weekend": ["10:00", "14:00", "21:00"]},
    "zhihu": {"weekday": ["07:30", "12:00", "21:00"], "weekend": ["09:00", "15:00", "22:00"]},
    "weibo": {"weekday": ["08:00", "12:00", "18:00", "22:00"], "weekend": ["10:00", "14:00", "20:00", "23:00"]},
    "twitter": {"weekday": ["08:00", "12:00", "17:00", "21:00"], "weekend": ["09:00", "13:00", "19:00"]},
}


class PostScheduler:
    """定时发布管理器"""

    def __init__(self):
        self.calendar: list = load_json("content_calendar.json", [])
        self.history: list = load_json("schedule_history.json", [])

    def schedule_post(self, content: dict, platform: str, time: str) -> dict:
        """
        安排定时发布
        content: 内容字典
        platform: 平台名
        time: ISO 格式时间字符串
        """
        entry = {
            "id": f"sched_{len(self.calendar) + 1}",
            "content": content,
            "platform": platform,
            "scheduled_time": time,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        self.calendar.append(entry)
        save_json("content_calendar.json", self.calendar)
        logger.info(f"已排期 [{platform}] @ {time}: {content.get('title', content.get('body', '')[:30])}")
        return entry

    def suggest_best_time(self, platform: str, days_ahead: int = 7) -> list:
        """建议最佳发布时间"""
        times = BEST_POSTING_TIMES.get(platform)
        if not times:
            return [{"message": f"无 {platform} 的时间建议数据"}]

        suggestions = []
        now = datetime.now()
        for d in range(days_ahead):
            date = now + timedelta(days=d)
            day_type = "weekend" if date.weekday() >= 5 else "weekday"
            for t in times.get(day_type, []):
                dt = datetime.strptime(f"{date.strftime('%Y-%m-%d')} {t}", "%Y-%m-%d %H:%M")
                if dt > now:
                    suggestions.append({
                        "datetime": dt.isoformat(),
                        "weekday": date.strftime("%A"),
                        "day_type": day_type,
                        "time": t,
                    })
        return suggestions[:10]

    def get_calendar(self, days_ahead: int = 30) -> list:
        """获取内容日历"""
        cutoff = (datetime.now() + timedelta(days=days_ahead)).isoformat()
        return [e for e in self.calendar if e["scheduled_time"] <= cutoff and e["status"] == "pending"]

    def get_due_posts(self) -> list:
        """获取所有到期应发布的内容"""
        now = datetime.now().isoformat()
        return [e for e in self.calendar if e["status"] == "pending" and e["scheduled_time"] <= now]

    def mark_published(self, entry_id: str) -> dict:
        """标记已发布"""
        for e in self.calendar:
            if e["id"] == entry_id:
                e["status"] = "published"
                e["published_at"] = datetime.now().isoformat()
                self.history.append(e)
                save_json("content_calendar.json", self.calendar)
                save_json("schedule_history.json", self.history)
                return e
        raise ValueError(f"未找到排期: {entry_id}")

    def cancel_schedule(self, entry_id: str) -> dict:
        """取消排期"""
        for e in self.calendar:
            if e["id"] == entry_id:
                e["status"] = "cancelled"
                save_json("content_calendar.json", self.calendar)
                return e
        raise ValueError(f"未找到排期: {entry_id}")

    def remove_completed(self):
        """清理已完成条目"""
        self.calendar = [e for e in self.calendar if e["status"] == "pending"]
        save_json("content_calendar.json", self.calendar)


if __name__ == "__main__":
    ps = PostScheduler()
    print("定时发布器就绪。调用 schedule_post(content, platform, time) 排期。")
    print("建议时间:", json.dumps(ps.suggest_best_time("weibo", 3), ensure_ascii=False, indent=2))
