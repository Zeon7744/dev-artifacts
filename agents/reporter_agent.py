"""
报告 Agent - 格式化输出和报告生成
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import json

from .base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)


class ReporterAgent(BaseAgent):
    """
    报告 Agent
    
    职责：
    - 格式化输出
    - 生成多种格式报告
    - 报告模板管理
    - 导出功能
    """
    
    FORMATS = ["markdown", "json", "html", "csv"]
    
    def __init__(self, **kwargs):
        super().__init__(
            name="ReporterAgent",
            description="报告格式化工具专家",
            **kwargs
        )
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行报告生成
        
        Args:
            input_data: {
                "format": "markdown" | "json" | "html" | "csv",
                "content": {...},  # 原始数据
                "template": "daily" | "weekly" | "custom",
                "title": "报告标题"
            }
        """
        self._log_event("start", input_data)
        
        fmt = input_data.get("format", "markdown")
        content = input_data.get("content", {})
        template = input_data.get("template", "daily")
        title = input_data.get("title", f"财经报告 - {datetime.now().strftime('%Y-%m-%d')}")
        
        # 生成报告
        report = self._generate_report(content, template, title)
        
        # 格式化输出
        if fmt == "markdown":
            output = self._format_markdown(report)
        elif fmt == "json":
            output = json.dumps(report, ensure_ascii=False, indent=2)
        elif fmt == "html":
            output = self._format_html(report)
        elif fmt == "csv":
            output = self._format_csv(content)
        else:
            output = str(report)
        
        result = {
            "format": fmt,
            "title": title,
            "generated_at": datetime.now().isoformat(),
            "content": output,
            "size_bytes": len(output.encode('utf-8'))
        }
        
        self._log_event("complete", {"format": fmt, "size": len(output)})
        
        return result
    
    def _generate_report(
        self, 
        content: Dict, 
        template: str,
        title: str
    ) -> Dict:
        """根据模板生成报告结构"""
        report = {
            "title": title,
            "generated_at": datetime.now().isoformat(),
            "template": template,
            "sections": []
        }
        
        if template == "daily":
            report["sections"] = [
                {"name": "市场概览", "data": content.get("market_overview", "")},
                {"name": "热门事件", "data": content.get("hot_events", [])},
                {"name": "情绪分析", "data": content.get("sentiment", {})},
                {"name": "资产趋势", "data": content.get("trends", {})},
                {"name": "操作建议", "data": content.get("advice", "")}
            ]
        elif template == "weekly":
            report["sections"] = [
                {"name": "周度总结", "data": content.get("weekly_summary", "")},
                {"name": "周涨跌榜", "data": content.get("weekly_changes", [])},
                {"name": "下周展望", "data": content.get("outlook", "")}
            ]
        else:
            # 自定义模板
            for section in content.get("sections", []):
                report["sections"].append(section)
        
        return report
    
    def _format_markdown(self, report: Dict) -> str:
        """Markdown 格式"""
        lines = [
            f"# {report['title']}",
            f"\n*生成时间: {report['generated_at']}*\n",
            "---\n"
        ]
        
        for section in report["sections"]:
            lines.append(f"\n## {section['name']}\n")
            
            data = section["data"]
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        lines.append(f"**{key}:**")
                        for k, v in value.items():
                            lines.append(f"- {k}: {v}")
                    else:
                        lines.append(f"- **{key}:** {value}")
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        lines.append(f"- {item.get('name', item.get('keyword', str(item)))}")
                    else:
                        lines.append(f"- {item}")
            else:
                lines.append(str(data))
            
            lines.append("")
        
        lines.append("\n---\n*本报告由金融新闻MCP自动生成*")
        
        return "\n".join(lines)
    
    def _format_html(self, report: Dict) -> str:
        """HTML 格式"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='zh-CN'>",
            "<head>",
            "  <meta charset='UTF-8'>",
            "  <title>{title}</title>",
            "  <style>",
            "    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}",
            "    h1 {{ color: #1a1a1a; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; }}",
            "    h2 {{ color: #333; margin-top: 30px; }}",
            "    .meta {{ color: #666; font-size: 14px; }}",
            "    .section {{ background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 10px 0; }}",
            "    .tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; }}",
            "    .positive {{ background: #d4edda; color: #155724; }}",
            "    .negative {{ background: #f8d7da; color: #721c24; }}",
            "    .neutral {{ background: #fff3cd; color: #856404; }}",
            "    table {{ width: 100%; border-collapse: collapse; }}",
            "    th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}",
            "    th {{ background: #f5f5f5; }}",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{report['title']}</h1>",
            f"  <p class='meta'>生成时间: {report['generated_at']}</p>",
        ]
        
        for section in report["sections"]:
            html_parts.append(f"  <div class='section'>")
            html_parts.append(f"    <h2>{section['name']}</h2>")
            
            data = section["data"]
            if isinstance(data, dict):
                html_parts.append("    <table>")
                for key, value in data.items():
                    if isinstance(value, dict):
                        html_parts.append(f"      <tr><th>{key}</th><td></td></tr>")
                        for k, v in value.items():
                            css_class = "positive" if isinstance(v, (int, float)) and v > 0 else "negative" if v < 0 else "neutral"
                            html_parts.append(f"      <tr><td>{k}</td><td><span class='tag {css_class}'>{v}</span></td></tr>")
                    else:
                        css_class = "positive" if isinstance(value, (int, float)) and value > 0 else "negative" if isinstance(value, (int, float)) and value < 0 else "neutral"
                        html_parts.append(f"      <tr><th>{key}</th><td><span class='tag {css_class}'>{value}</span></td></tr>")
                html_parts.append("    </table>")
            elif isinstance(data, list):
                html_parts.append("    <ul>")
                for item in data:
                    if isinstance(item, dict):
                        html_parts.append(f"      <li>{item.get('name', item.get('keyword', str(item)))}</li>")
                    else:
                        html_parts.append(f"      <li>{item}</li>")
                html_parts.append("    </ul>")
            else:
                html_parts.append(f"    <p>{data}</p>")
            
            html_parts.append("  </div>")
        
        html_parts.extend([
            "  <hr>",
            "  <p class='meta'>本报告由金融新闻MCP自动生成</p>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)
    
    def _format_csv(self, content: Dict) -> str:
        """CSV 格式"""
        import csv
        import io
        
        output = io.StringIO()
        
        # 提取可表格化的数据
        writer = csv.writer(output)
        writer.writerow(["类别", "名称", "数值", "状态", "时间"])
        
        if "trends" in content:
            for symbol, data in content["trends"].items():
                writer.writerow([
                    "趋势",
                    data.get("name", symbol),
                    data.get("direction", ""),
                    "上涨" if data.get("direction") == "up" else "下跌" if data.get("direction") == "down" else "震荡",
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ])
        
        if "sentiment" in content:
            writer.writerow([
                "情绪",
                "市场情绪指数",
                content["sentiment"].get("average_score", ""),
                content["sentiment"].get("label", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ])
        
        return output.getvalue()
