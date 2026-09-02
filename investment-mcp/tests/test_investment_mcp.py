"""
investment-mcp 测试套件
覆盖核心MCP协议、工具列表、工具调用等
"""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


class TestMCPServerInfo(unittest.TestCase):
    """服务器信息测试"""

    def test_server_info(self):
        from server_core import SERVER_INFO
        self.assertEqual(SERVER_INFO["name"], "investment-mcp")
        self.assertIn("version", SERVER_INFO)
        self.assertEqual(SERVER_INFO["version"], "1.0.0")

    def test_protocol_version(self):
        from server_core import MCP_PROTOCOL_VERSION
        self.assertEqual(MCP_PROTOCOL_VERSION, "2026-07-28")


class TestToolsDefinition(unittest.TestCase):
    """工具定义测试"""

    def test_tools_exist(self):
        from server_core import TOOLS_DEFINITION
        self.assertIsInstance(TOOLS_DEFINITION, list)
        self.assertGreater(len(TOOLS_DEFINITION), 0)

    def test_tools_have_required_fields(self):
        from server_core import TOOLS_DEFINITION
        for tool in TOOLS_DEFINITION:
            self.assertIn("name", tool)
            self.assertIn("description", tool)

    def test_expected_tools(self):
        from server_core import TOOLS_DEFINITION
        tool_names = [t["name"] for t in TOOLS_DEFINITION]
        expected = ["predict_crypto", "detect_regime", "analyze_commodity",
                    "analyze_fund", "run_backtest", "list_tools"]
        for name in expected:
            self.assertIn(name, tool_names, f"工具 {name} 缺失")


class TestMCPHandlers(unittest.TestCase):
    """MCP协议处理器测试"""

    def test_discover(self):
        from server_core import handle_mcp_discover
        result = handle_mcp_discover()
        self.assertEqual(result["jsonrpc"], "2.0")
        self.assertIn("result", result)
        self.assertIn("serverInfo", result["result"])
        self.assertIn("capabilities", result["result"])

    def test_tools_list(self):
        from server_core import handle_tools_list
        result = handle_tools_list()
        self.assertEqual(result["jsonrpc"], "2.0")
        self.assertIn("tools", result["result"])
        self.assertGreater(len(result["result"]["tools"]), 0)

    def test_tools_call_list(self):
        from server_core import handle_tools_call
        result = handle_tools_call("list_tools", {})
        self.assertIn("content", result)
        self.assertFalse(result.get("isError", False))

    def test_tools_call_unknown(self):
        from server_core import handle_tools_call
        result = handle_tools_call("nonexistent_tool", {})
        self.assertTrue(result.get("isError", False))

    def test_mcp_request_discover(self):
        from server_core import handle_mcp_request
        request = {"jsonrpc": "2.0", "method": "server/discover", "id": 1}
        result = handle_mcp_request(request)
        self.assertEqual(result["jsonrpc"], "2.0")
        self.assertEqual(result["id"], 1)

    def test_mcp_request_tools_list(self):
        from server_core import handle_mcp_request
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 2}
        result = handle_mcp_request(request)
        self.assertEqual(result["jsonrpc"], "2.0")

    def test_mcp_request_tools_call(self):
        from server_core import handle_mcp_request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 3,
            "params": {"name": "list_tools", "arguments": {}}
        }
        result = handle_mcp_request(request)
        self.assertEqual(result["jsonrpc"], "2.0")

    def test_mcp_request_unknown_method(self):
        from server_core import handle_mcp_request
        request = {"jsonrpc": "2.0", "method": "unknown/method", "id": 4}
        result = handle_mcp_request(request)
        self.assertIn("error", result)


class TestCryptoHandler(unittest.TestCase):
    """加密货币预测处理器测试"""

    def test_predict_crypto_default(self):
        from server_core import handle_tools_call
        result = handle_tools_call("predict_crypto", {})
        self.assertIn("content", result)
        self.assertFalse(result.get("isError", False))


class TestCommodityHandler(unittest.TestCase):
    """大宗商品分析处理器测试"""

    def test_analyze_commodity_default(self):
        from server_core import handle_tools_call
        result = handle_tools_call("analyze_commodity", {})
        self.assertIn("content", result)
        self.assertFalse(result.get("isError", False))


class TestFundHandler(unittest.TestCase):
    """基金分析处理器测试"""

    def test_analyze_fund_default(self):
        from server_core import handle_tools_call
        result = handle_tools_call("analyze_fund", {})
        self.assertIn("content", result)
        self.assertFalse(result.get("isError", False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
