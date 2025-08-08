#!/usr/bin/env python3
"""
数据库管理脚本
用于管理论文数据库，包括查看、删除等操作
"""

from datetime import datetime
from database import DatabaseManager


class DBManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def show_stats(self):
        """显示数据库统计信息"""
        print("\n=== 数据库统计信息 ===")
        
        # 总体统计
        stats = self.db_manager.get_paper_stats()
        print(f"总论文数: {stats['total']}")
        print(f"相关论文: {stats['relevant']}")
        print(f"不相关论文: {stats['irrelevant']}")
        print(f"未标记论文: {stats['untagged']}")
        
        # 按数据源统计
        arxiv_stats = self.db_manager.get_paper_stats('arXiv')
        print(f"\narXiv论文: {arxiv_stats['total']}")
        
    def list_papers(self, limit=10):
        """列出最新的论文"""
        print(f"\n=== 最新 {limit} 篇论文 ===")
        papers = self.db_manager.get_papers(limit=limit)
        
        if not papers:
            print("数据库中没有论文")
            return
        
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['id']} - {paper['title'][:60]}...")
            print(f"   分类: {', '.join(paper['categories'][:3])}{'...' if len(paper['categories']) > 3 else ''}")
            print(f"   日期: {paper['published_date']}")
            print()
    
    def search_papers(self, keyword):
        """搜索论文"""
        print(f"\n=== 搜索关键词: {keyword} ===")
        papers = self.db_manager.get_papers()
        
        matched_papers = []
        for paper in papers:
            if (keyword.lower() in paper['title'].lower() or 
                keyword.lower() in paper['abstract'].lower() or
                any(keyword.lower() in cat.lower() for cat in paper['categories'])):
                matched_papers.append(paper)
        
        if not matched_papers:
            print("没有找到匹配的论文")
            return
        
        print(f"找到 {len(matched_papers)} 篇相关论文:")
        for i, paper in enumerate(matched_papers[:10], 1):  # 只显示前10个
            print(f"{i}. {paper['id']} - {paper['title'][:60]}...")
    
    def delete_paper_interactive(self):
        """交互式删除单篇论文"""
        paper_id = input("\n请输入要删除的论文ID (如 2508.00781): ").strip()
        if not paper_id:
            print("未输入论文ID")
            return
        
        # 先查找论文信息
        papers = self.db_manager.get_papers()
        paper = None
        for p in papers:
            if p['id'] == paper_id:
                paper = p
                break
        
        if not paper:
            print(f"未找到论文: {paper_id}")
            return
        
        print(f"\n找到论文:")
        print(f"ID: {paper['id']}")
        print(f"标题: {paper['title']}")
        print(f"分类: {', '.join(paper['categories'])}")
        print(f"日期: {paper['published_date']}")
        
        confirm = input(f"\n确认删除论文 {paper_id}? (y/N): ").strip().lower()
        if confirm == 'y':
            if self.db_manager.delete_paper(paper_id):
                print(f"✅ 已删除论文: {paper_id}")
            else:
                print(f"❌ 删除失败: {paper_id}")
        else:
            print("已取消删除")
    
    def delete_all_papers_interactive(self):
        """交互式删除所有论文"""
        stats = self.db_manager.get_paper_stats()
        total_count = stats['total']
        
        if total_count == 0:
            print("数据库中没有论文")
            return
        
        print(f"\n⚠️  警告: 将删除数据库中的所有 {total_count} 篇论文!")
        confirm1 = input("这个操作不可恢复，确认继续? (y/N): ").strip().lower()
        
        if confirm1 != 'y':
            print("已取消删除")
            return
        
        confirm2 = input("最后确认: 输入 'DELETE ALL' 来确认删除所有论文: ").strip()
        
        if confirm2 == 'DELETE ALL':
            deleted_count = self.db_manager.delete_all_papers()
            print(f"✅ 已删除所有 {deleted_count} 篇论文")
        else:
            print("确认文本不匹配，已取消删除")
    
    def delete_by_source_interactive(self):
        """交互式按数据源删除"""
        print("\n可用的数据源:")
        print("1. arXiv")
        print("2. bioRxiv")
        print("3. ChemRxiv")
        
        choice = input("请选择要删除的数据源 (1-3): ").strip()
        source_map = {'1': 'arXiv', '2': 'bioRxiv', '3': 'ChemRxiv'}
        
        if choice not in source_map:
            print("无效选择")
            return
        
        source = source_map[choice]
        stats = self.db_manager.get_paper_stats(source)
        count = stats['total']
        
        if count == 0:
            print(f"数据库中没有 {source} 论文")
            return
        
        confirm = input(f"确认删除所有 {count} 篇 {source} 论文? (y/N): ").strip().lower()
        if confirm == 'y':
            deleted_count = self.db_manager.delete_papers_by_source(source)
            print(f"✅ 已删除 {deleted_count} 篇 {source} 论文")
        else:
            print("已取消删除")
    
    def reset_auto_increment_interactive(self):
        """交互式重置自增ID"""
        print("\n⚠️  重置自增ID将使下一个插入的记录从ID=1开始")
        confirm = input("确认重置自增ID? (y/N): ").strip().lower()
        
        if confirm == 'y':
            if self.db_manager.reset_auto_increment():
                print("✅ 已重置自增ID序列，下一条记录将从ID=1开始")
            else:
                print("❌ 重置自增ID失败")
        else:
            print("已取消重置")
    
    def backup_database(self):
        """备份数据库"""
        import shutil
        
        db_path = self.db_manager.db_path
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            shutil.copy2(db_path, backup_path)
            print(f"✅ 数据库已备份到: {backup_path}")
        except Exception as e:
            print(f"❌ 备份失败: {e}")
    
    def run(self):
        """运行交互式管理界面"""
        print("=== 论文数据库管理工具 ===")
        
        while True:
            print("\n请选择操作:")
            print("1. 查看数据库统计")
            print("2. 列出最新论文")
            print("3. 搜索论文")
            print("4. 删除单篇论文")
            print("5. 删除指定数据源的所有论文")
            print("6. 删除所有论文")
            print("7. 重置自增ID序列")
            print("8. 备份数据库")
            print("0. 退出")
            
            choice = input("\n请输入选择 (0-8): ").strip()
            
            try:
                if choice == '0':
                    print("再见!")
                    break
                elif choice == '1':
                    self.show_stats()
                elif choice == '2':
                    limit = input("显示多少篇论文 (默认10): ").strip()
                    limit = int(limit) if limit.isdigit() else 10
                    self.list_papers(limit)
                elif choice == '3':
                    keyword = input("请输入搜索关键词: ").strip()
                    if keyword:
                        self.search_papers(keyword)
                elif choice == '4':
                    self.delete_paper_interactive()
                elif choice == '5':
                    self.delete_by_source_interactive()
                elif choice == '6':
                    self.delete_all_papers_interactive()
                elif choice == '7':
                    self.reset_auto_increment_interactive()
                elif choice == '8':
                    self.backup_database()
                else:
                    print("无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n\n操作被中断")
                break
            except Exception as e:
                print(f"❌ 操作出错: {e}")


if __name__ == "__main__":
    manager = DBManager()
    manager.run()