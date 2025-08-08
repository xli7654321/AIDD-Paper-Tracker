import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from config import SEARCH_CONFIG, DATA_CONFIG, LOGGING_CONFIG
from database import DatabaseManager


class BioRxivFetcher:
    def __init__(self):
        self.setup_logging()
        self.setup_data_dir()
        self.db_manager = DatabaseManager()
        self.papers_cache = {}
        self.load_existing_papers()
        
        # bioRxiv supported categories
        self.supported_categories = [
            'biochemistry',
            'bioinformatics', 
            'biophysics',
            'synthetic biology'
        ]
    
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
    
    def setup_data_dir(self):
        os.makedirs(DATA_CONFIG['data_dir'], exist_ok=True)
    
    def load_existing_papers(self):
        """从数据库加载已存在的论文到缓存"""
        try:
            papers_list = self.db_manager.get_papers(source='bioRxiv')
            self.papers_cache = {}
            for paper in papers_list:
                self.papers_cache[paper['id']] = paper
            self.logger.info(f"从数据库加载了 {len(self.papers_cache)} 篇已存在的bioRxiv论文")
        except Exception as e:
            self.logger.error(f"从数据库加载已存在论文失败: {e}")
            self.papers_cache = {}
    
    def save_papers(self, papers_list=None):
        """保存论文到数据库"""
        try:
            if papers_list is None:
                papers_list = list(self.papers_cache.values())
            
            result = self.db_manager.save_papers_batch(papers_list, source='bioRxiv')
            self.logger.info(f"保存bioRxiv论文到数据库: 新增 {result['saved']} 篇，更新 {result['updated']} 篇")
            
            return result
        except Exception as e:
            self.logger.error(f"保存bioRxiv论文到数据库失败: {e}")
            return {'saved': 0, 'updated': 0}
    
    def fetch_category(self, category: str, start_date: str, end_date: str) -> List[Dict]:
        """获取特定分类的所有论文"""
        all_papers = []
        cursor = 0  # 从第0个记录开始
        
        while True:
            api_url = f"https://api.biorxiv.org/details/biorxiv/{start_date}/{end_date}/{cursor}"
            
            # 添加category参数
            params = {'category': category.replace(' ', '_')}  # 空格替换为下划线
            
            self.logger.info(f"正在获取 {category} 分类，cursor={cursor}")
            
            try:
                response = requests.get(api_url, params=params, timeout=30)
                response.raise_for_status()
                print(response.url)
                data = response.json()
                
                # 检查响应状态
                messages = data.get('messages', [])
                if not messages or messages[0].get('status') != 'ok':
                    self.logger.warning(f"API返回状态异常: {messages}")
                    break
                
                message = messages[0]
                total_count = message.get('total', 0)
                current_count = message.get('count', 0)
                
                self.logger.info(f"{category} 分类总共 {total_count} 篇论文，当前批次 {current_count} 篇")
                
                # 如果当前页没有数据，说明已经获取完毕
                if current_count == 0:
                    break
                
                # 解析当前页的论文
                collection = data.get('collection', [])
                papers = self._parse_papers(collection)
                all_papers.extend(papers)
                
                self.logger.info(f"{category} 分类 cursor={cursor} 获得 {len(papers)} 篇有效论文")
                
                # 计算是否还有下一页
                # 每页最多100条，如果当前页少于100条或者已经获取了所有数据
                if current_count < 100 or len(all_papers) >= int(total_count):
                    break
                
                # 下一次请求的cursor应该是当前cursor + 当前返回的数量
                cursor += current_count
                time.sleep(0.5)  # 添加延迟避免请求过快
                
            except Exception as e:
                self.logger.error(f"获取 {category} 分类 cursor={cursor} 失败: {e}")
                break
        
        self.logger.info(f"{category} 分类共获取 {len(all_papers)} 篇论文")
        return all_papers
    
    def fetch(self, query_params: Dict=None) -> List[Dict]:
        """获取bioRxiv论文"""
        categories = query_params.get('categories', self.supported_categories)
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')
        
        if not start_date or not end_date:
            self.logger.error("必须提供开始和结束日期")
            return []
        
        # 格式化日期为YYYY-MM-DD
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d')
        
        all_papers = []
        
        # 为每个分类单独调用API
        for category in categories:
            if category not in self.supported_categories:
                self.logger.warning(f"不支持的分类: {category}")
                continue
            
            try:
                category_papers = self.fetch_category(category, start_date, end_date)
                all_papers.extend(category_papers)
            except Exception as e:
                self.logger.error(f"获取分类 {category} 失败: {e}")
                continue
        
        # 去重 - 基于DOI的最后部分作为唯一标识
        unique_papers = {}
        for paper in all_papers:
            paper_id = paper.get('id')
            if paper_id and paper_id not in unique_papers:
                unique_papers[paper_id] = paper
        
        deduplicated_papers = list(unique_papers.values())
        self.logger.info(f"总共获取 {len(all_papers)} 篇论文，去重后 {len(deduplicated_papers)} 篇")
        
        return deduplicated_papers
    
    def _parse_papers(self, collection: List[Dict]) -> List[Dict]:
        """解析论文数据"""
        papers = []
        
        for item in collection:
            try:
                # 只处理type为"new results"的论文
                if item.get('type') != 'new results':
                    continue
                
                # 提取DOI后面的部分作为ID
                doi = item.get('doi', '')
                if not doi:
                    continue
                
                paper_id = doi.split('/')[-1] if '/' in doi else doi
                
                # 构造论文数据
                paper = {
                    'id': paper_id,
                    'title': item.get('title', ''),
                    'authors': self._parse_authors(item.get('authors', '')),
                    'abstract': item.get('abstract', ''),
                    'categories': [item.get('category', '')],
                    'published_date': item.get('date', ''),
                    'url': f"https://www.biorxiv.org/content/{doi}",
                    'pdf_url': f"https://www.biorxiv.org/content/{doi}.full.pdf",
                    'fetched_date': datetime.now().isoformat(timespec='seconds'),
                    'doi': doi,
                    'type': item.get('type', ''),
                    'version': item.get('version', ''),
                    'license': item.get('license', ''),
                    'server': item.get('server', 'bioRxiv')
                }
                
                papers.append(paper)
                
            except Exception as e:
                self.logger.warning(f"解析论文失败: {e}, 数据: {item}")
                continue
        
        return papers
    
    def _parse_authors(self, authors_str: str) -> List[str]:
        """解析作者字符串"""
        if not authors_str:
            return []
        
        # 按分号和逗号分割作者
        authors = []
        for author in authors_str.split(';'):
            author = author.strip()
            if author:
                # 处理"LastName, FirstName"格式
                if ',' in author:
                    parts = author.split(',')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                        # 重新组合为"FirstName LastName"格式
                        author = f"{first_name} {last_name}".strip()
                
                authors.append(author)
        
        return authors
    
    def update_papers(self, categories: List[str] = None, start_date=None, end_date=None) -> Dict:
        """更新bioRxiv论文"""
        if categories is None:
            categories = self.supported_categories
        
        # 验证分类
        valid_categories = [cat for cat in categories if cat in self.supported_categories]
        if not valid_categories:
            self.logger.error(f"没有有效的分类。支持的分类: {self.supported_categories}")
            return {'scraped_papers': 0, 'new_papers': 0, 'total_papers': 0, 'db_saved': 0, 'db_updated': 0}
        
        # 设置默认日期
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=SEARCH_CONFIG['days_back'])
        
        query_params = {
            'categories': valid_categories,
            'start_date': start_date,
            'end_date': end_date
        }
        
        scraped_papers = self.fetch(query_params)
        
        categories_text = ', '.join(valid_categories)
        self.logger.info(f"更新bioRxiv论文范围: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}, 分类: {categories_text}")
        
        # 去重并添加到缓存
        new_papers = []
        added_count = 0
        
        for paper in scraped_papers:
            if paper['id'] not in self.papers_cache:
                self.papers_cache[paper['id']] = paper
                new_papers.append(paper)
                added_count += 1
        
        # 保存新论文到数据库
        if new_papers:
            save_result = self.save_papers(new_papers)
        else:
            save_result = {'saved': 0, 'updated': 0}
        
        stats = {
            'scraped_papers': len(scraped_papers),
            'new_papers': added_count,
            'total_papers': len(self.papers_cache),
            'db_saved': save_result['saved'],
            'db_updated': save_result['updated']
        }
        
        self.logger.info(f"bioRxiv更新完成: {stats}")
        
        return stats


if __name__ == '__main__':
    fetcher = BioRxivFetcher()
    stats = fetcher.update_papers()
    print(f"更新统计: {stats}")