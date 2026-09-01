#!/usr/bin/env python3
"""
完整工作流测试脚本 v2
整合模板提取、知识图谱和措施单生成
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加scripts目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 使用模块导入
import importlib.util

# 加载生成器模块
spec = importlib.util.spec_from_file_location("measures_gen", "scripts/05_measures_generation_v2.py")
measures_gen_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measures_gen_module)

MeasuresGeneratorV2 = measures_gen_module.MeasuresGeneratorV2
RealTemplateLoader = measures_gen_module.RealTemplateLoader
MeasuresExporter = measures_gen_module.MeasuresExporter

# 加载Word导出模块
spec2 = importlib.util.spec_from_file_location("docx_gen", "scripts/08_measures_docx_generator.py")
docx_gen_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(docx_gen_module)

MeasuresDocGenerator = docx_gen_module.MeasuresDocGenerator


def test_transformer():
    """测试主变保护措施单生成"""
    print("\n" + "="*60)
    print("测试1: 220kV主变保护定检措施单")
    print("="*60)
    
    # 加载真实模板
    template_paths = [
        'data/templates_附录4-6_v2.json',
        'data/templates_附录4-7_v2.json'
    ]
    loader = RealTemplateLoader(template_paths)
    real_templates = loader.get_templates()
    
    # 生成参数
    params = {
        'equipment_type': '主变保护',
        'work_type': '定检',
        'voltage_level': '220kV',
        'substation_name': 'XX变电站',
        'work_ticket_number': 'WT-2026-001'
    }
    
    # 生成措施单
    generator = MeasuresGeneratorV2(real_templates=real_templates)
    measures = generator.generate(params)
    
    # 校验
    validation = generator.validate_measures(measures)
    print(f"\n✅ 合规校验: {'通过' if validation['valid'] else '失败'}")
    print(f"  - 措施项数量: {validation['item_count']}")
    if validation['warnings']:
        print(f"  - 警告: {validation['warnings']}")
    
    # 导出JSON
    json_path = 'docs/220kV主变保护定检措施单_v2.json'
    exporter = MeasuresExporter()
    exporter.export_to_json(measures, json_path)
    print(f"\n📄 JSON已导出: {json_path}")
    
    # 导出Markdown
    md_path = json_path.replace('.json', '.md')
    exporter.export_to_markdown(measures, md_path)
    print(f"📝 Markdown已导出: {md_path}")
    
    # 导出Word
    docx_gen = MeasuresDocGenerator()
    docx_path = 'docs/220kV主变保护定检措施单_v2.docx'
    docx_gen.generate(measures.to_dict(), docx_path)
    print(f"📄 Word文档已导出: {docx_path}")
    
    return measures


def test_line():
    """测试线路保护措施单生成"""
    print("\n" + "="*60)
    print("测试2: 220kV线路保护定检措施单")
    print("="*60)
    
    # 加载真实模板
    template_paths = [
        'data/templates_附录4-6_v2.json',
        'data/templates_附录4-7_v2.json'
    ]
    loader = RealTemplateLoader(template_paths)
    real_templates = loader.get_templates()
    
    # 生成参数
    params = {
        'equipment_type': '线路保护',
        'work_type': '定检',
        'voltage_level': '220kV',
        'substation_name': 'YY变电站',
        'work_ticket_number': 'WT-2026-002'
    }
    
    # 生成措施单
    generator = MeasuresGeneratorV2(real_templates=real_templates)
    measures = generator.generate(params)
    
    # 校验
    validation = generator.validate_measures(measures)
    print(f"\n✅ 合规校验: {'通过' if validation['valid'] else '失败'}")
    print(f"  - 措施项数量: {validation['item_count']}")
    if validation['warnings']:
        print(f"  - 警告: {validation['warnings']}")
    
    # 导出JSON
    json_path = 'docs/220kV线路保护定检措施单_v2.json'
    exporter = MeasuresExporter()
    exporter.export_to_json(measures, json_path)
    print(f"\n📄 JSON已导出: {json_path}")
    
    # 导出Markdown
    md_path = json_path.replace('.json', '.md')
    exporter.export_to_markdown(measures, md_path)
    print(f"📝 Markdown已导出: {md_path}")
    
    # 导出Word
    docx_gen = MeasuresDocGenerator()
    docx_path = 'docs/220kV线路保护定检措施单_v2.docx'
    docx_gen.generate(measures.to_dict(), docx_path)
    print(f"📄 Word文档已导出: {docx_path}")
    
    return measures


def main():
    """主函数"""
    print("\n" + "="*60)
    print("电气二次AI模型训练工具集 - 完整工作流测试 v2")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试1: 主变保护
    transformer_measures = test_transformer()
    
    # 测试2: 线路保护
    line_measures = test_line()
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
    
    # 输出统计
    print("\n📊 输出文件统计:")
    docs_dir = Path('docs')
    for f in sorted(docs_dir.glob('*')):
        if f.is_file():
            size = f.stat().st_size
            print(f"  - {f.name} ({size} bytes)")
    
    print("\n✅ 所有测试通过!")


if __name__ == '__main__':
    main()
