#!/usr/bin/env python3
"""
二次作业AI工具集 - 完整工作流集成脚本
提供端到端流程：解析 → 抽取 → 图谱 → 生成 → 导出
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List

# 添加scripts目录到路径
_scripts_dir = Path(__file__).parent
sys.path.insert(0, str(_scripts_dir))

# 导入模块（使用模块名而非文件名）
import importlib.util

def _load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, _scripts_dir / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_parser_mod = _load_module('data_parsing', '01_data_parsing.py')
_extractor_mod = _load_module('knowledge_extraction', '02_knowledge_extraction.py')
_graph_mod = _load_module('knowledge_graph_enhanced', '03_knowledge_graph_enhanced.py')
_measures_gen_mod = _load_module('measures_generation', '05_measures_generation.py')
_doc_gen_mod = _load_module('measures_docx_generator', '08_measures_docx_generator.py')

SecondaryDocParser = _parser_mod.SecondaryDocParser
KnowledgeExtractor = _extractor_mod.KnowledgeExtractor
EnhancedKnowledgeGraph = _graph_mod.EnhancedKnowledgeGraph
MeasuresGenerator = _measures_gen_mod.MeasuresGenerator
MeasuresDocGenerator = _doc_gen_mod.MeasuresDocGenerator


class SecondaryAIWorkflow:
    """二次作业AI完整工作流"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.parser = SecondaryDocParser()
        self.extractor = KnowledgeExtractor()
        self.graph_builder = EnhancedKnowledgeGraph()
        self.measures_gen = MeasuresGenerator()
        self.doc_gen = MeasuresDocGenerator()
        
        # 工作目录
        self.work_dir = Path(self.config.get('work_dir', str(Path(__file__).parent.parent)))
        self.scripts_dir = Path(__file__).parent
        self.data_dir = self.work_dir / 'data'
        self.docs_dir = self.work_dir / 'docs'
        self.examples_dir = self.work_dir / 'examples'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.examples_dir.mkdir(parents=True, exist_ok=True)
    
    def run_full_pipeline(self, 
                          doc_path: str, 
                          output_prefix: str = 'pipeline_output',
                          skip_steps: List[str] = None) -> Dict[str, str]:
        """运行完整流水线"""
        skip_steps = skip_steps or []
        results = {}
        
        print("=" * 60)
        print("二次作业AI工具集 - 完整工作流")
        print("=" * 60)
        
        # 步骤1: 文档解析
        if 'parse' not in skip_steps:
            print("\n[步骤1/5] 文档解析...")
            parsed_path = self.data_dir / f"{output_prefix}_parsed.json"
            if not parsed_path.exists():
                result = self.parser.parse_docx(doc_path)
                self.parser.save_results(str(parsed_path), 'json')
                results['parsed'] = str(parsed_path)
                print(f"  ✓ 解析完成: {len(result['sections'])} 章节, {len(result['tables'])} 表格")
            else:
                print(f"  - 使用已有解析结果: {parsed_path}")
                results['parsed'] = str(parsed_path)
        
        # 步骤2: 知识抽取
        if 'extract' not in skip_steps:
            print("\n[步骤2/5] 知识抽取...")
            extract_path = self.data_dir / f"{output_prefix}_knowledge.json"
            if not extract_path.exists():
                # 读取解析结果
                with open(results.get('parsed', ''), 'r', encoding='utf-8') as f:
                    parsed_data = json.load(f)
                
                # 抽取知识
                text = json.dumps(parsed_data, ensure_ascii=False)
                self.extractor.extract_from_text(text)
                self.extractor.save_results(str(extract_path))
                results['knowledge'] = str(extract_path)
                print(f"  ✓ 抽取完成: {self.extractor.get_results()['metadata']}")
            else:
                print(f"  - 使用已有抽取结果: {extract_path}")
                results['knowledge'] = str(extract_path)
        
        # 步骤3: 知识图谱构建
        if 'graph' not in skip_steps:
            print("\n[步骤3/5] 知识图谱构建...")
            graph_path = self.data_dir / f"{output_prefix}_graph.json"
            if not graph_path.exists():
                with open(results.get('knowledge', ''), 'r', encoding='utf-8') as f:
                    knowledge_data = json.load(f)
                
                self.graph_builder.build_from_knowledge(knowledge_data)
                self.graph_builder.export_to_json(str(graph_path))
                results['graph'] = str(graph_path)
                stats = self.graph_builder.get_stats()
                print(f"  ✓ 图谱构建完成: {stats['node_count']} 节点, {stats['edge_count']} 边")
            else:
                print(f"  - 使用已有图谱结果: {graph_path}")
                results['graph'] = str(graph_path)
        
        # 步骤4: 措施单生成
        if 'generate' not in skip_steps:
            print("\n[步骤4/5] 措施单智能生成...")
            # 这里使用示例输入文件
            example_path = self.work_dir / 'examples' / 'example_220kV_transformer.json'
            if example_path.exists():
                with open(example_path, 'r', encoding='utf-8') as f:
                    params = json.load(f)
                
                measures = self.measures_gen.generate(params)
                measures_path = self.data_dir / f"{output_prefix}_measures.json"
                with open(measures_path, 'w', encoding='utf-8') as f:
                    json.dump(measures.to_dict(), f, ensure_ascii=False, indent=2)
                results['measures'] = str(measures_path)
                print(f"  ✓ 措施单生成完成: {len(measures.items)} 条措施项")
        
        # 步骤5: Word文档导出
        if 'export' not in skip_steps:
            print("\n[步骤5/5] Word文档导出...")
            measures_path = results.get('measures', self.data_dir / f"{output_prefix}_measures.json")
            if measures_path.exists():
                with open(measures_path, 'r', encoding='utf-8') as f:
                    measures_data = json.load(f)
                
                doc_path = self.docs_dir / f"{output_prefix}_措施单.docx"
                self.doc_gen.generate(measures_data, str(doc_path))
                results['docx'] = str(doc_path)
                print(f"  ✓ Word文档已生成: {doc_path}")
        
        print("\n" + "=" * 60)
        print("✓ 完整工作流执行完成")
        print("=" * 60)
        
        return results
    
    def generate_measures_from_params(self, 
                                      params: Dict[str, Any],
                                      output_dir: str = None) -> Dict[str, str]:
        """从参数直接生成措施单"""
        output_dir = Path(output_dir) if output_dir else self.docs_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成措施单数据
        measures = self.measures_gen.generate(params)
        
        # 保存JSON
        json_path = output_dir / f"{params.get('station_name', 'measures')}_措施单.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(measures.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 生成Word
        docx_path = output_dir / f"{params.get('station_name', 'measures')}_措施单.docx"
        self.doc_gen.generate(measures.to_dict(), str(docx_path))
        
        return {
            'json': str(json_path),
            'docx': str(docx_path)
        }


def main():
    parser = argparse.ArgumentParser(description='二次作业AI工具集 - 完整工作流')
    parser.add_argument('--doc', '-d', help='输入的Word文档路径')
    parser.add_argument('--params', '-p', help='输入参数JSON文件路径（用于生成措施单）')
    parser.add_argument('--output-prefix', '-o', default='output', help='输出文件前缀')
    parser.add_argument('--skip', '-s', nargs='*', help='跳过的步骤: parse, extract, graph, generate, export')
    parser.add_argument('--mode', '-m', choices=['pipeline', 'generate'], default='pipeline',
                        help='运行模式: pipeline(完整流程) 或 generate(仅生成措施单)')
    
    args = parser.parse_args()
    
    # 创建配置
    config = {
        'work_dir': str(Path(__file__).parent)
    }
    
    workflow = SecondaryAIWorkflow(config)
    
    if args.mode == 'generate' and args.params:
        # 仅生成模式
        params = json.load(open(args.params, 'r', encoding='utf-8'))
        output_dir = Path(args.output_prefix).parent if Path(args.output_prefix).parent != Path('.') else workflow.docs_dir
        
        results = workflow.generate_measures_from_params(params, str(output_dir))
        print(f"\n✓ 措施单生成完成:")
        for k, v in results.items():
            print(f"  - {k}: {v}")
    else:
        # 完整流水线模式
        if not args.doc:
            # 使用默认的实施细则文档
            args.doc = "/Coze/Drive/红剑/converted_docs/广东电网有限责任公司厂站二次设备及其二次回路工作安全技术措施单实施细则（2025版）.docx"
        
        results = workflow.run_full_pipeline(
            args.doc,
            args.output_prefix,
            args.skip
        )
        
        print(f"\n📁 输出文件:")
        for k, v in results.items():
            print(f"  - {k}: {v}")


if __name__ == '__main__':
    main()
