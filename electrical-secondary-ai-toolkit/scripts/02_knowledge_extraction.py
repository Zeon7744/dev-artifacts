#!/usr/bin/env python3
"""
二次作业知识抽取器
从标准文档中提取术语、规则、流程等知识要素
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import collections

# 术语提取模式
TERM_PATTERNS = [
    # 标准术语定义格式：编号 + 术语 + 定义
    r'(\d+\.\d+)\s*([^：\n]+)[：:]\s*([^\n]{10,200})',
    # 括号定义格式
    r'（([^）]+)）([是：:]([^\n]{5,100}))',
]

# 规则提取模式
RULE_PATTERNS = [
    # 强制性要求
    (r'(应|必须|严禁|禁止)\s*([^；;。\n]{10,100})', 'mandatory'),
    # 建议性要求
    (r'(宜|建议)\s*([^；;。\n]{10,100})', 'recommendation'),
    # 操作动词模式
    (r'(取下|装上|断开|合上|投入|退出|打开|连上|拔出|插入|切换至|拆除|接入)\s*([^；;。\n]{5,80})', 'action'),
]

# 设备类型关键词
EQUIPMENT_KEYWORDS = [
    '主变保护', '线路保护', '母差保护', '备自投', '安稳装置',
    '测控装置', '智能终端', '过程层交换机', '保护装置',
    '电流互感器', '电压互感器', 'CT', 'PT',
    '压板', '空开', '端子', '熔断器',
    '光纤', '光缆', '尾纤',
]

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


@dataclass
class ExtractedTerm:
    """抽取的术语"""
    term_id: str
    name: str
    definition: str
    source_section: str
    source_reference: str
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExtractedRule:
    """抽取的规则"""
    rule_id: str
    rule_type: str  # mandatory, recommendation, action
    content: str
    context: str
    source_section: str
    related_equipment: List[str] = None
    related_action: str = ''
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExtractedProcedure:
    """抽取的流程"""
    procedure_id: str
    name: str
    steps: List[str]
    prerequisites: List[str]
    precautions: List[str]
    source_section: str
    
    def to_dict(self) -> dict:
        return asdict(self)


class KnowledgeExtractor:
    """二次作业知识抽取器"""
    
    def __init__(self):
        self.terms: List[ExtractedTerm] = []
        self.rules: List[ExtractedRule] = []
        self.procedures: List[ExtractedProcedure] = []
        self.entity_counter = {
            'term': 0,
            'rule': 0,
            'procedure': 0
        }
    
    def extract_from_text(self, text: str, source_section: str = '', 
                          source_reference: str = '') -> Dict[str, Any]:
        """从文本抽取知识"""
        
        # 1. 提取术语
        self._extract_terms(text, source_section, source_reference)
        
        # 2. 提取规则
        self._extract_rules(text, source_section)
        
        # 3. 提取流程
        self._extract_procedures(text, source_section)
        
        # 4. 提取实体
        entities = self._extract_entities(text)
        
        return {
            'terms_count': len([t for t in self.terms if t.source_section == source_section]),
            'rules_count': len([r for r in self.rules if r.source_section == source_section]),
            'procedures_count': len([p for p in self.procedures if p.source_section == source_section]),
            'entities': entities
        }
    
    def _extract_terms(self, text: str, section: str, reference: str):
        """提取术语定义"""
        for pattern in TERM_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 3:
                    term_id = match[0] if match[0].isdigit() else f"term_{len(self.terms)+1:04d}"
                    name = match[1].strip() if isinstance(match[1], str) else str(match[1])
                    definition = match[-1].strip() if isinstance(match[-1], str) else str(match[-1])
                    
                    # 过滤有效术语（长度适中，不是纯数字）
                    if len(name) > 2 and len(name) < 50 and not name.isdigit():
                        self.entity_counter['term'] += 1
                        self.terms.append(ExtractedTerm(
                            term_id=f"term_{self.entity_counter['term']:04d}",
                            name=name,
                            definition=definition,
                            source_section=section,
                            source_reference=reference,
                            tags=self._tag_term(name, definition)
                        ))
    
    def _extract_rules(self, text: str, section: str):
        """提取规则"""
        for pattern, rule_type in RULE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                content = match[1] if isinstance(match[1], str) else str(match[1])
                
                # 提取相关设备和动作
                equipment = self._find_equipment(content)
                action = self._find_action(content)
                
                if len(content) > 5:  # 过滤太短的规则
                    self.entity_counter['rule'] += 1
                    self.rules.append(ExtractedRule(
                        rule_id=f"rule_{self.entity_counter['rule']:04d}",
                        rule_type=rule_type,
                        content=content,
                        context=section,
                        source_section=section,
                        related_equipment=equipment,
                        related_action=action
                    ))
    
    def _extract_procedures(self, text: str, section: str):
        """提取流程"""
        # 检测步骤列表
        step_patterns = [
            r'(\d+)[）\.)]\s*([^\n]{10,200})',
            r'[一二三四五六七八九十][、．]\s*([^\n]{10,200})',
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, text)
            if len(matches) >= 3:  # 至少3步才算流程
                steps = [m[1] if isinstance(m, tuple) else m for m in matches[:20]]
                
                self.entity_counter['procedure'] += 1
                self.procedures.append(ExtractedProcedure(
                    procedure_id=f"proc_{self.entity_counter['procedure']:04d}",
                    name=f"流程_{self.entity_counter['procedure']:04d}",
                    steps=steps,
                    prerequisites=[],
                    precautions=[],
                    source_section=section
                ))
                break
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """提取实体"""
        entities = {
            'equipment': [],
            'voltage_level': [],
            'location': [],
            'action': []
        }
        
        # 提取电压等级
        voltage_matches = re.findall(r'(\d+kV)', text)
        entities['voltage_level'] = list(set(voltage_matches))
        
        # 提取设备类型
        for keyword in EQUIPMENT_KEYWORDS:
            if keyword in text:
                entities['equipment'].append(keyword)
        
        # 提取操作动词
        for verb in ACTION_TYPE_MAP.keys():
            if verb in text:
                entities['action'].append(verb)
        
        return entities
    
    def _tag_term(self, name: str, definition: str) -> List[str]:
        """为术语打标签"""
        tags = []
        
        # 根据名称和定义分类
        if '保护' in name or '保护' in definition:
            tags.append('保护设备')
        if '电流' in name or 'CT' in name:
            tags.append('电流回路')
        if '电压' in name or 'PT' in name:
            tags.append('电压回路')
        if '压板' in name:
            tags.append('压板')
        if '光纤' in name or '光缆' in name:
            tags.append('通信')
        if '端子' in name:
            tags.append('端子')
        
        return tags
    
    def _find_equipment(self, text: str) -> List[str]:
        """在文本中查找相关设备"""
        found = []
        for keyword in EQUIPMENT_KEYWORDS:
            if keyword in text:
                found.append(keyword)
        return found
    
    def _find_action(self, text: str) -> str:
        """在文本中查找主要动作"""
        for verb in ACTION_TYPE_MAP.keys():
            if verb in text:
                return verb
        return ''
    
    def get_results(self) -> Dict[str, Any]:
        """获取抽取结果"""
        return {
            'metadata': {
                'extract_time': datetime.now().isoformat(),
                'terms_count': len(self.terms),
                'rules_count': len(self.rules),
                'procedures_count': len(self.procedures)
            },
            'terms': [t.to_dict() for t in self.terms[:100]],  # 限制数量
            'rules': [r.to_dict() for r in self.rules[:200]],
            'procedures': [p.to_dict() for p in self.procedures[:50]],
            'statistics': {
                'term_tags': self._get_term_tag_stats(),
                'rule_types': self._get_rule_type_stats(),
                'action_distribution': self._get_action_stats()
            }
        }
    
    def _get_term_tag_stats(self) -> Dict[str, int]:
        """获取术语标签统计"""
        tag_counts = collections.Counter()
        for term in self.terms:
            for tag in term.tags:
                tag_counts[tag] += 1
        return dict(tag_counts.most_common(20))
    
    def _get_rule_type_stats(self) -> Dict[str, int]:
        """获取规则类型统计"""
        type_counts = collections.Counter(r.rule_type for r in self.rules)
        return dict(type_counts)
    
    def _get_action_stats(self) -> Dict[str, int]:
        """获取动作分布统计"""
        action_counts = collections.Counter(r.related_action for r in self.rules if r.related_action)
        return dict(action_counts.most_common(15))
    
    def save_results(self, output_path: str, format: str = 'json') -> str:
        """保存抽取结果"""
        results = self.get_results()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        elif format == 'md':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# 知识抽取结果\n\n")
                f.write(f"**抽取时间**: {results['metadata']['extract_time']}\n\n")
                f.write(f"- 术语数: {results['metadata']['terms_count']}\n")
                f.write(f"- 规则数: {results['metadata']['rules_count']}\n")
                f.write(f"- 流程数: {results['metadata']['procedures_count']}\n\n")
                
                # 保存术语摘要
                f.write("## 术语摘要\n\n")
                for term in results['terms'][:20]:
                    f.write(f"- **{term['name']}**: {term['definition'][:50]}...\n")
                
                # 保存规则摘要
                f.write("\n## 规则摘要\n\n")
                for rule in results['rules'][:20]:
                    f.write(f"- [{rule['rule_type']}] {rule['content'][:50]}...\n")
        
        return str(output_path)


def main():
    """主函数 - 命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='二次作业知识抽取器')
    parser.add_argument('--input', '-i', required=True, help='输入文本文件或JSON路径')
    parser.add_argument('--output', '-o', default='output/knowledge_extracted.json', help='输出路径')
    parser.add_argument('--format', '-f', choices=['json', 'md'], default='json', help='输出格式')
    parser.add_argument('--section', '-s', default='', help='指定章节处理')
    
    args = parser.parse_args()
    
    # 读取输入
    input_path = Path(args.input)
    if input_path.suffix == '.json':
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        text = json.dumps(data, ensure_ascii=False)
    else:
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
    
    # 抽取知识
    extractor = KnowledgeExtractor()
    extractor.extract_from_text(text, source_section=args.section)
    
    # 保存结果
    output_path = extractor.save_results(args.output, args.format)
    
    # 打印统计
    results = extractor.get_results()
    print(f"✓ 知识抽取完成")
    print(f"  - 术语数: {results['metadata']['terms_count']}")
    print(f"  - 规则数: {results['metadata']['rules_count']}")
    print(f"  - 流程数: {results['metadata']['procedures_count']}")
    print(f"  - 输出文件: {output_path}")
    
    # 打印标签统计
    print(f"\n📊 术语标签分布:")
    for tag, count in results['statistics']['term_tags'].items():
        print(f"  - {tag}: {count}")


if __name__ == '__main__':
    main()
