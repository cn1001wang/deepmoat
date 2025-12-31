import json
from typing import List, Tuple

def snake_to_camel(name: str) -> str:
    """蛇形转驼峰"""
    parts = name.split('_')
    return parts[0] + ''.join(x.title() for x in parts[1:])

def get_sa_type(type_str: str) -> str:
    """获取SQLAlchemy类型"""
    types = {'str': 'String(100)', 'float': 'Float', 'int': 'Integer'}
    return types.get(type_str.lower(), 'String(100)')

def get_py_type(type_str: str) -> str:
    """获取Python类型"""
    types = {'str': 'str', 'float': 'float', 'int': 'int'}
    return types.get(type_str.lower(), 'str')

def generate_model(table_name: str, fields: List[List], primary_keys: List[str]) -> str:
    """生成Model"""
    class_name = ''.join(w.capitalize() for w in table_name.split('_'))
    
    code = f'''from sqlalchemy import Column, String, Float, Integer
from app.db.session import Base

class {class_name}(Base):
    __tablename__ = "{table_name}"

'''
    
    for name, ftype, desc in fields:
        sa_type = get_sa_type(ftype)
        if name in primary_keys:
            code += f'    {name} = Column({sa_type}, primary_key=True, index=True, comment="{desc}")  # {desc}\n'
        else:
            code += f'    {name} = Column({sa_type}, comment="{desc}")  # {desc}\n'
    
    return code

def generate_schema(table_name: str, fields: List[List], primary_keys: List[str]) -> str:
    """生成Schema"""
    class_name = ''.join(w.capitalize() for w in table_name.split('_'))
    
    code = f'''from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class {class_name}Read(BaseSchema):
'''
    
    for name, ftype, desc in fields:
        py_type = get_py_type(ftype)
        camel = snake_to_camel(name)
        
        if name in primary_keys:
            if camel != name:
                code += f'    {name}: {py_type} = Field(..., alias="{camel}")  # {desc}\n'
            else:
                code += f'    {name}: {py_type}  # {desc}\n'
        else:
            if camel != name:
                code += f'    {name}: Optional[{py_type}] = Field(None, alias="{camel}")  # {desc}\n'
            else:
                code += f'    {name}: Optional[{py_type}] = None  # {desc}\n'
    
    return code

def main():
    print("=" * 50)
    print("Model & Schema 生成器")
    print("=" * 50)
    
    table_name = input("\n表名: ").strip()
    
    print("\n粘贴字段JSON数组:")
    json_str = input().strip()
    
    try:
        fields = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return
    
    print("\n主键（逗号分隔，默认第一个字段）:")
    pk_input = input().strip()
    primary_keys = [pk.strip() for pk in pk_input.split(',')] if pk_input else [fields[0][0]]
    
    model_code = generate_model(table_name, fields, primary_keys)
    schema_code = generate_schema(table_name, fields, primary_keys)
    
    with open(f"{table_name}_model.py", 'w', encoding='utf-8') as f:
        f.write(model_code)
    
    with open(f"{table_name}_schema.py", 'w', encoding='utf-8') as f:
        f.write(schema_code)
    
    print(f"\n✓ 已生成: {table_name}_model.py 和 {table_name}_schema.py")
    print("\n" + "=" * 50)
    print(model_code)
    print("=" * 50)
    print(schema_code)

if __name__ == "__main__":
    main()
# ```

# **使用示例**:
# ```
# 表名: income

# 粘贴字段JSON数组:
# [["ts_code","str","Y","TS代码"],["ann_date","str","Y","公告日期"],["end_date","str","Y","报告期"],["eps","float","Y","基本每股收益"]]

# 主键（逗号分隔，默认第一个字段）:
# ts_code,end_date