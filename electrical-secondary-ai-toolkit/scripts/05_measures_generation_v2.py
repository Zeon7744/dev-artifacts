#!/usr/bin/env python3
"""
二次措施单智能生成器 v2
基于真实附录数据和知识图谱，自动生成符合标准的二次措施单
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

# 操作动词规范（根据标准4.2.1.2）
VALID_ACTION_VERBS = {
    'fuse': ['取下', '装上'],
    'air_switch': ['断开', '合上'],
    'pressure_plate': ['退出', '投入'],
    'terminal_connector': ['打开', '连上'],
    'fiber': ['拔出', '插入'],
    'switch_handle': ['切换至'],
    'wire': ['拆除', '接入'],
    # 补充常见操作
    'seal': ['密封'],
    'short_circuit': ['短接', '跨接'],
    'confirm': ['确认'],
}


@dataclass
class MeasureItem:
    """单条安全措施"""
    seq: str
    category: str  # 核实、密封安措、回路安措等
    subcategory: str
    content: str
    location: str = ''
    execute_mark: str = ''
    execute_time: str = ''
    restore_mark: str = ''
    restore_time: str = ''
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MeasuresSheet:
    """完整的二次措施单"""
    station_name: str
    sheet_number: str
    work_ticket_number: str
    items: List[MeasureItem]
    preparer: str = ''
    approver: str = ''
    executor: str = ''
    supervisor: str = ''
    restorer: str = ''
    witness: str = ''
    notes: str = ''
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


class RealTemplateLoader:
    """从附录文档加载真实模板"""
    
    def __init__(self, template_data_paths: List[str]):
        self.templates = {}
        self._load_templates(template_data_paths)
    
    def _load_templates(self, paths: List[str]):
        """加载模板数据"""
        for path in paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for template in data.get('templates', []):
                    key = f"{template['voltage_level']}_{template['equipment_type']}"
                    self.templates[key] = template
            except Exception as e:
                print(f"警告: 加载模板失败 {path}: {e}")
    
    def get_templates(self) -> Dict[str, Dict]:
        """获取所有模板"""
        return self.templates


class TemplateMatcherV2:
    """模板匹配引擎 v2 - 基于真实附录数据"""
    
    def __init__(self, real_templates: Optional[Dict[str, Dict]] = None):
        self.real_templates = real_templates or {}
        
        # 预设模板（作为补充）
        self.default_templates = {
            '主变保护_220kV_定检': {
                'keywords': ['主变保护', '变压器保护', '220kV', '定检'],
                'priority': 1,
                'structure': {
                    'categories': ['核实', '密封安措', '回路安措'],
                    'has_multi_screen': True,
                    'requires_ct_check': True,
                    'requires_pt_check': True,
                    'screen_count': 3  # A/B/C屏
                },
                'sample_items': [
                    {
                        'seq': '一',
                        'category': '核实',
                        'subcategory': '',
                        'content': '核实二次措施单与现场实际接线一致',
                        'location': ''
                    },
                    {
                        'seq': '二',
                        'category': '密封安措',
                        'subcategory': '',
                        'content': '',
                        'location': ''
                    },
                    {
                        'seq': '（一）',
                        'category': '密封安措',
                        'subcategory': '压板密封',
                        'content': '逐一密封工作票中列明退出的涉及运行设备的压板',
                        'location': ''
                    },
                    {
                        'seq': '（二）',
                        'category': '密封安措',
                        'subcategory': '空开密封',
                        'content': '逐一密封工作票中列明工作范围内的交流电压、直流电源空开',
                        'location': ''
                    },
                    {
                        'seq': '（三）',
                        'category': '密封安措',
                        'subcategory': '出口回路密封',
                        'content': '密封涉及运行设备的跳闸、失灵、闭锁出口回路端子',
                        'location': ''
                    },
                    {
                        'seq': '（四）',
                        'category': '密封安措',
                        'subcategory': '带电回路密封',
                        'content': '密封带电的二次电压回路、二次电流回路端子',
                        'location': ''
                    },
                    {
                        'seq': '三',
                        'category': '回路安措',
                        'subcategory': '',
                        'content': '',
                        'location': ''
                    },
                    {
                        'seq': '（一）',
                        'category': '回路安措',
                        'subcategory': '电流回路',
                        'content': '确认CT无流后，打开二次电流回路端子连接片，并密封非工作侧端子',
                        'location': ''
                    },
                    {
                        'seq': '（二）',
                        'category': '回路安措',
                        'subcategory': '电压回路',
                        'content': '打开二次电压回路端子连接片，并密封非工作侧端子',
                        'location': ''
                    }
                ]
            },
            '线路保护_220kV_定检': {
                'keywords': ['线路保护', '线保护', '220kV', '定检'],
                'priority': 2,
                'structure': {
                    'categories': ['核实', '密封安措', '回路安措'],
                    'has_multi_screen': True,
                    'requires_ct_check': True,
                    'requires_pt_check': True,
                    'requires_fiber_check': True,
                    'screen_count': 2  # 主一/主二保护屏
                },
                'sample_items': [
                    {
                        'seq': '一',
                        'category': '核实',
                        'subcategory': '',
                        'content': '核实二次措施单与现场实际接线一致',
                        'location': ''
                    },
                    {
                        'seq': '二',
                        'category': '密封安措',
                        'subcategory': '',
                        'content': '',
                        'location': ''
                    },
                    {
                        'seq': '（一）',
                        'category': '密封安措',
                        'subcategory': '压板密封',
                        'content': '逐一密封工作票中列明退出的涉及运行设备的压板',
                        'location': ''
                    },
                    {
                        'seq': '（二）',
                        'category': '密封安措',
                        'subcategory': '空开密封',
                        'content': '逐一密封工作票中列明工作范围内的交流电压、直流电源空开',
                        'location': ''
                    },
                    {
                        'seq': '（三）',
                        'category': '密封安措',
                        'subcategory': '出口回路密封',
                        'content': '逐一密封涉及运行设备的跳闸、失灵、闭锁出口回路端子',
                        'location': ''
                    },
                    {
                        'seq': '（四）',
                        'category': '密封安措',
                        'subcategory': '带电回路密封',
                        'content': '密封带电的二次电压回路、二次电流回路端子',
                        'location': ''
                    },
                    {
                        'seq': '三',
                        'category': '回路安措',
                        'subcategory': '',
                        'content': '',
                        'location': ''
                    },
                    {
                        'seq': '（一）',
                        'category': '回路安措',
                        'subcategory': '电流回路',
                        'content': '确认线路CT无流后，打开二次电流回路端子连接片',
                        'location': ''
                    },
                    {
                        'seq': '（二）',
                        'category': '回路安措',
                        'subcategory': '电压回路',
                        'content': '打开二次电压回路端子连接片',
                        'location': ''
                    },
                    {
                        'seq': '（三）',
                        'category': '回路安措',
                        'subcategory': '光纤通道',
                        'content': '拔出保护光纤通道尾纤，并用防尘套密封',
                        'location': ''
                    }
                ]
            }
        }
    
    def match(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """匹配最佳模板"""
        scores = {}
        
        # 评分真实模板
        for key, template in self.real_templates.items():
            score = 0
            voltage = params.get('voltage_level', '')
            equipment = params.get('equipment_type', '')
            work_type = params.get('work_type', '')
            
            if voltage in key:
                score += 3
            if equipment in key:
                score += 3
            if work_type in key:
                score += 1
            
            if score > 0:
                scores[key] = score
        
        # 评分默认模板
        for tpl_name, tpl_data in self.default_templates.items():
            score = 0
            keywords = tpl_data['keywords']
            for kw in keywords:
                if kw in str(params):
                    score += 1
            
            # 结构匹配加分
            if params.get('voltage_level') and params['voltage_level'] in tpl_name:
                score += 2
            if params.get('equipment_type') and params['equipment_type'] in tpl_name:
                score += 2
            if params.get('work_type') == '定检' and '定检' in tpl_name:
                score += 1
            
            if score > 0:
                scores[f"default:{tpl_name}"] = score
        
        if not scores:
            # 返回第一个可用模板
            if self.real_templates:
                best_key = list(self.real_templates.keys())[0]
                return {
                    'matched_template': best_key,
                    'scores': {best_key: 1},
                    'template_data': self.real_templates[best_key],
                    'is_real': True
                }
            else:
                best_name = list(self.default_templates.keys())[0]
                return {
                    'matched_template': best_name,
                    'scores': {best_name: 1},
                    'template_data': self.default_templates[best_name],
                    'is_real': False
                }
        
        # 返回得分最高的模板
        best_key = max(scores, key=scores.get)
        is_real = best_key not in [f"default:{n}" for n in self.default_templates.keys()]
        
        return {
            'matched_template': best_key,
            'scores': scores,
            'template_data': self.real_templates.get(best_key) or self.default_templates.get(best_key.replace("default:", "")),
            'is_real': is_real
        }


class MeasuresGeneratorV2:
    """二次措施单智能生成器 v2"""
    
    def __init__(self, knowledge_base: Optional[Dict] = None, real_templates: Optional[Dict] = None):
        self.kb = knowledge_base or {}
        self.template_matcher = TemplateMatcherV2(real_templates)
        
        # 操作动词映射
        self.action_verbs = VALID_ACTION_VERBS
    
    def generate(self, params: Dict[str, Any]) -> MeasuresSheet:
        """生成措施单"""
        
        # 1. 参数验证
        validated_params = self._validate_params(params)
        
        # 2. 模板匹配
        match_result = self.template_matcher.match(validated_params)
        template = match_result['template_data']
        is_real = match_result.get('is_real', False)
        
        # 3. 生成措施项
        items = self._generate_items(validated_params, template, is_real)
        
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
        year = datetime.now().strftime('%Y')
        hash_val = hash(f"{params['substation_name']}{params['equipment_type']}")
        seq = abs(hash_val) % 1000 + 1
        return f"{year}-{seq:04d}"
    
    def _generate_items(self, params: Dict[str, Any], template: Dict, is_real: bool) -> List[MeasureItem]:
        """生成具体措施项"""
        items = []
        
        if is_real and 'items' in template:
            # 使用真实模板数据
            items = self._process_real_template(template, params)
        else:
            # 使用默认模板逻辑
            items = self._generate_from_default_template(params, template)
        
        return items
    
    def _process_real_template(self, template: Dict, params: Dict) -> List[MeasureItem]:
        """处理真实模板数据"""
        items = []
        
        for item_data in template.get('items', []):
            # 填充位置信息
            content = item_data.get('content', '')
            location = item_data.get('location', '')
            
            # 替换占位符
            content = self._fill_placeholders(content, params)
            location = self._fill_placeholders(location, params)
            
            item = MeasureItem(
                seq=item_data.get('seq', ''),
                category=item_data.get('category', ''),
                subcategory=item_data.get('subcategory', ''),
                content=content,
                location=location
            )
            items.append(item)
        
        return items
    
    def _generate_from_default_template(self, params: Dict, template: Dict) -> List[MeasureItem]:
        """从默认模板生成"""
        items = []
        structure = template.get('structure', {})
        screen_count = structure.get('screen_count', 3)
        
        # 第一遍：核实
        items.append(MeasureItem(
            seq='一',
            category='核实',
            subcategory='',
            content='核实二次措施单与现场实际接线一致',
            location=''
        ))
        
        # 第二遍：密封安措
        if '密封安措' in structure.get('categories', []):
            items.append(MeasureItem(
                seq='二',
                category='密封安措',
                subcategory='',
                content='',
                location=''
            ))
            
            # 添加密封安措子项
            sub_items = template.get('sample_items', [])
            for item in sub_items:
                if item.get('category') == '密封安措':
                    items.append(MeasureItem(
                        seq=item['seq'],
                        category='密封安措',
                        subcategory=item.get('subcategory', ''),
                        content=item['content'],
                        location=item.get('location', '')
                    ))
        
        # 第三遍：回路安措
        if '回路安措' in structure.get('categories', []):
            items.append(MeasureItem(
                seq='三',
                category='回路安措',
                subcategory='',
                content='',
                location=''
            ))
            
            for item in sub_items:
                if item.get('category') == '回路安措':
                    items.append(MeasureItem(
                        seq=item['seq'],
                        category='回路安措',
                        subcategory=item.get('subcategory', ''),
                        content=item['content'],
                        location=item.get('location', '')
                    ))
        
        return items
    
    def _fill_placeholders(self, content: str, params: Dict) -> str:
        """填充占位符"""
        if not content:
            return content
        
        # 替换变电站名称
        station = params.get('substation_name', 'XX')
        content = content.replace('XX', station)
        
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
        has_verify = False
        has_sealing = False
        has_circuit = False
        
        for item in measures.items:
            if item.category == '核实':
                has_verify = True
            if item.category == '密封安措':
                has_sealing = True
            if item.category == '回路安措':
                has_circuit = True
        
        if not has_verify:
            warnings.append('缺少核实项')
        if not has_sealing:
            warnings.append('缺少密封安措项')
        if not has_circuit:
            warnings.append('缺少回路安措项')
        
        # 3. 检查操作动词规范性
        invalid_verbs = ['耀', '曜']
        for item in measures.items:
            for verb in invalid_verbs:
                if verb in item.content:
                    issues.append(f"措施项包含禁止字符'{verb}': {item.content[:50]}...")
        
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
    
    parser = argparse.ArgumentParser(description='二次措施单智能生成器 v2')
    parser.add_argument('--input', '-i', required=True, help='输入参数JSON路径')
    parser.add_argument('--output', '-o', default='output/measures.json', help='输出路径')
    parser.add_argument('--format', '-f', choices=['json', 'md', 'both'], default='both', help='输出格式')
    parser.add_argument('--validate', '-v', action='store_true', help='执行合规校验')
    parser.add_argument('--templates', '-t', nargs='+', help='真实模板数据文件路径')
    
    args = parser.parse_args()
    
    # 读取输入参数
    with open(args.input, 'r', encoding='utf-8') as f:
        params = json.load(f)
    
    # 加载真实模板
    real_templates = None
    if args.templates:
        loader = RealTemplateLoader(args.templates)
        real_templates = loader.get_templates()
    
    # 生成措施单
    generator = MeasuresGeneratorV2(real_templates=real_templates)
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
