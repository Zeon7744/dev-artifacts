#!/usr/bin/env python3
"""
二次作业AI工具集 - FastAPI服务
提供REST API接口，方便开发者集成
"""

import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# 添加scripts目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent))

import importlib.util

def _load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 加载模块
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

# 创建工作目录
WORK_DIR = Path(__file__).parent
DATA_DIR = WORK_DIR / 'data'
DOCS_DIR = WORK_DIR / 'docs'
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# 创建FastAPI应用
app = FastAPI(
    title="二次作业AI工具集",
    description="广东电网二次作业标准文档解析、知识抽取、知识图谱构建、措施单智能生成API",
    version="1.0.0"
)


# ===== 数据模型 =====

class MeasuresParams(BaseModel):
    """措施单生成参数"""
    station_name: str  # 变电站名称
    voltage_level: str  # 电压等级
    equipment_type: str  # 设备类型
    work_type: str  # 工作类型
    work_content: str  # 工作内容
    safety_requirements: List[str] = []  # 安全要求


class ParseResult(BaseModel):
    """解析结果"""
    section_count: int
    table_count: int
    knowledge_element_count: int
    output_file: str


class KnowledgeStats(BaseModel):
    """知识抽取统计"""
    terms_count: int
    rules_count: int
    procedures_count: int
    action_distribution: Dict[str, int]


class GraphStats(BaseModel):
    """知识图谱统计"""
    node_count: int
    edge_count: int
    node_type_distribution: Dict[str, int]
    edge_type_distribution: Dict[str, int]


class MeasuresResult(BaseModel):
    """措施单生成结果"""
    item_count: int
    categories: Dict[str, int]
    output_json: str
    output_docx: str


# ===== API端点 =====

@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "二次作业AI工具集 API",
        "version": "1.0.0",
        "endpoints": {
            "parse": "POST /api/parse - 解析文档",
            "extract": "POST /api/extract - 抽取知识",
            "graph": "POST /api/graph - 构建知识图谱",
            "generate": "POST /api/generate - 生成措施单",
            "download": "GET /api/download/{file} - 下载文件"
        }
    }


@app.post("/api/parse", response_model=ParseResult)
async def parse_document(file: UploadFile = File(...)):
    """解析Word文档"""
    try:
        # 保存上传文件
        input_path = DATA_DIR / f"upload_{file.filename}"
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 解析文档
        parser = SecondaryDocParser()
        result = parser.parse_docx(str(input_path))
        output_path = DATA_DIR / f"parsed_{file.stem}.json"
        parser.save_results(str(output_path), 'json')
        
        return ParseResult(
            section_count=len(result['sections']),
            table_count=len(result['tables']),
            knowledge_element_count=len(result['knowledge_elements']),
            output_file=str(output_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract", response_model=KnowledgeStats)
async def extract_knowledge(parsed_file: str = None):
    """从解析结果中抽取知识"""
    try:
        if not parsed_file:
            # 使用最新的解析结果
            parsed_files = list(DATA_DIR.glob("parsed_*.json"))
            if not parsed_files:
                raise HTTPException(status_code=400, detail="请先上传并解析文档")
            parsed_file = str(sorted(parsed_files)[-1])
        
        # 读取解析结果
        with open(parsed_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        # 抽取知识
        extractor = KnowledgeExtractor()
        text = json.dumps(parsed_data, ensure_ascii=False)
        extractor.extract_from_text(text)
        
        results = extractor.get_results()
        output_path = DATA_DIR / "knowledge_extracted.json"
        extractor.save_results(str(output_path))
        
        return KnowledgeStats(
            terms_count=results['metadata']['terms_count'],
            rules_count=results['metadata']['rules_count'],
            procedures_count=results['metadata']['procedures_count'],
            action_distribution=results['statistics']['action_distribution']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph", response_model=GraphStats)
async def build_knowledge_graph(knowledge_file: str = None):
    """构建知识图谱"""
    try:
        if not knowledge_file:
            # 使用最新抽取结果
            knowledge_files = list(DATA_DIR.glob("knowledge_*.json"))
            if not knowledge_files:
                raise HTTPException(status_code=400, detail="请先抽取知识")
            knowledge_file = str(sorted(knowledge_files)[-1])
        
        # 读取知识数据
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)
        
        # 构建图谱
        builder = EnhancedKnowledgeGraph()
        builder.build_from_knowledge(knowledge_data)
        
        output_path = DATA_DIR / "knowledge_graph.json"
        builder.export_to_json(str(output_path))
        
        stats = builder.get_stats()
        
        return GraphStats(
            node_count=stats['node_count'],
            edge_count=stats['edge_count'],
            node_type_distribution=stats['node_type_distribution'],
            edge_type_distribution=stats['edge_type_distribution']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate", response_model=MeasuresResult)
async def generate_measures(params: MeasuresParams):
    """生成二次措施单"""
    try:
        # 构建生成参数
        generate_params = {
            'station_name': params.station_name,
            'voltage_level': params.voltage_level,
            'equipment_type': params.equipment_type,
            'work_type': params.work_type,
            'work_content': params.work_content,
            'safety_requirements': params.safety_requirements
        }
        
        # 生成措施单
        generator = MeasuresGenerator()
        measures = generator.generate(generate_params)
        
        # 导出JSON
        json_path = DOCS_DIR / f"{params.station_name}_措施单.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(measures.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 导出Word
        doc_path = DOCS_DIR / f"{params.station_name}_措施单.docx"
        doc_gen = MeasuresDocGenerator()
        doc_gen.generate(measures.to_dict(), str(doc_path))
        
        # 统计类别
        categories = {}
        for item in measures.items:
            cat = item.get('category', '其他')
            categories[cat] = categories.get(cat, 0) + 1
        
        return MeasuresResult(
            item_count=len(measures.items),
            categories=categories,
            output_json=str(json_path),
            output_docx=str(doc_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载生成的文件"""
    file_path = DOCS_DIR / filename
    if not file_path.exists():
        file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(str(file_path), filename=filename)


@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    parsed_files = list(DATA_DIR.glob("parsed_*.json"))
    knowledge_files = list(DATA_DIR.glob("knowledge_*.json"))
    graph_files = list(DATA_DIR.glob("knowledge_graph*.json"))
    doc_files = list(DOCS_DIR.glob("*.docx"))
    
    return {
        "parsed_documents": len(parsed_files),
        "knowledge_entries": len(knowledge_files),
        "knowledge_graphs": len(graph_files),
        "generated_docs": len(doc_files),
        "work_dir": str(WORK_DIR)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
