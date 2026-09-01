#!/usr/bin/env python3
"""
附录模板提取器
从附录4-6、4-7等参考文档中提取真实措施单模板
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict


@dataclass
class MeasureTemplate:
    """措施单模板"""
    template_id: str
    name: str
    equipment_type: str  # 主变保护、线路保护、母差保护等
    voltage_level: str   # 220kV, 500kV等
    work_type: str       # 定检、投运等
    categories: List[str]  # 密封安措、回路安措等
    items: List[Dict[str, str]]  # 措施项列表
    source_file: str
    source_row_start: int
    source_row_end: int
    
    def to_dict(self) -> dict:
        return asdict(self)


class AppendixTemplateExtractor:
    """附录模板提取器"""
    
    # 设备类型关键词
    EQUIPMENT_PATTERNS = {
        '主变保护': ['主变保护', '变压器保护'],
        '线路保护': ['线路保护', '线保护'],
        '母差保护': ['母差保护', '母差'],
        '备自投': ['备自投', '备用电源'],
        '安稳装置': ['安稳装置', '安全稳定'],
    }
    
    # 电压等级关键词
    VOLTAGE_PATTERNS = {
        '500kV': ['500kV', '500千伏'],
        '220kV': ['220kV', '220千伏'],
        '110kV': ['110kV', '110千伏'],
        '35kV': ['35kV', '35千伏'],
        '10kV': ['10kV', '10千伏'],
    }
    
    def __init__(self):
        self.templates: List[MeasureTemplate] = []
        self.template_counter = 0
    
    def extract_from_parsed_data(self, parsed_data: Dict[str, Any]) -> List[MeasureTemplate]:
        """从解析数据中提取模板"""
        tables = parsed_data.get('tables', [])
        
        for table in tables:
            table_templates = self._extract_from_table(table)
            self.templates.extend(table_templates)
        
        return self.templates
    
    def _extract_from_table(self, table: Dict[str, Any]) -> List[MeasureTemplate]:
        """从单个表格提取模板"""
        templates = []
        rows = table.get('rows', [])
        
        if not rows:
            return templates
        
        # 检测表格标题行（通常包含变电站名称）
        header_text = ' '.join([str(h) for h in table.get('headers', [])[:2]])
        
        # 解析表格内容
        current_category = None
        current_subcategory = None
        current_items = []
        start_row = 0
        
        for row_idx, row in enumerate(rows):
            if not row or len(row) < 2:
                continue
            
            # 提取第一列（序号）和第二列（内容）
            seq = row[0].strip() if row[0] else ''
            content = row[1].strip() if len(row) > 1 and row[1] else ''
            
            # 检测类别标题行
            if self._is_category_header(seq, content):
                if current_items:
                    # 保存上一个模板
                    template = self._create_template(
                        header_text, current_items, table, start_row, row_idx - 1
                    )
                    if template:
                        templates.append(template)
                
                current_category = self._parse_category(content)
                current_items = []
                start_row = row_idx
                current_subcategory = None
                
            elif self._is_subcategory_header(seq, content):
                current_subcategory = self._parse_subcategory(content)
                
            elif seq and content and self._is_measure_content(content):
                # 这是实际的措施项
                item = {
                    'seq': seq,
                    'category': current_category or '',
                    'subcategory': current_subcategory or '',
                    'content': content
                }
                current_items.append(item)
        
        # 保存最后一个模板
        if current_items:
            template = self._create_template(
                header_text, current_items, table, start_row, len(rows) - 1
            )
            if template:
                templates.append(template)
        
        return templates
    
    def _is_category_header(self, seq: str, content: str) -> bool:
        """检测是否为类别标题行"""
        # 类别标题通常是"一"、"二"、"密封安措"、"回路安措"等
        category_keywords = ['一', '二', '三', '四', '五', 
                            '密封安措', '回路安措', '核实']
        return any(kw in content for kw in category_keywords) and len(content) < 20
    
    def _is_subcategory_header(self, seq: str, content: str) -> bool:
        """检测是否为子类别标题行"""
        # 子类别标题通常是"（一）"、"（二）"等
        if re.match(r'^[（(][一二三四五六七八九十]+[）)]$', seq):
            return True
        if re.match(r'^[（(][一二三四五六七八九十]+[）)]', content):
            return True
        return False
    
    def _is_measure_content(self, content: str) -> bool:
        """检测是否为措施内容"""
        # 措施内容通常包含操作动词
        action_verbs = ['密封', '打开', '断开', '合上', '投入', '退出', 
                       '取下', '装上', '拔出', '插入', '拆除', '接入',
                       '确认', '连上', '切换至']
        return any(verb in content for verb in action_verbs) and len(content) > 10
    
    def _parse_category(self, content: str) -> str:
        """解析类别"""
        if '密封' in content or '安措' in content:
            return '密封安措'
        elif '回路' in content:
            return '回路安措'
        elif '核实' in content:
            return '核实'
        return content
    
    def _parse_subcategory(self, content: str) -> str:
        """解析子类别"""
        # 提取"在XX屏操作"等信息
        match = re.search(r'在[^屏]*屏', content)
        if match:
            return match.group()
        return content[:30] if len(content) > 30 else content
    
    def _create_template(self, 
                        header_text: str,
                        items: List[Dict],
                        table: Dict,
                        start_row: int,
                        end_row: int) -> MeasureTemplate:
        """创建模板"""
        if not items:
            return None
        
        self.template_counter += 1
        
        # 从内容推断设备类型和电压等级
        all_content = ' '.join([item['content'] for item in items])
        equipment_type = self._detect_equipment_type(all_content)
        voltage_level = self._detect_voltage_level(all_content)
        work_type = '定检' if '定检' in header_text or '定检' in all_content else '其他'
        
        # 提取类别
        categories = list(set([item['category'] for item in items if item['category']]))
        
        return MeasureTemplate(
            template_id=f"tmpl_{self.template_counter:04d}",
            name=f"{voltage_level}{equipment_type}{work_type}措施单",
            equipment_type=equipment_type,
            voltage_level=voltage_level,
            work_type=work_type,
            categories=categories,
            items=items,
            source_file=table.get('source_file', 'unknown'),
            source_row_start=start_row,
            source_row_end=end_row
        )
    
    def _detect_equipment_type(self, text: str) -> str:
        """检测设备类型"""
        for equip_type, keywords in self.EQUIPMENT_PATTERNS.items():
            for kw in keywords:
                if kw in text:
                    return equip_type
        return '保护装置'
    
    def _detect_voltage_level(self, text: str) -> str:
        """检测电压等级"""
        for voltage, keywords in self.VOLTAGE_PATTERNS.items():
            for kw in keywords:
                if kw in text:
                    return voltage
        # 尝试从文本中提取kV
        match = re.search(r'(\d+)kV', text)
        if match:
            return match.group(1) + 'kV'
        return '220kV'
    
    def save_templates(self, output_path: str):
        """保存模板到JSON文件"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'metadata': {
                'total_templates': len(self.templates),
                'extraction_time': __import__('datetime').datetime.now().isoformat()
            },
            'templates': [t.to_dict() for t in self.templates]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='附录模板提取器')
    parser.add_argument('--input', '-i', required=True, help='输入的解析JSON文件')
    parser.add_argument('--output', '-o', default='data/templates_extracted.json', help='输出路径')
    
    args = parser.parse_args()
    
    # 读取解析数据
    with open(args.input, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    # 提取模板
    extractor = AppendixTemplateExtractor()
    templates = extractor.extract_from_parsed_data(parsed_data)
    
    # 保存
    output_path = extractor.save_templates(args.output)
    
    # 打印统计
    print(f"✓ 模板提取完成: {len(templates)} 个模板")
    print(f"  输出文件: {output_path}")
    
    # 打印模板列表
    print("\n📋 提取的模板:")
    for t in templates:
        print(f"  - [{t.template_id}] {t.name} ({len(t.items)} 项)")


if __name__ == '__main__':
    main()
