import os
import json
import logging
from config import DATA_CONFIG, LOGGING_CONFIG
from database import DatabaseManager


class DataProcessor:
    def __init__(self):
        self.setup_logging()
        self.db_manager = DatabaseManager()
        self.papers_data = {}
        self.load_data()
        
        # 执行数据迁移（如果需要）
        self._migrate_json_to_db_if_needed()
    
    def setup_logging(self):
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG['level']),
            format=LOGGING_CONFIG['format'],
            handlers=[
                logging.FileHandler(LOGGING_CONFIG['file'], encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_data(self, source: str = None):
        """从数据库加载论文数据"""
        try:
            papers_list = self.db_manager.get_papers(source=source)
            
            # 转换为字典格式以保持与现有代码的兼容性
            self.papers_data = {}
            for paper in papers_list:
                self.papers_data[paper['id']] = paper
            
            self.logger.info(f"从数据库加载了 {len(self.papers_data)} 篇论文数据")
            
        except Exception as e:
            self.logger.error(f"从数据库加载论文数据失败: {e}")
            self.papers_data = {}
    
    def save_papers_to_db(self, papers_data: list, source: str = 'arXiv'):
        """保存论文数据到数据库"""
        try:
            result = self.db_manager.save_papers_batch(papers_data, source)
            self.logger.info(f"保存论文到数据库: 新增 {result['saved']} 篇，更新 {result['updated']} 篇")
            return result
        except Exception as e:
            self.logger.error(f"保存论文到数据库失败: {e}")
            return {'saved': 0, 'updated': 0}
    
    def update_paper_relevance(self, paper_id: str, is_relevant: bool = None):
        """更新论文相关性标记"""
        success = self.db_manager.update_paper_relevance(paper_id, is_relevant)
        if success:
            # 同时更新内存中的数据
            if paper_id in self.papers_data:
                self.papers_data[paper_id]['is_relevant'] = is_relevant
        return success
    
    def get_paper_stats(self, source: str = None):
        """获取论文统计信息"""
        return self.db_manager.get_paper_stats(source)
    
    def delete_paper(self, paper_id: str):
        """删除论文"""
        success = self.db_manager.delete_paper(paper_id)
        if success:
            # 从内存中移除
            if paper_id in self.papers_data:
                del self.papers_data[paper_id]
        return success
    
    def delete_papers_by_source(self, source: str):
        """删除指定数据源的所有论文"""
        deleted_count = self.db_manager.delete_papers_by_source(source)
        if deleted_count > 0:
            # 重新加载数据
            self.load_data()
        return deleted_count
    
    def _migrate_json_to_db_if_needed(self):
        """如果需要，从JSON文件迁移数据到数据库"""
        # arXiv迁移
        papers_path = os.path.join(DATA_CONFIG['data_dir'], DATA_CONFIG['papers_file'])
        migration_flag_path = os.path.join(DATA_CONFIG['data_dir'], '.migrated')
        
        # 检查是否已经迁移过
        if not os.path.exists(migration_flag_path):
            if os.path.exists(papers_path):
                try:
                    self.logger.info("开始从arXiv JSON文件迁移数据到数据库...")
                    result = self.db_manager.migrate_from_json(papers_path, 'arXiv')
                    
                    # 重新加载数据
                    self.load_data()
                    
                    # 可选：备份原JSON文件
                    backup_path = papers_path + '.backup'
                    if not os.path.exists(backup_path):
                        import shutil
                        shutil.copy2(papers_path, backup_path)
                        self.logger.info(f"原JSON文件已备份至: {backup_path}")
                    
                    self.logger.info(f"arXiv数据迁移完成: 新增 {result['saved']} 篇，更新 {result['updated']} 篇")
                    
                except Exception as e:
                    self.logger.error(f"arXiv数据迁移失败: {e}")
            
            # 创建迁移标记文件
            with open(migration_flag_path, 'w') as f:
                f.write('migrated')
        
    
    def _load_papers_from_json(self):
        """从JSON文件加载论文数据（向后兼容）"""
        papers_path = os.path.join(DATA_CONFIG['data_dir'], DATA_CONFIG['papers_file'])
        if os.path.exists(papers_path):
            try:
                with open(papers_path, 'r', encoding='utf-8') as f:
                    self.papers_data = json.load(f)
                self.logger.info(f"从JSON文件加载了 {len(self.papers_data)} 篇论文数据")
            except Exception as e:
                self.logger.error(f"加载JSON论文数据失败: {e}")
                self.papers_data = {}


if __name__ == '__main__':
    processor = DataProcessor()
    print(f"论文总数: {len(processor.papers_data)}")