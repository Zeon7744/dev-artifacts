#!/usr/bin/env python3
"""
二次作业知识图谱增强构建器
从规则、术语和实体中构建领域知识图谱
"""

import json
import re
import networkx as nx
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import collections

# 设备类型关键词
EQUIPMENT_KEYWORDS = {
    '主变保护', '线路保护', '母差保护', '备自投', '安稳装置',
    '测控装置', '智能终端', '过程层交换机', '保护装置',
    '电流互感器', '电压互感器', 'CT', 'PT',
    '压板', '硬压板', '软压板', '跳闸压板', '失灵压板',
    '空开', '熔断器', '端子', '端子排',
    '光纤', '光缆', '尾纤',
    '继电保护', '安全自动装置',
}

# 动作类型映射
ACTION_TYPE_MAP = {
    '取下': 'remove_fuse',
    '装上': 'install_fuse',
    '断开': 'open_air_switch',
    '合上': 'close_air_switch',
    '投入': 'input_pressure_plate',
    '退出': 'output_pressure_plate',
    '打开': 'open_terminal',
    '连上': 'connect_terminal',
    '拔出': 'pull_out_fiber',
    '插入': 'insert_fiber',
    '切换至': 'switch_handle',
    '拆除': 'remove_wire',
    '接入': 'connect_wire',
    '密封': 'seal',
}

# 节点类型定义
NODE_TYPES = {
    'equipment': {'label': '设备', 'color': '#3498db'},
    'component': {'label': '部件', 'color': '#2ecc71'},
    'action': {'label': '操作', 'color': '#e74c3c'},
    'rule': {'label': '规则', 'color': '#f39c12'},
    'risk': {'label': '风险', 'color': '#9b59b6'},
    'voltage_level': {'label': '电压等级', 'color': '#1abc9c'},
    'location': {'label': '地点', 'color': '#e67e22'},
    'document': {'label': '文档', 'color': '#95a5a6'},
}


@dataclass
class KGNode:
    """知识图谱节点"""
    node_id: str
    node_type: str
    label: str
    properties: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            'id': self.node_id,
            'type': self.node_type,
            'label': self.label,
            'properties': self.properties
        }


@dataclass
class KGEdge:
    """知识图谱边"""
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            'source': self.source_id,
            'target': self.target_id,
            'relation': self.relation_type,
            'properties': self.properties
        }


class EnhancedKnowledgeGraph:
    """增强版二次作业知识图谱构建器"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: List[KGNode] = []
        self.edges: List[KGEdge] = []
        self.entity_map: Dict[str, str] = {}
        
    def build_from_knowledge(self, knowledge_data: Dict[str, Any]) -> 'EnhancedKnowledgeGraph':
        """从知识抽取结果构建图谱"""
        
        # 1. 添加文档根节点
        self._add_document_root()
        
        # 2. 处理规则
        self._process_rules(knowledge_data.get('rules', []))
        
        # 3. 处理术语
        self._process_terms(knowledge_data.get('terms', []))
        
        # 4. 建立动作-设备关系
        self._build_action_equipment_relations()
        
        # 5. 建立设备层级关系
        self._build_equipment_hierarchy()
        
        return self
    
    def _add_document_root(self):
        """添加文档根节点"""
        self._add_node(KGNode(
            node_id="doc_root",
            node_type='document',
            label='二次作业标准体系',
            properties={'source': '实施细则2025版'}
        ))
    
    def _process_rules(self, rules: List[Dict]):
        """处理规则，提取实体和关系"""
        rule_counter = 0
        
        for rule in rules:
            rule_counter += 1
            rule_id = f"rule_{rule_counter:04d}"
            content = rule.get('content', '')
            
            # 添加规则节点
            self._add_node(KGNode(
                node_id=rule_id,
                node_type='rule',
                label=content[:40] + '...' if len(content) > 40 else content,
                properties={
                    'rule_type': rule.get('rule_type', 'unknown'),
                    'full_content': content,
                    'context': rule.get('context', '')
                }
            ))
            self._add_edge("doc_root", rule_id, 'stipulates', {})
            
            # 提取设备实体
            equipment_found = self._extract_equipment(content)
            for equip in equipment_found:
                equip_id = f"equip_{equip}"
                if equip_id not in self.entity_map:
                    self._add_node(KGNode(
                        node_id=equip_id,
                        node_type='equipment',
                        label=equip,
                        properties={}
                    ))
                self._add_edge(rule_id, equip_id, 'applies_to', {})
            
            # 提取动作实体
            action_found = self._extract_action(content)
            if action_found:
                action_id = f"action_{action_found}"
                if action_id not in self.entity_map:
                    self._add_node(KGNode(
                        node_id=action_id,
                        node_type='action',
                        label=f"{action_found}操作",
                        properties={'action_type': action_found}
                    ))
                self._add_edge(rule_id, action_id, 'requires', {})
            
            # 提取电压等级
            voltages = re.findall(r'(\d+kV)', content)
            for v in set(voltages):
                volt_id = f"voltage_{v}"
                if volt_id not in self.entity_map:
                    self._add_node(KGNode(
                        node_id=volt_id,
                        node_type='voltage_level',
                        label=v,
                        properties={}
                    ))
                self._add_edge(rule_id, volt_id, 'applies_to', {})
        
        print(f"  - 处理了 {rule_counter} 条规则")
    
    def _process_terms(self, terms: List[Dict]):
        """处理术语定义"""
        term_counter = 0
        for term in terms:
            term_counter += 1
            term_id = f"term_{term_counter:04d}"
            
            self._add_node(KGNode(
                node_id=term_id,
                node_type='equipment',
                label=term.get('name', ''),
                properties={
                    'definition': term.get('definition', ''),
                    'tags': term.get('tags', [])
                }
            ))
            self._add_edge("doc_root", term_id, 'defines', {})
    
    def _extract_equipment(self, text: str) -> List[str]:
        """从文本中提取设备实体"""
        found = []
        for keyword in EQUIPMENT_KEYWORDS:
            if keyword in text:
                found.append(keyword)
        return found
    
    def _extract_action(self, text: str) -> str:
        """从文本中提取主要动作"""
        for verb in ACTION_TYPE_MAP.keys():
            if verb in text:
                return verb
        return ''
    
    def _build_action_equipment_relations(self):
        """建立动作与设备的关联关系"""
        action_nodes = [n for n in self.nodes if n.node_type == 'action']
        equip_nodes = [n for n in self.nodes if n.node_type == 'equipment']
        
        # 基于动作类型建立通用关联
        action_equip_map = {
            '取下': ['压板', '空开', '熔断器'],
            '装上': ['压板', '空开', '熔断器'],
            '断开': ['空开', '端子', '回路'],
            '合上': ['空开', '回路'],
            '投入': ['压板', '保护'],
            '退出': ['压板', '保护'],
            '打开': ['端子', '接点'],
            '连上': ['端子', '接点'],
            '拔出': ['光纤', '尾纤'],
            '插入': ['光纤', '尾纤'],
            '切换至': ['把手', '切换开关'],
            '拆除': ['线', '电缆'],
            '接入': ['线', '电缆'],
            '密封': ['端子', '接口'],
        }
        
        for action_node in action_nodes:
            action_type = action_node.properties.get('action_type', '')
            if action_type in action_equip_map:
                related_equip = action_equip_map[action_type]
                for equip in equip_nodes:
                    for keyword in related_equip:
                        if keyword in equip.label:
                            self._add_edge(action_node.node_id, equip.node_id, 'related_to', {'weight': 0.8})
                            break
    
    def _build_equipment_hierarchy(self):
        """建立设备层级关系"""
        equip_nodes = [n for n in self.nodes if n.node_type == 'equipment']
        
        # 建立保护设备层级
        protection_keywords = ['主变保护', '线路保护', '母差保护', '备自投', '安稳装置']
        for equip in equip_nodes:
            for kw in protection_keywords:
                if kw in equip.label:
                    self._add_edge(equip.node_id, "equip_保护装置", 'is_a', {'weight': 0.9})
                    break
    
    def _add_node(self, node: KGNode):
        """添加节点到图谱"""
        if node.node_id not in self.entity_map:
            self.entity_map[node.node_id] = node.node_id
            self.graph.add_node(
                node.node_id,
                label=node.label,
                node_type=node.node_type,
                **node.properties
            )
            self.nodes.append(node)
    
    def _add_edge(self, source: str, target: str, relation: str, properties: Dict = None):
        """添加边到图谱"""
        if source in self.entity_map and target in self.entity_map:
            if not self.graph.has_edge(source, target):
                self.graph.add_edge(
                    source,
                    target,
                    relation=relation,
                    **(properties or {})
                )
                self.edges.append(KGEdge(
                    source_id=source,
                    target_id=target,
                    relation_type=relation,
                    properties=properties or {}
                ))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取图谱统计"""
        node_types = collections.Counter(n.node_type for n in self.nodes)
        edge_types = collections.Counter(e.relation_type for e in self.edges)
        
        return {
            'node_count': self.graph.number_of_nodes(),
            'edge_count': self.graph.number_of_edges(),
            'node_type_distribution': dict(node_types),
            'edge_type_distribution': dict(edge_types),
            'density': nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0,
            'avg_degree': sum(dict(self.graph.degree()).values()) / max(1, self.graph.number_of_nodes())
        }
    
    def export_to_json(self, output_path: str):
        """导出为JSON"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'metadata': {
                'build_time': datetime.now().isoformat(),
                'stats': self.get_stats()
            },
            'nodes': [n.to_dict() for n in self.nodes],
            'edges': [e.to_dict() for e in self.edges]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def export_to_networkx(self, output_path: str):
        """导出为NetworkX格式（供可视化使用）"""
        import json
        data = {
            'nodes': list(self.graph.nodes(data=True)),
            'edges': list(self.graph.edges(data=True))
        }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)
        
        return str(output_path)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='二次作业知识图谱增强构建器')
    parser.add_argument('--input', '-i', required=True, help='输入知识抽取结果JSON')
    parser.add_argument('--output', '-o', default='data/knowledge_graph_enhanced.json', help='输出路径')
    
    args = parser.parse_args()
    
    # 读取知识数据
    with open(args.input, 'r', encoding='utf-8') as f:
        knowledge_data = json.load(f)
    
    # 构建图谱
    print("正在构建知识图谱...")
    builder = EnhancedKnowledgeGraph()
    builder.build_from_knowledge(knowledge_data)
    
    # 导出
    output_path = builder.export_to_json(args.output)
    
    # 打印统计
    stats = builder.get_stats()
    print(f"\n✓ 知识图谱构建完成: {output_path}")
    print(f"\n📊 图谱统计:")
    print(f"  - 节点数: {stats['node_count']}")
    print(f"  - 边数: {stats['edge_count']}")
    print(f"  - 节点类型分布: {stats['node_type_distribution']}")
    print(f"  - 关系类型分布: {stats['edge_type_distribution']}")
    print(f"  - 图谱密度: {stats['density']:.4f}")
    print(f"  - 平均度数: {stats['avg_degree']:.2f}")


if __name__ == '__main__':
    main()
