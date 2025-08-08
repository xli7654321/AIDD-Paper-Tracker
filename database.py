import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from config import DATA_CONFIG


class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or f"{DATA_CONFIG['data_dir']}/papers.db"
        self.setup_logging()
        self.init_database()
    
    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建papers表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    authors TEXT,
                    abstract TEXT,
                    categories TEXT,
                    published_date TEXT,
                    url TEXT,
                    pdf_url TEXT,
                    source TEXT NOT NULL,
                    fetched_date TEXT,
                    is_relevant INTEGER DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引提高查询性能
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_id ON papers(paper_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON papers(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_date ON papers(published_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_relevant ON papers(is_relevant)")
            
            conn.commit()
            self.logger.info("数据库初始化完成")
    
    def save_paper(self, paper_data: Dict, source: str = 'arXiv') -> bool:
        """保存单篇论文到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 准备数据
                authors_json = json.dumps(paper_data.get('authors', []), ensure_ascii=False)
                categories_json = json.dumps(paper_data.get('categories', []), ensure_ascii=False)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO papers 
                    (paper_id, title, authors, abstract, categories, published_date, 
                     url, pdf_url, source, fetched_date, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    paper_data.get('id'),
                    paper_data.get('title'),
                    authors_json,
                    paper_data.get('abstract'),
                    categories_json,
                    paper_data.get('published_date'),
                    paper_data.get('url'),
                    paper_data.get('pdf_url'),
                    source,
                    paper_data.get('fetched_date'),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"保存论文失败: {e}")
            return False
    
    def save_papers_batch(self, papers_data: List[Dict], source: str = 'arXiv') -> Dict:
        """批量保存论文"""
        saved_count = 0
        updated_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for paper_data in papers_data:
                    # 检查论文是否已存在
                    cursor.execute("SELECT id FROM papers WHERE paper_id = ?", (paper_data.get('id'),))
                    exists = cursor.fetchone()
                    
                    # 准备数据
                    authors_json = json.dumps(paper_data.get('authors', []), ensure_ascii=False)
                    categories_json = json.dumps(paper_data.get('categories', []), ensure_ascii=False)
                    
                    if exists:
                        # 更新现有记录
                        cursor.execute("""
                            UPDATE papers SET 
                            title=?, authors=?, abstract=?, categories=?, published_date=?,
                            url=?, pdf_url=?, fetched_date=?, updated_at=?
                            WHERE paper_id=?
                        """, (
                            paper_data.get('title'),
                            authors_json,
                            paper_data.get('abstract'),
                            categories_json,
                            paper_data.get('published_date'),
                            paper_data.get('url'),
                            paper_data.get('pdf_url'),
                            paper_data.get('fetched_date'),
                            datetime.now().isoformat(),
                            paper_data.get('id')
                        ))
                        updated_count += 1
                    else:
                        # 插入新记录
                        cursor.execute("""
                            INSERT INTO papers 
                            (paper_id, title, authors, abstract, categories, published_date,
                             url, pdf_url, source, fetched_date, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            paper_data.get('id'),
                            paper_data.get('title'),
                            authors_json,
                            paper_data.get('abstract'),
                            categories_json,
                            paper_data.get('published_date'),
                            paper_data.get('url'),
                            paper_data.get('pdf_url'),
                            source,
                            paper_data.get('fetched_date'),
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
                        saved_count += 1
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"批量保存论文失败: {e}")
        
        return {'saved': saved_count, 'updated': updated_count}
    
    def get_papers(self, source: str = None, limit: int = None) -> List[Dict]:
        """获取论文列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM papers"
                params = []
                
                if source:
                    query += " WHERE source = ?"
                    params.append(source)
                
                query += " ORDER BY paper_id DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # 获取列名
                columns = [description[0] for description in cursor.description]
                
                # 转换为字典列表
                papers = []
                for row in rows:
                    paper = dict(zip(columns, row))
                    
                    # 解析JSON字段
                    if paper['authors']:
                        paper['authors'] = json.loads(paper['authors'])
                    if paper['categories']:
                        paper['categories'] = json.loads(paper['categories'])
                    
                    # 为了保持与现有代码的兼容性，将paper_id映射为id
                    paper['id'] = paper['paper_id']
                    
                    papers.append(paper)
                
                return papers
                
        except Exception as e:
            self.logger.error(f"获取论文列表失败: {e}")
            return []
    
    def update_paper_relevance(self, paper_id: str, is_relevant: Optional[bool]) -> bool:
        """更新论文相关性标记"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 将布尔值转换为整数，None保持为NULL
                relevance_value = None if is_relevant is None else (1 if is_relevant else 0)
                
                cursor.execute("""
                    UPDATE papers SET is_relevant = ?, updated_at = ?
                    WHERE paper_id = ?
                """, (relevance_value, datetime.now().isoformat(), paper_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"更新论文 {paper_id} 相关性标记为 {is_relevant}")
                    return True
                else:
                    self.logger.warning(f"未找到论文 {paper_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"更新论文相关性失败: {e}")
            return False
    
    def get_paper_stats(self, source: str = None) -> Dict:
        """获取论文统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                where_clause = "WHERE source = ?" if source else ""
                params = [source] if source else []
                
                # 总数
                cursor.execute(f"SELECT COUNT(*) FROM papers {where_clause}", params)
                total_count = cursor.fetchone()[0]
                
                # 相关论文数
                cursor.execute(f"SELECT COUNT(*) FROM papers {where_clause} {'AND' if where_clause else 'WHERE'} is_relevant = 1", params)
                relevant_count = cursor.fetchone()[0]
                
                # 不相关论文数
                cursor.execute(f"SELECT COUNT(*) FROM papers {where_clause} {'AND' if where_clause else 'WHERE'} is_relevant = 0", params)
                irrelevant_count = cursor.fetchone()[0]
                
                # 未标记论文数
                cursor.execute(f"SELECT COUNT(*) FROM papers {where_clause} {'AND' if where_clause else 'WHERE'} is_relevant IS NULL", params)
                untagged_count = cursor.fetchone()[0]
                
                return {
                    'total': total_count,
                    'relevant': relevant_count,
                    'irrelevant': irrelevant_count,
                    'untagged': untagged_count
                }
                
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {'total': 0, 'relevant': 0, 'irrelevant': 0, 'untagged': 0}
    
    def migrate_from_json(self, json_file_path: str, source: str = 'arXiv') -> Dict:
        """从JSON文件迁移数据到数据库"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 转换为论文列表
            papers_list = list(json_data.values()) if isinstance(json_data, dict) else json_data
            
            # 批量保存
            result = self.save_papers_batch(papers_list, source)
            
            self.logger.info(f"从 {json_file_path} 迁移数据完成: 新增 {result['saved']} 篇，更新 {result['updated']} 篇")
            return result
            
        except Exception as e:
            self.logger.error(f"从JSON迁移数据失败: {e}")
            return {'saved': 0, 'updated': 0}
    
    def delete_paper(self, paper_id: str) -> bool:
        """删除单篇论文"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM papers WHERE paper_id = ?", (paper_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"删除论文 {paper_id}")
                    return True
                else:
                    self.logger.warning(f"未找到论文 {paper_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"删除论文失败: {e}")
            return False
    
    def delete_papers_by_source(self, source: str) -> int:
        """删除指定数据源的所有论文"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM papers WHERE source = ?", (source,))
                conn.commit()
                
                deleted_count = cursor.rowcount
                self.logger.info(f"删除了 {deleted_count} 篇 {source} 论文")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"删除论文失败: {e}")
            return 0
    
    def delete_all_papers(self) -> int:
        """删除所有论文"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM papers")
                conn.commit()
                
                deleted_count = cursor.rowcount
                self.logger.info(f"删除了所有 {deleted_count} 篇论文")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"删除所有论文失败: {e}")
            return 0
    
    def delete_papers_by_date_range(self, start_date: str, end_date: str, source: str = None) -> int:
        """删除指定日期范围内的论文"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if source:
                    cursor.execute("""
                        DELETE FROM papers 
                        WHERE published_date BETWEEN ? AND ? AND source = ?
                    """, (start_date, end_date, source))
                else:
                    cursor.execute("""
                        DELETE FROM papers 
                        WHERE published_date BETWEEN ? AND ?
                    """, (start_date, end_date))
                
                conn.commit()
                
                deleted_count = cursor.rowcount
                self.logger.info(f"删除了日期范围 {start_date} 至 {end_date} 内的 {deleted_count} 篇论文")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"删除指定日期范围论文失败: {e}")
            return 0
    
    def reset_auto_increment(self) -> bool:
        """重置自增ID序列"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 重置papers表的自增序列
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='papers'")
                conn.commit()
                
                self.logger.info("已重置自增ID序列")
                return True
                
        except Exception as e:
            self.logger.error(f"重置自增ID失败: {e}")
            return False