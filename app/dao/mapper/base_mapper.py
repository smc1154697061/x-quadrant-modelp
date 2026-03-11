from typing import Type, List, Optional, Dict, Any
from common import log_
from common.db_utils import get_db_connection
from .base_entity import BaseEntity


class BaseMapper:
    entity_class: Type[BaseEntity] = None
    table_name: str = None
    primary_key: str = 'id'
    
    def __init__(self):
        if not self.entity_class or not self.table_name:
            raise ValueError(f"{self.__class__.__name__} 必须定义 entity_class 和 table_name")
    
    def select_by_id(self, id_value) -> Optional[BaseEntity]:
        sql = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = %s"
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, (id_value,))
                    columns = [col[0] for col in cursor.description]
                    result = cursor.fetchone()
                    if not result:
                        return None
                    data = dict(zip(columns, result))
                    return self.entity_class.from_dict(data)
                except Exception as e:
                    log_.error(f"根据ID查询失败: {str(e)}")
                    return None
    
    def select_list(self, conditions: Dict[str, Any] = None, 
                   order_by: str = None, 
                   limit: int = None, 
                   offset: int = 0) -> List[BaseEntity]:
        sql = f"SELECT * FROM {self.table_name}"
        params = []
        
        if conditions:
            where_clauses = []
            for field, value in conditions.items():
                where_clauses.append(f"{field} = %s")
                params.append(value)
            sql += " WHERE " + " AND ".join(where_clauses)
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit is not None:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, params if params else None)
                    columns = [col[0] for col in cursor.description]
                    results = cursor.fetchall()
                    data_list = [dict(zip(columns, row)) for row in results]
                    return self.entity_class.from_dict_list(data_list)
                except Exception as e:
                    log_.error(f"条件查询失败: {str(e)}")
                    return []
    
    def select_one(self, conditions: Dict[str, Any]) -> Optional[BaseEntity]:
        results = self.select_list(conditions, limit=1)
        return results[0] if results else None
    
    def select_all(self, order_by: str = None, limit: int = 100, offset: int = 0) -> List[BaseEntity]:
        return self.select_list(conditions=None, order_by=order_by, limit=limit, offset=offset)
    
    def count(self, conditions: Dict[str, Any] = None) -> int:
        sql = f"SELECT COUNT(*) FROM {self.table_name}"
        params = []
        
        if conditions:
            where_clauses = []
            for field, value in conditions.items():
                where_clauses.append(f"{field} = %s")
                params.append(value)
            sql += " WHERE " + " AND ".join(where_clauses)
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, params if params else None)
                    result = cursor.fetchone()
                    return result[0] if result else 0
                except Exception as e:
                    log_.error(f"统计记录数失败: {str(e)}")
                    return 0
    
    def insert(self, entity: BaseEntity) -> Optional[int]:
        data = entity.to_dict()
        if self.primary_key in data and data[self.primary_key] is None:
            del data[self.primary_key]
        
        fields = list(data.keys())
        placeholders = ['%s'] * len(fields)
        values = [data[field] for field in fields]
        
        sql = f"INSERT INTO {self.table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)}) RETURNING {self.primary_key}"
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, values)
                    result = cursor.fetchone()
                    return result[0] if result else None
                except Exception as e:
                    log_.error(f"插入记录失败: {str(e)}")
                    raise
    
    def insert_batch(self, entities: List[BaseEntity]) -> int:
        if not entities:
            return 0
        
        data = entities[0].to_dict()
        if self.primary_key in data and data[self.primary_key] is None:
            del data[self.primary_key]
        
        fields = list(data.keys())
        placeholders = ['%s'] * len(fields)
        
        sql = f"INSERT INTO {self.table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    values_list = []
                    for entity in entities:
                        entity_data = entity.to_dict()
                        if self.primary_key in entity_data and entity_data[self.primary_key] is None:
                            del entity_data[self.primary_key]
                        values_list.append([entity_data[field] for field in fields])
                    
                    cursor.executemany(sql, values_list)
                    return cursor.rowcount
                except Exception as e:
                    log_.error(f"批量插入失败: {str(e)}")
                    raise
    
    def update_by_id(self, entity: BaseEntity) -> int:
        data = entity.to_dict()
        id_value = data.get(self.primary_key)
        
        if id_value is None:
            raise ValueError(f"实体对象必须包含主键字段: {self.primary_key}")
        
        del data[self.primary_key]
        
        if not data:
            return 0
        
        set_clauses = [f"{field} = %s" for field in data.keys()]
        values = list(data.values())
        values.append(id_value)
        
        sql = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE {self.primary_key} = %s"
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, values)
                    return cursor.rowcount
                except Exception as e:
                    log_.error(f"更新记录失败: {str(e)}")
                    raise
    
    def update(self, data: Dict[str, Any], conditions: Dict[str, Any]) -> int:
        if not data or not conditions:
            return 0
        
        set_clauses = [f"{field} = %s" for field in data.keys()]
        where_clauses = [f"{field} = %s" for field in conditions.keys()]
        
        values = list(data.values()) + list(conditions.values())
        
        sql = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, values)
                    return cursor.rowcount
                except Exception as e:
                    log_.error(f"条件更新失败: {str(e)}")
                    raise
    
    def delete_by_id(self, id_value) -> int:
        sql = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = %s"
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, (id_value,))
                    return cursor.rowcount
                except Exception as e:
                    log_.error(f"删除记录失败: {str(e)}")
                    raise
    
    def delete(self, conditions: Dict[str, Any]) -> int:
        if not conditions:
            raise ValueError("删除操作必须指定条件")
        
        where_clauses = [f"{field} = %s" for field in conditions.keys()]
        values = list(conditions.values())
        
        sql = f"DELETE FROM {self.table_name} WHERE {' AND '.join(where_clauses)}"
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, values)
                    return cursor.rowcount
                except Exception as e:
                    log_.error(f"条件删除失败: {str(e)}")
                    raise
