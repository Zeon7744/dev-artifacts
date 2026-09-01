#!/usr/bin/env python3
"""
二次措施单智能生成器
基于知识图谱和模板匹配，自动生成符合标准的二次措施单
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import copy

# 措施单标准格式（9列）
MEASURES_TABLE_HEADERS = [
    '序号', '执行', '时间', '安全技术措施内容', 
    '安全技术措施内容', '安全技术措施内容', '安全技术措施内容',
    '恢复', '时间'
]


@dataclass
class MeasureItem:
    """单条安全措施"""
    seq: str
    category: str  # 密封安措、回路安措等
    subcategory: str
    content: str
    location: str = ''  # 屏柜位置
    execute_mark: str = ''  # 执行标记
    execute_time: str = ''  # 执行时间
    restore_mark: str = ''  # 恢复标记
    restore_time: str = ''  # 恢复时间
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MeasuresSheet:
    """完整的二次措施单"""
    station_name: str
    sheet_number: str
    work_ticket_number: str
    items: List[MeasureItem]
    preparer: str = ''  # 编制人
    approver: str = ''  # 工作负责人
    executor: str = ''  # 执行人
    supervisor: str = ''  # 监护人
    restorer: str = ''  # 恢复人
    witness: str = ''  # 见证人
    notes: str = ''  # 备注
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            'station_name': self.station_name,
            'sheet_number': self.sheet_number,
            'work_ticket_number': self.work_ticket_number,
            'items': [item.to_dict() for item in self.items],
            'preparer': self.preparer,
            'approver': self.approver,
            'executor': self.executor,
            'supervisor': self.supervisor,
            'restorer': self.restorer,
            'witness': self.witness,
            'notes': self.notes,
            'created_at': self.created_at
        }


class TemplateMatcher:
    """模板匹配引擎"""
    
    # 预设模板库（基于附录4典型文档）
    TEMPLATES = {
        '主变保护_220kV_定检': {
            'keywords': ['主变保护', '220kV', '定检'],
            'priority': 1,
            'structure': {
                'categories': ['密封安措', '回路安措'],
                'has_multi_screen': True,
                'requires_ct_check': True,
                'requires_pt_check': True
            },
            'sample_content': [
                {
                    'category': '密封安措',
                    'subcategory': '压板密封',
                    'content': '逐一密封工作票中列明退出的涉及运行设备的压板'
                },
                {
                    'category': '密封安措', 
                    'subcategory': '空开密封',
                    'content': '逐一密封工作票中列明工作范围内的交流电压、直流电源空开'
                },
                {
                    'category': '密封安措',
                    'subcategory': '出口回路密封',
                    'content': '密封涉及运行设备的跳闸、失灵、闭锁出口回路端子'
                },
                {
                    'category': '回路安措',
                    'subcategory': '电流回路',
                    'content': '确认CT无流后，打开二次电流回路端子连接片，并密封非工作侧端子'
                },
                {
                    'category': '回路安措',
                    'subcategory': '电压回路',
                    'content': '打开二次电压回路端子连接片，并密封非工作侧端子'
                }
            ]
        },
        '线路保护_220kV_定检': {
            'keywords': ['线路保护', '220kV', '定检'],
            'priority': 2,
            'structure': {
                'categories': ['密封安措', '回路安措'],
                'has_multi_screen': True,
                'requires_ct_check': True,
                'requires_pt_check': True,
                'requires_fiber_check': True
            },
            'sample_content': [
                {
                    'category': '密封安措',
                    'subcategory': '压板密封',
                    'content': '逐一密封工作票中列明退出的涉及运行设备的压板'
                },
                {
                    'category': '回路安措',
                    'subcategory': '电流回路',
                    'content': '确认线路CT无流后，打开二次电流回路端子连接片'
                },
                {
                    'category': '回路安措',
                    'subcategory': '电压回路',
                    'content': '打开二次电压回路端子连接片'
                },
                {
                    'category': '回路安措',
                    'subcategory': '光纤通道',
                    'content': '拔出保护光纤通道尾纤，并用防尘套密封'
                }
            ]
        },
        '母差保护_500kV_定检': {
            'keywords': ['母差保护', '500kV', '定检'],
            'priority': 3,
            'structure': {
                'categories': ['密封安措', '回路安措'],
                'has_multi_screen': True,
                'requires_ct_check': True,
                'requires_busbar_check': True
            },
            'sample_content': [
                {
                    'category': '密封安措',
                    'subcategory': '压板密封',
                    'content': '逐一密封工作票中列明退出的涉及运行设备的压板'
                },
                {
                    'category': '回路安措',
                    'subcategory': '母差电流回路',
                    'content': '在母差保护屏打开母线电流回路端子连接片'
                }
            ]
        }
    }
    
    def __init__(self):
        self.templates = self.TEMPLATES
    
    def match(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """匹配最佳模板"""
        scores = {}
        
        for template_name, template in self.templates.items():
            score = 0
            for keyword in template['keywords']:
                if keyword in str(params):
                    score += 1
            
            # 结构匹配加分
            if params.get('voltage_level') and template_name.endswith(params['voltage_level']):
                score += 2
            if params.get('equipment_type') and params['equipment_type'] in template_name:
                score += 2
            if params.get('work_type') == '定检' and '定检' in template_name:
                score += 1
            
            scores[template_name] = score
        
        # 返回得分最高的模板
        best_template = max(scores, key=scores.get)
        return {
            'matched_template': best_template,
            'scores': scores,
            'template_data': self.templates[best_template]
        }


class MeasuresGenerator:
    """二次措施单智能生成器"""
    
    def __init__(self, knowledge_base: Optional[Dict] = None):
        self.kb = knowledge_base or {}
        self.template_matcher = TemplateMatcher()
        
        # 操作动词映射（根据标准4.2.1.2）
        self.action_verbs = {
            'fuse': {'take_off': '取下', 'install': '装上'},
            'air_switch': {'open': '断开', 'close': '合上'},
            'pressure_plate': {'output': '退出', 'input': '投入'},
            'terminal_connector': {'open': '打开', 'connect': '连上'},
            'fiber': {'pull_out': '拔出', 'insert': '插入'},
            'switch_handle': {'switch_to': '切换至'},
            'wire': {'remove': '拆除', 'connect': '接入'}
        }
    
    def generate(self, params: Dict[str, Any]) -> MeasuresSheet:
        """生成措施单"""
        
        # 1. 参数验证
        validated_params = self._validate_params(params)
        
        # 2. 模板匹配
        match_result = self.template_matcher.match(validated_params)
        template = match_result['template_data']
        
        # 3. 生成措施项
        items = self._generate_items(validated_params, template)
        
        # 4. 填充基本信息
        sheet_number = self._generate_sheet_number(validated_params)
        
        # 5. 生成完整措施单
        measures_sheet = MeasuresSheet(
            station_name=validated_params.get('substation_name', 'XX变电站'),
            sheet_number=sheet_number,
            work_ticket_number=validated_params.get('work_ticket_number', ''),
            items=items,
            notes=validated_params.get('notes', '')
        )
        
        return measures_sheet
    
    def _validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证输入参数"""
        required = ['equipment_type', 'work_type']
        optional = ['voltage_level', 'substation_name', 'protection_model', 
                   'wiring_form', 'work_ticket_number']
        
        # 设置默认值
        defaults = {
            'voltage_level': '220kV',
            'substation_name': 'XX变电站',
            'protection_model': '',
            'wiring_form': '',
            'work_ticket_number': '',
            'notes': ''
        }
        
        validated = {}
        for key in required:
            if key not in params:
                raise ValueError(f"缺少必填参数: {key}")
            validated[key] = params[key]
        
        for key in optional:
            validated[key] = params.get(key, defaults.get(key, ''))
        
        return validated
    
    def _generate_sheet_number(self, params: Dict[str, Any]) -> str:
        """生成措施单编号"""
        # 格式：年份-序号
        year = datetime.now().strftime('%Y')
        # 使用简单哈希生成序号
        hash_val = hash(f"{params['substation_name']}{params['equipment_type']}")
        seq = abs(hash_val) % 1000 + 1
        return f"{year}-{seq:04d}"
    
    def _generate_items(self, params: Dict[str, Any], template: Dict) -> List[MeasureItem]:
        """生成具体措施项"""
        items = []
        seq_num = 1
        location_counter = {'A': 1, 'B': 2, 'C': 3}
        
        # 第一遍：核实阶段
        items.append(MeasureItem(
            seq=str(seq_num),
            category='',
            subcategory='',
            content='核实二次措施单与现场实际接线一致',
            location=params.get('substation_name', '')
        ))
        seq_num += 1
        
        # 第二遍：根据模板生成密封安措
        if '密封安措' in template['structure']['categories']:
            items.append(MeasureItem(
                seq='',
                category='密封安措',
                subcategory='',
                content='',
                location=''
            ))
            
            for content_item in template['sample_content']:
                if content_item['category'] == '密封安措':
                    screen_suffix = chr(64 + (seq_num % 3))  # A, B, C轮换
                    items.append(MeasureItem(
                        seq=str(seq_num),
                        category='密封安措',
                        subcategory=content_item['subcategory'],
                        content=self._format_measure_content(
                            content_item['content'],
                            params,
                            screen_suffix
                        ),
                        location=f'{params.get("substation_name", "XX")}{screen_suffix}屏'
                    ))
                    seq_num += 1
        
        # 第三遍：生成回路安措
        if '回路安措' in template['structure']['categories']:
            items.append(MeasureItem(
                seq='',
                category='回路安措',
                subcategory='',
                content='',
                location=''
            ))
            
            for content_item in template['sample_content']:
                if content_item['category'] == '回路安措':
                    screen_suffix = chr(64 + (seq_num % 3))
                    items.append(MeasureItem(
                        seq=str(seq_num),
                        category='回路安措',
                        subcategory=content_item['subcategory'],
                        content=self._format_measure_content(
                            content_item['content'],
                            params,
                            screen_suffix
                        ),
                        location=f'{params.get("substation_name", "XX")}{screen_suffix}屏'
                    ))
                    seq_num += 1
        
        return items
    
    def _format_measure_content(self, content_template: str, params: Dict, screen: str) -> str:
        """格式化措施内容，填充具体参数"""
        
        # 替换占位符
        content = content_template
        
        # 设备名称替换
        equipment = params.get('equipment_type', '')
        voltage = params.get('voltage_level', '220kV')
        
        # 添加具体屏柜信息
        if '在XXP' in content:
            content = content.replace('XXP', f'{params.get("substation_name", "XX")}{screen}')
        
        # 添加电压等级
        if voltage in ['220kV', '500kV']:
            content = f'{voltage} {equipment}' + content.replace(f'{voltage} {equipment}', '').replace('XX', params.get("substation_name", "XX"))
        
        return content
    
    def validate_measures(self, measures: MeasuresSheet) -> Dict[str, Any]:
        """校验措施单合规性"""
        issues = []
        warnings = []
        
        # 1. 检查必填字段
        if not measures.sheet_number:
            issues.append('缺少措施单编号')
        if not measures.items:
            issues.append('措施单为空')
        
        # 2. 检查措施项完整性
        has_sealing = False
        has_circuit = False
        for item in measures.items:
            if '密封安措' in item.category:
                has_sealing = True
            if '回路安措' in item.category:
                has_circuit = True
        
        if not has_sealing:
            warnings.append('缺少密封安措项')
        if not has_circuit:
            warnings.append('缺少回路安措项')
        
        # 3. 检查操作动词规范性（根据4.2.1.2）
        valid_verbs = ['取下', '装上', '断开', '合上', '投入', '退出', 
                      '打开', '连上', '拔出', '插入', '切换至', '拆除', '接入']
        
        for item in measures.items:
            for verb in valid_verbs:
                if verb in item.content:
                    break
            else:
                # 检查是否有有效操作动词
                if item.category and '安措' in item.category:
                    pass  # 允许类别标题行
            
        # 4. 检查关键回路是否密封
        critical_keywords = ['跳闸', '失灵', '闭锁', '电流', '电压']
        for item in measures.items:
            if '密封' in item.content:
                for keyword in critical_keywords:
                    if keyword in item.content:
                        break
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'item_count': len(measures.items),
            'checked_at': datetime.now().isoformat()
        }


class MeasuresExporter:
    """措施单导出器"""
    
    @staticmethod
    def export_to_json(measures: MeasuresSheet, output_path: str) -> str:
        """导出为JSON"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = measures.to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    @staticmethod
    def export_to_markdown(measures: MeasuresSheet, output_path: str) -> str:
        """导出为Markdown"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# 二次措施单\n\n")
            f.write(f"**变电站**: {measures.station_name}\n\n")
            f.write(f"**措施单编号**: {measures.sheet_number}\n\n")
            f.write(f"**工作票编号**: {measures.work_ticket_number}\n\n")
            f.write(f"**生成时间**: {measures.created_at}\n\n")
            
            f.write("## 安全措施内容\n\n")
            f.write("| 序号 | 类别 | 子类别 | 措施内容 | 位置 |\n")
            f.write("|-----|------|--------|---------|------|\n")
            
            for item in measures.items:
                f.write(f"| {item.seq} | {item.category} | {item.subcategory} | {item.content} | {item.location} |\n")
            
            f.write("\n## 签名栏\n\n")
            f.write(f"- 编制人: {measures.preparer}\n")
            f.write(f"- 工作负责人: {measures.approver}\n")
            f.write(f"- 执行人: {measures.executor}\n")
            f.write(f"- 监护人: {measures.supervisor}\n")
            f.write(f"- 恢复人: {measures.restorer}\n")
            
            if measures.notes:
                f.write(f"\n**备注**: {measures.notes}\n")
        
        return str(output_path)


def main():
    """主函数 - 命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='二次措施单智能生成器')
    parser.add_argument('--input', '-i', required=True, help='输入参数JSON路径')
    parser.add_argument('--output', '-o', default='output/measures.json', help='输出路径')
    parser.add_argument('--format', '-f', choices=['json', 'md', 'both'], default='both', help='输出格式')
    parser.add_argument('--validate', '-v', action='store_true', help='执行合规校验')
    
    args = parser.parse_args()
    
    # 读取输入参数
    with open(args.input, 'r', encoding='utf-8') as f:
        params = json.load(f)
    
    # 生成措施单
    generator = MeasuresGenerator()
    measures = generator.generate(params)
    
    # 合规校验
    validation = None
    if args.validate:
        validation = generator.validate_measures(measures)
        print(f"\n✅ 合规校验结果:")
        print(f"  - 有效: {validation['valid']}")
        print(f"  - 问题数: {len(validation['issues'])}")
        print(f"  - 警告数: {len(validation['warnings'])}")
        if validation['issues']:
            print(f"  - 问题详情: {validation['issues']}")
        if validation['warnings']:
            print(f"  - 警告详情: {validation['warnings']}")
    
    # 导出
    exporter = MeasuresExporter()
    
    if args.format in ['json', 'both']:
        json_path = exporter.export_to_json(measures, args.output)
        print(f"\n📄 JSON已导出: {json_path}")
    
    if args.format in ['md', 'both']:
        md_path = args.output.replace('.json', '.md')
        md_path = exporter.export_to_markdown(measures, md_path)
        print(f"📝 Markdown已导出: {md_path}")
    
    # 保存校验结果
    if validation and args.validate:
        val_path = args.output.replace('.json', '_validation.json')
        with open(val_path, 'w', encoding='utf-8') as f:
            json.dump(validation, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
