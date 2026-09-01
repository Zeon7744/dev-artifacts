#!/usr/bin/env python3
"""
二次作业知识图谱构建器
基于解析后的数据构建领域知识图谱
"""

import json
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

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

# 关系类型定义
RELATION_TYPES = {
    'belongs_to': {'label': '属于', 'directed': True},
    'contains': {'label': '包含', 'directed': True},
    'requires': {'label': '需要', 'directed': True},
    'prohibited': {'label': '禁止', 'directed': True},
    'mandatory': {'label': '必须', 'directed': True},
    'related_to': {'label': '关联', 'directed': False},
    'applies_to': {'label': '适用于', 'directed': True},
    'references': {'label': '引用', 'directed': True},
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


class KnowledgeGraphBuilder:
    """二次作业知识图谱构建器"""
    
    def __init__(self):
        self.graph = nx.DiGraph()  # 有向图
        self.nodes: List[KGNode] = []
        self.edges: List[KGEdge] = []
        self.entity_map: Dict[str, str] = {}  # 实体名 -> 节点ID
        
    def build_from_parsed_data(self, parsed_data: Dict[str, Any]) -> 'KnowledgeGraphBuilder':
        """从解析数据构建知识图谱"""
        
        # 1. 处理章节结构
        self._build_from_sections(parsed_data.get('sections', []))
        
        # 2. 处理表格数据
        self._build_from_tables(parsed_data.get('tables', []))
        
        # 3. 处理知识元素
        self._build_from_knowledge_elements(parsed_data.get('knowledge_elements', []))
        
        # 4. 建立关联关系
        self._build_relationships()
        
        return self
    
    def _build_from_sections(self, sections: List[Dict]):
        """从章节构建图谱"""
        doc_node_id = "doc_main"
        
        # 添加主文档节点
        self._add_node(KGNode(
            node_id=doc_node_id,
            node_type='document',
            label='实施细则（2025版）',
            properties={'source': '主文档'}
        ))
        
        current_section_id = None
        for section in sections:
            section_id = section['section_id']
            section_node = KGNode(
                node_id=section_id,
                node_type='document',
                label=section['title'][:30],  # 截断过长标题
                properties={
                    'level': section['level'],
                    'content_preview': section['content'][:100] if section['content'] else ''
                }
            )
            self._add_node(section_node)
            self._add_edge(doc_node_id, section_id, 'references', {'weight': 1.0})
            
            # 建立父子关系
            if current_section_id and section['level'] > 1:
                self._add_edge(current_section_id, section_id, 'contains', {})
                current_section_id = section_id
            
            # 提取章节中的关键实体
            self._extract_entities_from_text(section['content'], section_id)
    
    def _build_from_tables(self, tables: List[Dict]):
        """从表格构建图谱"""
        for table in tables:
            table_id = table['table_id']
            
            # 添加表格节点
            self._add_node(KGNode(
                node_id=table_id,
                node_type='document',
                label=f'表格: {table["headers"][0] if table["headers"] else "未知"}',
                properties={'row_count': len(table['rows'])}
            ))
            
            # 提取表格中的实体
            for row_idx, row in enumerate(table['rows'][:10]):  # 限制处理行数
                for cell_idx, cell in enumerate(row):
                    if cell and len(cell) > 2:
                        entity_id = f"{table_id}_row{row_idx}_col{cell_idx}"
                        self._add_node(KGNode(
                            node_id=entity_id,
                            node_type='component',
                            label=cell[:20],
                            properties={'source_table': table_id}
                        ))
    
    def _build_from_knowledge_elements(self, elements: List[Dict]):
        """从知识元素构建图谱"""
        for elem in elements:
            elem_id = elem['element_id']
            elem_type = elem['element_type']
            
            # 映射元素类型到节点类型
            type_map = {
                'term': 'equipment',
                'rule': 'rule',
                'procedure': 'action',
                'requirement': 'rule'
            }
            
            node_type = type_map.get(elem_type, 'component')
            
            self._add_node(KGNode(
                node_id=elem_id,
                node_type=node_type,
                label=elem['name'][:30],
                properties={
                    'original_type': elem_type,
                    'definition': elem.get('definition', '')[:100],
                    'context': elem.get('context', '')
                }
            ))
            
            # 建立与上下文的关联
            if elem.get('context'):
                self._add_edge(elem['context'], elem_id, 'requires', {})
    
    def _extract_entities_from_text(self, text: str, context_id: str):
        """从文本中提取实体并添加到图谱"""
        if not text:
            return
            
        # 提取电压等级
        voltage_patterns = [
            r'(\d+kV)',
            r'(500kV|220kV|110kV|35kV|10kV)',
        ]
        for pattern in voltage_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                entity_id = f"voltage_{match}"
                if entity_id not in self.entity_map:
                    self._add_node(KGNode(
                        node_id=entity_id,
                        node_type='voltage_level',
                        label=match,
                        properties={}
                    ))
                self._add_edge(context_id, entity_id, 'applies_to', {})
        
        # 提取设备名称关键词
        equipment_keywords = [
            '主变保护', '线路保护', '母差保护', '备自投', '安稳装置',
            '测控装置', '智能终端', '过程层交换机', '保护装置',
        ]
        for keyword in equipment_keywords:
            if keyword in text:
                entity_id = f"equip_{keyword}"
                if entity_id not in self.entity_map:
                    self._add_node(KGNode(
                        node_id=entity_id,
                        node_type='equipment',
                        label=keyword,
                        properties={}
                    ))
                self._add_edge(context_id, entity_id, 'requires', {})
    
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
            edge_key = (source, target, relation)
            if not self.graph.has_edge(source, target) or relation not in [e[2] for e in self.graph.edges(data=True) if e[0]==source and e[1]==target]:
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
    
    def _build_relationships(self):
        """建立额外关联关系"""
        # 为同类型的节点建立关联
        type_nodes = {}
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            if node_type not in type_nodes:
                type_nodes[node_type] = []
            type_nodes[node_type].append(node_id)
        
        # 同一类型的多个节点之间建立关联（限制数量避免过多边）
        for node_type, node_ids in type_nodes.items():
            if len(node_ids) > 1:
                for i in range(min(5, len(node_ids) - 1)):  # 限制关联数量
                    self._add_edge(node_ids[i], node_ids[i+1], 'related_to', {})
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        return {
            'node_count': self.graph.number_of_nodes(),
            'edge_count': self.graph.number_of_edges(),
            'node_types': dict(self.graph.nodes(data='node_type')),
            'relation_types': list(set([e[2] for e in self.graph.edges(data='relation')])),
            'density': nx.density(self.graph),
            'avg_degree': sum(dict(self.graph.degree()).values()) / max(1, self.graph.number_of_nodes())
        }
    
    def export_to_json(self, output_path: str):
        """导出为JSON格式"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'metadata': {
                'build_time': datetime.now().isoformat(),
                'stats': self.get_graph_stats()
            },
            'nodes': [n.to_dict() for n in self.nodes],
            'edges': [e.to_dict() for e in self.edges]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def export_to_networkx_json(self, output_path: str):
        """导出为NetworkX JSON格式（可用于pyvis可视化）"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为networkx-json格式
        graph_data = nx.node_link_data(self.graph)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def visualize(self, output_path: str = 'output/knowledge_graph.html', 
                  max_nodes: int = 100):
        """可视化知识图谱（生成HTML文件）"""
        try:
            from pyvis.network import Network
            
            # 创建网络
            net = Network(
                height="750px",
                width="100%",
                notebook=False,
                directed=True
            )
            
            # 添加节点（限制数量）
            nodes_to_add = list(self.graph.nodes())[:max_nodes]
            for node_id in nodes_to_add:
                node_data = self.graph.nodes[node_id]
                node_type = node_data.get('node_type', 'unknown')
                
                # 根据类型设置颜色和大小
                color = NODE_TYPES.get(node_type, {}).get('color', '#95a5a6')
                size = 20 if node_type == 'document' else 15
                
                net.add_node(
                    node_id,
                    label=node_data.get('label', node_id)[:20],
                    color=color,
                    size=size,
                    title=str(node_data)
                )
            
            # 添加边
            edges_to_add = list(self.graph.edges())[:max_nodes * 2]
            for source, target in edges_to_add:
                edge_data = self.graph.edges[source, target]
                relation = edge_data.get('relation', 'related')
                
                net.add_edge(
                    source,
                    target,
                    label=RELATION_TYPES.get(relation, {}).get('label', relation),
                    title=relation
                )
            
            # 物理布局
            net.set_options('''
                var options = {
                    "physics": {
                        "forceDirected": {
                            "gravity": -300,
                            "springLength": 200,
                            "springConstant": 0.05
                        },
                        "stabilization": {"iterations": 100}
                    }
                };
            ''')
            
            # 保存
            net.save_graph(output_path)
            return output_path
            
        except ImportError:
            print("警告: pyvis未安装，无法生成可视化")
            return None
    
    def query(self, query_type: str = 'equipment', query_term: str = '') -> List[Dict]:
        """查询知识图谱"""
        results = []
        
        if query_type == 'equipment':
            # 查询设备相关节点
            for node_id, data in self.graph.nodes(data=True):
                if data.get('node_type') == 'equipment' and (
                    not query_term or query_term.lower() in data.get('label', '').lower()
                ):
                    # 获取邻居节点
                    neighbors = list(self.graph.neighbors(node_id))
                    results.append({
                        'node': data,
                        'neighbors': [self.graph.nodes[n] for n in neighbors[:10]]
                    })
        
        elif query_type == 'rule':
            # 查询规则相关节点
            for node_id, data in self.graph.nodes(data=True):
                if data.get('node_type') == 'rule':
                    results.append(data)
        
        elif query_type == 'all':
            # 返回所有节点
            for node_id, data in self.graph.nodes(data=True):
                results.append({
                    'id': node_id,
                    'data': data
                })
        
        return results


# 导入re模块
import re


def main():
    """主函数 - 命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='二次作业知识图谱构建器')
    parser.add_argument('--input', '-i', required=True, help='输入解析数据JSON路径')
    parser.add_argument('--output', '-o', default='output/knowledge_graph.json', help='输出路径')
    parser.add_argument('--visualize', '-v', action='store_true', help='生成可视化HTML')
    
    args = parser.parse_args()
    
    # 读取解析数据
    with open(args.input, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    # 构建知识图谱
    builder = KnowledgeGraphBuilder()
    builder.build_from_parsed_data(parsed_data)
    
    # 导出结果
    json_path = builder.export_to_json(args.output)
    print(f"✓ 知识图谱已导出: {json_path}")
    
    # 打印统计信息
    stats = builder.get_graph_stats()
    print(f"\n📊 图谱统计:")
    print(f"  - 节点数: {stats['node_count']}")
    print(f"  - 边数: {stats['edge_count']}")
    print(f"  - 密度: {stats['density']:.4f}")
    print(f"  - 平均度数: {stats['avg_degree']:.2f}")
    
    # 生成可视化
    if args.visualize:
        viz_path = builder.visualize()
        if viz_path:
            print(f"\n📈 可视化已生成: {viz_path}")
    
    # 保存stats
    with open(Path(args.output).parent / 'graph_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
