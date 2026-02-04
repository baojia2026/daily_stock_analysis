"""
替代 json-replier 的功能
提供JSON数据处理和验证
"""
import json
import jsonschema
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json
import logging

logger = logging.getLogger(__name__)

@dataclass_json
@dataclass
class JsonResponse:
    """标准JSON响应结构"""
    success: bool
    data: Optional[Any] = None
    message: str = ""
    error_code: Optional[int] = None
    timestamp: Optional[str] = None
    
    @classmethod
    def create_success(cls, data: Any = None, message: str = "操作成功"):
        """创建成功响应"""
        import datetime
        return cls(
            success=True,
            data=data,
            message=message,
            timestamp=datetime.datetime.now().isoformat()
        )
    
    @classmethod
    def create_error(cls, message: str, error_code: int = 500, data: Any = None):
        """创建错误响应"""
        import datetime
        return cls(
            success=False,
            data=data,
            message=message,
            error_code=error_code,
            timestamp=datetime.datetime.now().isoformat()
        )

class JsonValidator:
    """JSON数据验证器"""
    
    # 常用schema定义
    STOCK_DATA_SCHEMA = {
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "open": {"type": "number"},
                        "high": {"type": "number"},
                        "low": {"type": "number"},
                        "close": {"type": "number"},
                        "volume": {"type": "number"}
                    },
                    "required": ["date", "close"]
                }
            }
        },
        "required": ["symbol", "data"]
    }
    
    @staticmethod
    def validate(data: Dict, schema: Dict) -> bool:
        """验证JSON数据是否符合schema"""
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"JSON验证失败: {e}")
            return False
    
    @staticmethod
    def fix_json(json_str: str) -> str:
        """修复不规范的JSON字符串"""
        import json_fix
        try:
            data = json.loads(json_str)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            json_str = json_str.strip()
            if not json_str.startswith('{'):
                json_str = '{' + json_str
            if not json_str.endswith('}'):
                json_str = json_str + '}'
            return json_str

class JsonReplacer:
    """JSON数据处理器（替代json-replier）"""
    
    @staticmethod
    def pretty_print(data: Union[Dict, List, str]) -> str:
        """美化打印JSON"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return data
        
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    @staticmethod
    def extract_fields(data: Dict, fields: List[str]) -> Dict:
        """提取指定字段"""
        result = {}
        for field in fields:
            if field in data:
                result[field] = data[field]
            else:
                keys = field.split('.')
                current = data
                for key in keys:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break
                if current is not None:
                    result[field] = current
        return result
    
    @staticmethod
    def merge_json(*json_objects: Dict) -> Dict:
        """合并多个JSON对象"""
        result = {}
        for obj in json_objects:
            if isinstance(obj, dict):
                JsonReplacer._deep_merge(result, obj)
        return result
    
    @staticmethod
    def _deep_merge(base: Dict, update: Dict):
        """深度合并字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                JsonReplacer._deep_merge(base[key], value)
            else:
                base[key] = value

if __name__ == "__main__":
    response = JsonResponse.create_success(
        data={"stock": "AAPL", "price": 175.25},
        message="数据获取成功"
    )
    
    print("标准响应:")
    print(response.to_json(indent=2))
    
    validator = JsonValidator()
    sample_data = {
        "symbol": "000001",
        "data": [
            {"date": "2023-01-01", "close": 12.5},
            {"date": "2023-01-02", "close": 12.8}
        ]
    }
    
    is_valid = validator.validate(sample_data, JsonValidator.STOCK_DATA_SCHEMA)
    print(f"\n数据验证结果: {is_valid}")
    
    pretty_json = JsonReplacer.pretty_print(sample_data)
    print(f"\n美化后的JSON:\n{pretty_json}")
