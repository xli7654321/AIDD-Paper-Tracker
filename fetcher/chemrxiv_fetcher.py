import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from config import SEARCH_CONFIG, DATA_CONFIG, LOGGING_CONFIG
from database import DatabaseManager


class ChemRxivFetcher:
    def __init__(self):
        self.setup_logging()
        self.setup_data_dir()
        self.db_manager = DatabaseManager()
        self.papers_cache = {}
        self.load_existing_papers()
        
        # ChemRxiv支持的分类
        self.supported_categories = {
            'theoretical_computational': '605c72ef153207001f6470ce',  # Theoretical and Computational Chemistry
            'biological_medicinal': '605c72ef153207001f6470d0'       # Biological and Medicinal Chemistry
        }
        
        self.base_api_url = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/items"
    
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
            papers_list = self.db_manager.get_papers(source='ChemRxiv')
            self.papers_cache = {}
            for paper in papers_list:
                self.papers_cache[paper['id']] = paper
            self.logger.info(f"从数据库加载了 {len(self.papers_cache)} 篇已存在的ChemRxiv论文")
        except Exception as e:
            self.logger.error(f"从数据库加载已存在论文失败: {e}")
            self.papers_cache = {}
    
    def save_papers(self, papers_list=None):
        """保存论文到数据库"""
        try:
            if papers_list is None:
                papers_list = list(self.papers_cache.values())
            
            result = self.db_manager.save_papers_batch(papers_list, source='ChemRxiv')
            self.logger.info(f"保存ChemRxiv论文到数据库: 新增 {result['saved']} 篇，更新 {result['updated']} 篇")
            
            return result
        except Exception as e:
            self.logger.error(f"保存ChemRxiv论文到数据库失败: {e}")
            return {'saved': 0, 'updated': 0}
    
    def fetch_category(self, category_id: str, start_date: str, end_date: str) -> List[Dict]:
        """获取特定分类的所有论文"""
        all_papers = []
        limit = 50  # 固定每次获取50篇
        skip = 0    # 从第0个开始
        
        while True:
            params = {
                'limit': limit,
                'skip': skip,
                'sort': 'PUBLISHED_DATE_DESC',
                'searchDateFrom': start_date,
                'searchDateTo': end_date,
                'categoryIds': category_id
            }
            
            self.logger.info(f"正在获取分类 {category_id}，skip={skip}")
            
            try:
                response = requests.get(self.base_api_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # 获取总数和当前批次数据
                total_count = data.get('totalCount', 0)
                item_hits = data.get('itemHits', [])
                current_count = len(item_hits)
                
                self.logger.info(f"分类 {category_id} 总共 {total_count} 篇论文，当前批次 {current_count} 篇")
                
                # 如果当前页没有数据，说明已经获取完毕
                if current_count == 0:
                    break
                
                # 解析当前页的论文
                papers = self._parse_papers(item_hits)
                all_papers.extend(papers)
                
                self.logger.info(f"分类 {category_id} skip={skip} 获得 {len(papers)} 篇有效论文")
                
                # 检查是否还有下一页
                if skip + current_count >= total_count:
                    break
                
                # 下一次请求的skip
                skip += limit
                time.sleep(0.5)  # 添加延迟避免请求过快
                
            except Exception as e:
                self.logger.error(f"获取分类 {category_id} skip={skip} 失败: {e}")
                break
        
        self.logger.info(f"分类 {category_id} 共获取 {len(all_papers)} 篇论文")
        return all_papers
    
    def fetch(self, query_params: Dict = None) -> List[Dict]:
        """获取ChemRxiv论文"""
        categories = query_params.get('categories', list(self.supported_categories.keys()))
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
            
            category_id = self.supported_categories[category]
            
            try:
                category_papers = self.fetch_category(category_id, start_date, end_date)
                all_papers.extend(category_papers)
            except Exception as e:
                self.logger.error(f"获取分类 {category} 失败: {e}")
                continue
        
        # 去重 - 基于ID的去重
        unique_papers = {}
        for paper in all_papers:
            paper_id = paper.get('id')
            if paper_id:
                # 如果已存在相同ID的论文，保留最新的版本（根据publishedDate）
                if paper_id not in unique_papers:
                    unique_papers[paper_id] = paper
                else:
                    existing_paper = unique_papers[paper_id]
                    existing_date = existing_paper.get('published_date', '')
                    current_date = paper.get('published_date', '')
                    
                    # 比较日期，保留最新的
                    if current_date > existing_date:
                        unique_papers[paper_id] = paper
        
        deduplicated_papers = list(unique_papers.values())
        self.logger.info(f"总共获取 {len(all_papers)} 篇论文，去重后 {len(deduplicated_papers)} 篇")
        
        return deduplicated_papers
    
    def _parse_papers(self, item_hits: List[Dict]) -> List[Dict]:
        """解析论文数据"""
        papers = []
        
        for hit in item_hits:
            try:
                item = hit.get('item', {})
                
                # 基本信息
                item_id = item.get('id', '')
                doi = item.get('doi', '')
                title = item.get('title', '')
                abstract = item.get('abstract', '')
                
                # 提取DOI后面的部分作为ID（如果DOI存在）
                paper_id = doi.split('/')[-1] if doi and '/' in doi else item_id
                
                # 作者信息
                authors_list = item.get('authors', [])
                authors = []
                for author in authors_list:
                    first_name = author.get('firstName', '').strip()
                    last_name = author.get('lastName', '').strip()
                    if first_name and last_name:
                        authors.append(f"{first_name} {last_name}")
                    elif last_name:
                        authors.append(last_name)
                
                # 分类信息
                categories_list = item.get('categories', [])
                categories = [cat.get('name', '') for cat in categories_list if cat.get('name')]
                
                # 日期信息
                published_date = item.get('publishedDate', '')
                if published_date:
                    # 转换ISO格式日期为简化格式
                    try:
                        parsed_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                        published_date = parsed_date.strftime('%Y-%m-%d')
                    except:
                        pass
                
                # URL构建
                article_url = f"https://chemrxiv.org/engage/chemrxiv/article-details/{item_id}"
                
                # PDF URL
                pdf_url = ""
                asset = item.get('asset', {})
                if asset and asset.get('original'):
                    pdf_url = asset['original'].get('url', '')
                
                # 构造论文数据
                paper = {
                    'id': paper_id,
                    'title': title,
                    'authors': authors,
                    'abstract': abstract,
                    'categories': categories,
                    'published_date': published_date,
                    'url': article_url,
                    'pdf_url': pdf_url,
                    'fetched_date': datetime.now().isoformat(timespec='seconds'),
                    'doi': doi,
                    'item_id': item_id,
                    'version': item.get('version', ''),
                    'server': 'ChemRxiv'
                }
                
                papers.append(paper)
                
            except Exception as e:
                self.logger.warning(f"解析论文失败: {e}, 数据: {hit}")
                continue
        
        return papers
    
    def update_papers(self, categories: List[str] = None, start_date=None, end_date=None) -> Dict:
        """更新ChemRxiv论文"""
        if categories is None:
            categories = list(self.supported_categories.keys())
        
        # 验证分类
        valid_categories = [cat for cat in categories if cat in self.supported_categories]
        if not valid_categories:
            self.logger.error(f"没有有效的分类。支持的分类: {list(self.supported_categories.keys())}")
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
        self.logger.info(f"更新ChemRxiv论文范围: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}, 分类: {categories_text}")
        
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
        
        self.logger.info(f"ChemRxiv更新完成: {stats}")
        
        return stats


if __name__ == '__main__':
    fetcher = ChemRxivFetcher()
    stats = fetcher.update_papers()
    print(f"更新统计: {stats}")