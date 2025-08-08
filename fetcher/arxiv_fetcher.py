import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
from config import SEARCH_CONFIG, DATA_CONFIG, LOGGING_CONFIG
from database import DatabaseManager


class ArxivFetcher:
    def __init__(self):
        self.setup_logging()
        self.setup_data_dir()
        self.db_manager = DatabaseManager()
        self.papers_cache = {}
        self.load_existing_papers()
    
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
            papers_list = self.db_manager.get_papers(source='arXiv')
            self.papers_cache = {}
            for paper in papers_list:
                self.papers_cache[paper['id']] = paper
            self.logger.info(f"从数据库加载了 {len(self.papers_cache)} 篇已存在的论文")
        except Exception as e:
            self.logger.error(f"从数据库加载已存在论文失败: {e}")
            self.papers_cache = {}
    
    def save_papers(self, papers_list=None):
        """保存论文到数据库"""
        try:
            if papers_list is None:
                papers_list = list(self.papers_cache.values())
            
            result = self.db_manager.save_papers_batch(papers_list, source='arXiv')
            self.logger.info(f"保存论文到数据库: 新增 {result['saved']} 篇，更新 {result['updated']} 篇")
            
            # 同时保存到JSON作为备份（可选）
            self._save_papers_to_json_backup()
            
            return result
        except Exception as e:
            self.logger.error(f"保存论文到数据库失败: {e}")
            return {'saved': 0, 'updated': 0}
    
    def _save_papers_to_json_backup(self):
        """保存论文到JSON文件作为备份"""
        try:
            papers_path = os.path.join(DATA_CONFIG['data_dir'], DATA_CONFIG['papers_file'])
            with open(papers_path, 'w', encoding='utf-8') as f:
                json.dump(self.papers_cache, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"JSON备份保存了 {len(self.papers_cache)} 篇论文")
        except Exception as e:
            self.logger.warning(f"保存JSON备份失败: {e}")
    
    def fetch(self, query_params: Dict=None) -> List[Dict]:
        self.logger.info(f"使用web爬虫搜索，参数: {query_params}")
        all_papers = []
        results_per_page = query_params.get('results_per_page', 100)
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 第一页 - 获取总结果数
            search_url = self._build_search_url(query_params)
            self.logger.info(f"抓取第1页: {search_url}")
            
            response = requests.get(search_url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 解析总结果数
            total_results = self._parse_total_results(soup)
            if total_results == 0:
                self.logger.warning("未找到任何结果")
                return []
            
            # 计算总页数
            total_pages = (total_results + results_per_page - 1) // results_per_page
            self.logger.info(f"找到 {total_results} 篇论文，需要抓取 {total_pages} 页")
            
            # 解析第一页
            papers = self._parse_search_results(soup)
            all_papers.extend(papers)
            self.logger.info(f"第1页获得 {len(papers)} 篇论文")
            
            # 抓取剩余页面
            for page in range(2, total_pages + 1):
                start_index = (page - 1) * results_per_page
                page_query_params = query_params.copy()
                page_query_params['start'] = start_index
                
                page_url = self._build_search_url(page_query_params)
                self.logger.info(f"抓取第{page}页: start={start_index}")
                
                response = requests.get(page_url, headers=headers, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                papers = self._parse_search_results(soup)
                if papers:
                    all_papers.extend(papers)
                    self.logger.info(f"第{page}页获得 {len(papers)} 篇论文，累计 {len(all_papers)} 篇")
                else:
                    self.logger.warning(f"第{page}页未找到论文")
                
                time.sleep(1)  # 添加延迟避免请求过快
            
            self.logger.info(f"翻页完成，总共获取到 {len(all_papers)} 篇论文")
            return all_papers
            
        except Exception as e:
            self.logger.error(f"Web爬虫获取失败: {e}")
            return all_papers
   
    def update_papers(self, categories: List[str] = None, start_date=None, end_date=None) -> Dict:
        query_params = self._build_query_params(categories=categories, start_date=start_date, end_date=end_date)
        scraped_papers = self.fetch(query_params)
        print(start_date, end_date)

        categories_text = ', '.join(categories) if categories else '默认分类'
        self.logger.info(f"更新论文范围: {query_params['date_from']} to {query_params['date_to']}, 分类: {categories_text}")
        
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
        
        self.logger.info(f"更新完成: {stats}")

        return stats
    
    def _build_query_params(self, categories: List[str] = None, start_date=None, end_date=None) -> Dict:
        # 使用传入的日期，如果没有则使用默认日期范围
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=SEARCH_CONFIG['days_back'])

        # 使用传入的分类，如果没有则使用配置文件中的默认分类
        target_categories = categories if categories else SEARCH_CONFIG['categories']
        
        terms = []
        for category in target_categories:
            terms.append({
                'operator': SEARCH_CONFIG['operator'],
                'term': category,
                'field': 'all'
            })
        
        # 确保日期范围是完整的日历天数
        # 如果start_date包含时间信息，需要向上调整到下一天的开始
        if start_date.hour > 0 or start_date.minute > 0 or start_date.second > 0:
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        return {
            'terms': terms,
            'date_from': start_date.strftime('%Y-%m-%d'),
            'date_to': end_date.strftime('%Y-%m-%d'),
            'include_cross_list': SEARCH_CONFIG['include_cross_list'],
            'results_per_page': SEARCH_CONFIG['results_per_page'],
            'start': 0  # 默认从第一页开始
        }
    
    def _build_search_url(self, query_params: Dict) -> str:
        base_url = "https://arxiv.org/search/advanced"
        
        params = {
            'advanced': '',
            'classification-include_cross_list': 'include' if query_params.get('include_cross_list', True) else 'exclude',
            'date-year': '',
            'date-filter_by': 'date_range',  # 'all_dates', 'past_12', 'specific_year'
            'date-from_date': query_params.get('date_from', ''),
            'date-to_date': query_params.get('date_to', ''),
            'date-date_type': 'submitted_date',
            'abstracts': 'show',
            'size': query_params.get('results_per_page', 100),
            'order': '-announced_date_first'
        }
        
        # 添加分页参数
        if query_params.get('start', 0) > 0:
            params['start'] = query_params['start']
        
        terms = query_params.get('terms', [])
        for i, term in enumerate(terms):
            params[f'terms-{i}-operator'] = term.get('operator', 'AND')
            params[f'terms-{i}-term'] = term.get('term', '')
            params[f'terms-{i}-field'] = term.get('field', 'all')
        
        return f"{base_url}?{urlencode(params)}"
    
    def _parse_total_results(self, soup: BeautifulSoup) -> int:
        """解析搜索结果总数"""
        try:
            # 查找 div class='level' -> div class='level-left' -> h1 class='title'
            title_h1 = soup.select_one('div.level div.level-left h1.title.is-clearfix')
            if not title_h1:
                self.logger.warning("未找到目标 h1 元素")
                return 0
            
            # 解析类似 "Showing 1–50 of 1,588 results" 的文本
            title_text = title_h1.get_text().strip()
            self.logger.info(f"找到标题文本: {title_text}")
            
            # 使用正则表达式提取总数
            import re
            match = re.search(r'of\s+([\d,]+)\s+results', title_text)
            if match:
                total_str = match.group(1).replace(',', '')
                total_results = int(total_str)
                self.logger.info(f"解析出总结果数: {total_results}")
                return total_results
            else:
                self.logger.warning(f"无法从标题文本中解析结果数: {title_text}")
                return 0
                
        except Exception as e:
            self.logger.error(f"解析总结果数失败: {e}")
            return 0
    
    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict]:
        papers = []
        paper_list = soup.find('ol', class_='breathe-horizontal')
        if not paper_list:
            self.logger.warning("未找到论文列表元素")
            return papers
        
        for li in paper_list.find_all('li', class_='arxiv-result'):
            try:
                paper = self._parse_paper_element(li)
                if paper:
                    papers.append(paper)
            except Exception as e:
                self.logger.warning(f"解析论文元素失败: {e}")
                continue
        
        return papers
    
    def _parse_paper_element(self, element) -> Optional[Dict]:
        """解析单个论文元素"""
        try:
            arxiv_id = element.select_one('p.list-title a').get('href').split('/')[-1]
            title = element.select_one('p.title').text.strip()

            authors_elem = element.select_one('p.authors')
            authors = [a.text.strip() for a in authors_elem.select('a')] if authors_elem else []
            
            abstract = element.select_one('span.abstract-full').text.strip()
            abstract = re.sub(r'\s*△\s*Less\s*$', '', abstract).strip()
            
            date = element.select_one('p.is-size-7').text
            for part in date.split(';'):
                if 'Submitted' in part:
                    submitted_date = part.replace('Submitted', '').strip()
                    break
            
            categories_elem = element.select_one('div.tags')
            arxiv_categories = [span.text.strip() for span in categories_elem.select('span.tag')] if categories_elem else []
            
            return {
                'id': arxiv_id,
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'categories': arxiv_categories,
                'published_date': submitted_date,
                'url': f"https://arxiv.org/abs/{arxiv_id}",
                'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                'fetched_date': datetime.now().isoformat(timespec='seconds')
            }
        except Exception as e:
            self.logger.error(f"解析论文元素失败: {e}")
            return None
    
if __name__ == '__main__':
    fetcher = ArxivFetcher()
    stats = fetcher.update_papers()
    print(f"更新统计: {stats}")