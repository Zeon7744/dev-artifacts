#!/usr/bin/env python3
"""
附录模板提取器 v2
从附录文档中提取真实措施单模板，优化解析逻辑
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class MeasureItem:
    """措施项"""
    seq: str
    category: str  # 密封安措、回路安措等
    subcategory: str
    content: str
    location: str = ''
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MeasureTemplate:
    """措施单模板"""
    template_id: str
    name: str
    equipment_type: str
    voltage_level: str
    work_type: str
    categories: List[str]
    items: List[Dict[str, str]]
    source_file: str
    source_row_start: int
    source_row_end: int
    
    def to_dict(self) -> dict:
        return asdict(self)


class AppendixTemplateExtractorV2:
    """附录模板提取器 v2"""
    
    # 设备类型关键词映射
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
        """从单个表格提取模板 - 优化版"""
        templates = []
        rows = table.get('rows', [])
        
        if not rows:
            return templates
        
        # 收集所有行的有效内容
        parsed_rows = []
        for row_idx, row in enumerate(rows):
            if not row:
                continue
            
            # 提取关键列：序号、执行类别、内容列
            seq = row[0].strip() if len(row) > 0 else ''
            category = row[1].strip() if len(row) > 1 else ''
            content_col = 3  # 安全技术措施内容列
            
            # 获取内容（去重）
            content_parts = []
            for col_idx in range(3, min(len(row), 7)):  # 检查内容列
                part = row[col_idx].strip() if row[col_idx] else ''
                if part and part not in content_parts:
                    content_parts.append(part)
            
            content = ' '.join(content_parts) if content_parts else ''
            
            parsed_rows.append({
                'row_idx': row_idx,
                'seq': seq,
                'category': category,
                'content': content
            })
        
        # 分析行结构，识别类别和措施项
        current_category = None
        current_subcategory = None
        current_items = []
        start_row = 0
        
        for row_data in parsed_rows:
            seq = row_data['seq']
            category = row_data['category']
            content = row_data['content']
            row_idx = row_data['row_idx']
            
            # 检测主类别标题行（如"一"、"二"、"三"）
            if re.match(r'^[一二三四五六七八九十]+$', seq) and not content:
                # 保存上一个模板
                if current_items:
                    template = self._create_template(
                        '附录参考文档', current_items, table, start_row, row_idx - 1
                    )
                    if template:
                        templates.append(template)
                
                # 新类别开始
                if seq == '一':
                    current_category = '核实'
                elif seq == '二':
                    current_category = '密封安措'
                elif seq == '三':
                    current_category = '回路安措'
                else:
                    current_category = f'第{seq}部分'
                
                current_items = []
                current_subcategory = None
                start_row = row_idx
                
            # 检测子类别标题行（如"（一）"、"（二）"）
            elif re.match(r'^[（(][一二三四五六七八九十]+[）)]$', seq):
                current_subcategory = seq.strip('（）')
                
            # 检测具体措施项（有内容且有操作动词）
            elif seq and content and self._is_measure_content(content):
                item = {
                    'seq': seq,
                    'category': current_category or '',
                    'subcategory': current_subcategory or '',
                    'content': content,
                    'location': self._extract_location(content)
                }
                current_items.append(item)
        
        # 保存最后一个模板
        if current_items:
            template = self._create_template(
                '附录参考文档', current_items, table, start_row, len(parsed_rows) - 1
            )
            if template:
                templates.append(template)
        
        return templates
    
    def _is_measure_content(self, content: str) -> bool:
        """检测是否为有效的措施内容"""
        if not content or len(content) < 10:
            return False
        
        # 排除表头、备注、签名行等
        exclude_patterns = [
            r'^措施单编号', r'^工作票编号', r'^序号', r'^执行', r'^时间',
            r'^工作负责人', r'^编制人', r'^备注', r'^以下空白',
            r'^下接.*措施单页', r'^上接.*措施单页'
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, content):
                return False
        
        # 必须包含操作动词或关键词
        action_verbs = ['密封', '打开', '断开', '合上', '投入', '退出', 
                       '取下', '装上', '拔出', '插入', '拆除', '接入',
                       '确认', '连上', '切换至', '短接', '跨接',
                       '核实', '包封', '隔离']
        
        return any(verb in content for verb in action_verbs)
    
    def _extract_location(self, content: str) -> str:
        """从内容中提取位置信息"""
        # 匹配"在XXX屏操作"或"在XXX屏"
        match = re.search(r'在([^屏]*屏)', content)
        if match:
            return match.group(1)
        return ''
    
    def _create_template(self, 
                        header_text: str,
                        items: List[Dict],
                        table: Dict,
                        start_row: int,
                        end_row: int) -> Optional[MeasureTemplate]:
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
            name=f"{voltage_level}{equipment_type}措施单",
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
                'extraction_time': datetime.now().isoformat()
            },
            'templates': [t.to_dict() for t in self.templates]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='附录模板提取器 v2')
    parser.add_argument('--input', '-i', required=True, help='输入的解析JSON文件')
    parser.add_argument('--output', '-o', default='data/templates_extracted_v2.json', help='输出路径')
    
    args = parser.parse_args()
    
    # 读取解析数据
    with open(args.input, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    # 提取模板
    extractor = AppendixTemplateExtractorV2()
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
        for item in t.items[:3]:
            print(f"      {item['seq']}. {item['content'][:50]}...")
        if len(t.items) > 3:
            print(f"      ... 共 {len(t.items)} 项")


if __name__ == '__main__':
    main()
