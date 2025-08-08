from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel
import sys
import os

# Add the parent directory to Python path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from data_processor import DataProcessor
from fetcher.arxiv_fetcher import ArxivFetcher
from fetcher.biorxiv_fetcher import BioRxivFetcher
from fetcher.chemrxiv_fetcher import ChemRxivFetcher
from config import DATA_CONFIG

app = FastAPI(
    title="AIDD Paper Tracker API",
    description="API for AI Drug Discovery Paper Tracking System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize components
db_manager = DatabaseManager()
data_processor = DataProcessor()
arxiv_fetcher = ArxivFetcher()
biorxiv_fetcher = BioRxivFetcher()
chemrxiv_fetcher = ChemRxivFetcher()

# Pydantic models
class Paper(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    published_date: str
    source: str
    categories: List[str]
    is_relevant: Optional[int] = None  # 1 for relevant, 0 for irrelevant, None for untagged
    url: str
    pdf_url: Optional[str] = None
    doi: Optional[str] = None

class PaperUpdate(BaseModel):
    is_relevant: Optional[int] = None

class PaginatedPapersResponse(BaseModel):
    papers: List[Paper]
    total: int
    page: int
    page_size: int
    total_pages: int

class FilterParams(BaseModel):
    sources: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    relevance_status: Optional[List[str]] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    search_query: Optional[str] = None

class PaperStats(BaseModel):
    total: int
    relevant: int
    irrelevant: int
    untagged: int
    by_source: Dict[str, int]
    by_category: Dict[str, int]

class UpdateRequest(BaseModel):
    sources: List[str]  # Support multiple sources
    categories: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

@app.get("/")
async def root():
    return {"message": "AIDD Paper Tracker API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.options("/{path:path}")
async def options_handler():
    """Handle CORS preflight requests"""
    return {"message": "OK"}

# Paper data management endpoints
@app.get("/papers", response_model=PaginatedPapersResponse)
async def get_papers(
    source: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    categories: Optional[List[str]] = Query(None),
    relevance_status: Optional[List[str]] = Query(None),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    search_query: Optional[str] = None,
    search_scope: Optional[str] = Query("title", regex="^(title|abstract|authors|all)$")
):
    """Get papers with optional filtering and pagination"""
    try:
        # Load papers from database
        if source and len(source) > 0:
            # Load specified sources and combine them
            all_papers = {}
            for src in source:
                try:
                    temp_processor = DataProcessor()
                    temp_processor.load_data(source=src)
                    all_papers.update(temp_processor.papers_data)
                except Exception as e:
                    print(f"Warning: Failed to load {src} data: {e}")
            papers = list(all_papers.values())
        else:
            # Load all sources and combine them
            all_papers = {}
            for src in ['arXiv', 'bioRxiv', 'ChemRxiv']:
                try:
                    temp_processor = DataProcessor()
                    temp_processor.load_data(source=src)
                    all_papers.update(temp_processor.papers_data)
                except Exception as e:
                    print(f"Warning: Failed to load {src} data: {e}")
            papers = list(all_papers.values())
        
        # Apply filters (don't pass source filter since we already loaded only requested sources)
        filtered_papers = _filter_papers(papers, categories, relevance_status, date_start, date_end, search_query, None, search_scope)
        
        # Sort papers based on source
        filtered_papers = _sort_papers_by_source(filtered_papers)
        
        # Calculate pagination info
        total_filtered = len(filtered_papers)
        total_pages = (total_filtered + page_size - 1) // page_size if total_filtered > 0 else 1
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_papers = filtered_papers[start_idx:end_idx]
        
        # Convert to API model
        result_papers = []
        for paper in paginated_papers:
            # Map relevance status
            relevance_status_map = {1: "relevant", 0: "irrelevant", None: "untagged"}
            
            paper_data = Paper(
                id=paper.get('id', ''),
                title=paper.get('title', ''),
                authors=paper.get('authors', []),
                abstract=paper.get('abstract', ''),
                published_date=paper.get('published_date', ''),
                source=paper.get('source', '').lower(),
                categories=paper.get('categories', []),
                is_relevant=paper.get('is_relevant'),
                url=paper.get('url', ''),
                pdf_url=paper.get('pdf_url'),
                doi=paper.get('doi')
            )
            result_papers.append(paper_data)
        
        return PaginatedPapersResponse(
            papers=result_papers,
            total=total_filtered,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve papers: {str(e)}")

@app.get("/papers/stats", response_model=PaperStats)
async def get_paper_stats(
    source: Optional[List[str]] = Query(None),
    categories: Optional[List[str]] = Query(None),
    relevance_status: Optional[List[str]] = Query(None),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    search_query: Optional[str] = None,
    search_scope: Optional[str] = Query("title", regex="^(title|abstract|authors|all)$")
):
    """Get statistics about papers"""
    try:
        # Load papers from database
        if source and len(source) > 0:
            # Load specified sources and combine them
            all_papers = {}
            for src in source:
                try:
                    temp_processor = DataProcessor()
                    temp_processor.load_data(source=src)
                    all_papers.update(temp_processor.papers_data)
                except Exception as e:
                    print(f"Warning: Failed to load {src} data: {e}")
            papers = list(all_papers.values())
        else:
            # Load all sources and combine them
            all_papers = {}
            for src in ['arXiv', 'bioRxiv', 'ChemRxiv']:
                try:
                    temp_processor = DataProcessor()
                    temp_processor.load_data(source=src)
                    all_papers.update(temp_processor.papers_data)
                except Exception as e:
                    print(f"Warning: Failed to load {src} data: {e}")
            papers = list(all_papers.values())
        
        # Apply filters (don't pass source filter since we already loaded only requested sources)
        filtered_papers = _filter_papers(papers, categories, relevance_status, date_start, date_end, search_query, None, search_scope)
        
        # Calculate statistics
        stats = _calculate_stats(filtered_papers)
        
        return PaperStats(**stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")

@app.post("/papers/update")
async def update_papers(update_request: UpdateRequest):
    """Update papers from external sources"""
    try:
        sources = update_request.sources
        categories = update_request.categories or []
        start_date = update_request.start_date
        end_date = update_request.end_date
        
        # Convert dates if provided
        if start_date and end_date:
            from datetime import datetime, timedelta
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.min.time())
        else:
            from datetime import datetime, timedelta
            end_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_dt = end_dt - timedelta(days=30)
        
        # Update papers for each source
        total_new_papers = 0
        total_papers = 0
        updated_sources = []
        
        for source in sources:
            try:
                if source.lower() == 'arxiv':
                    stats = arxiv_fetcher.update_papers(
                        categories=categories,
                        start_date=start_dt,
                        end_date=end_dt
                    )
                elif source.lower() == 'biorxiv':
                    stats = biorxiv_fetcher.update_papers(
                        categories=categories,
                        start_date=start_dt,
                        end_date=end_dt
                    )
                elif source.lower() == 'chemrxiv':
                    stats = chemrxiv_fetcher.update_papers(
                        categories=categories,
                        start_date=start_dt,
                        end_date=end_dt
                    )
                else:
                    print(f"Warning: Unsupported source: {source}")
                    continue
                
                total_new_papers += stats.get('new_papers', 0)
                total_papers += stats.get('total_papers', 0)
                updated_sources.append(source)
                
            except Exception as e:
                print(f"Warning: Failed to update {source}: {e}")
                continue
        
        if not updated_sources:
            raise HTTPException(status_code=400, detail="No valid sources provided")
        
        sources_text = ", ".join(updated_sources)
        return {
            "message": f"Successfully updated papers from {sources_text}",
            "new_papers": total_new_papers,
            "total_papers": total_papers,
            "updated_sources": updated_sources
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update papers: {str(e)}")

@app.get("/sources")
async def get_available_sources():
    """Get list of available paper sources"""
    return {
        "sources": [
            {
                "id": "arxiv", 
                "name": "arXiv", 
                "categories": [
                    {"id": "physics.chem-ph", "name": "Physics - Chemical Physics"},
                    {"id": "cs.AI", "name": "Computer Science - Artificial Intelligence"},
                    {"id": "cs.LG", "name": "Computer Science - Machine Learning"},
                    {"id": "q-bio", "name": "Quantitative Biology"}
                ]
            },
            {
                "id": "biorxiv", 
                "name": "bioRxiv", 
                "categories": [
                    {"id": "biochemistry", "name": "Biochemistry"},
                    {"id": "bioinformatics", "name": "Bioinformatics"},
                    {"id": "biophysics", "name": "Biophysics"},
                    {"id": "synthetic biology", "name": "Synthetic Biology"}
                ]
            },
            {
                "id": "chemrxiv", 
                "name": "ChemRxiv", 
                "categories": [
                    {"id": "theoretical_computational", "name": "Theoretical and Computational Chemistry"},
                    {"id": "biological_medicinal", "name": "Biological and Medicinal Chemistry"}
                ]
            }
        ]
    }

@app.put("/papers/{paper_id}/relevance")
async def update_paper_relevance(paper_id: str, update: PaperUpdate):
    """Update the relevance status of a paper"""
    try:
        success = data_processor.update_paper_relevance(paper_id, 
            True if update.is_relevant == 1 else False if update.is_relevant == 0 else None)
        
        if success:
            return {"message": "Paper relevance updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Paper not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update paper relevance: {str(e)}")

@app.get("/categories")
async def get_available_categories():
    """Get all available categories across all sources"""
    return {
        "categories": [
            "physics.chem-ph", "cs.AI", "cs.LG", "q-bio",  # arXiv
            "biochemistry", "bioinformatics", "biophysics", "synthetic biology",  # bioRxiv
            "theoretical_computational", "biological_medicinal"  # ChemRxiv
        ]
    }

# Helper functions
def _filter_papers(papers, categories=None, relevance_status=None, date_start=None, date_end=None, search_query=None, source=None, search_scope="title"):
    """Filter papers based on various criteria"""
    filtered_papers = papers.copy()
    
    # Filter by source
    if source:
        filtered_papers = [p for p in filtered_papers if p.get('source', '').lower() == source.lower()]
    
    # Filter by categories
    if categories:
        filtered_papers = [p for p in filtered_papers if matches_category_filter(p.get('categories', []), categories, p.get('source', ''))]
    
    # Filter by relevance status
    if relevance_status:
        status_mapping = {
            'relevant': 1,
            'irrelevant': 0,
            'untagged': None
        }
        
        def check_relevance(paper):
            paper_relevance = paper.get('is_relevant')
            for status in relevance_status:
                if paper_relevance == status_mapping.get(status):
                    return True
            return False
        
        filtered_papers = [p for p in filtered_papers if check_relevance(p)]
    
    # Filter by date range
    if date_start or date_end:
        from datetime import datetime
        
        def parse_paper_date(date_str):
            if not date_str:
                return None
            
            date_formats = [
                '%d %B, %Y',
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            import re
            match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
            if match:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))
            
            return None
        
        def date_filter(paper):
            paper_date = parse_paper_date(paper.get('published_date', ''))
            if not paper_date:
                return False
            
            if date_start:
                start_dt = datetime.strptime(date_start, '%Y-%m-%d')
                if paper_date < start_dt:
                    return False
            
            if date_end:
                end_dt = datetime.strptime(date_end, '%Y-%m-%d')
                if paper_date > end_dt:
                    return False
            
            return True
        
        filtered_papers = [p for p in filtered_papers if date_filter(p)]
    
    # Filter by search query with scope
    if search_query:
        query = search_query.lower()
        
        def matches_search(paper):
            if search_scope == "title":
                return query in paper.get('title', '').lower()
            elif search_scope == "abstract":
                return query in paper.get('abstract', '').lower()
            elif search_scope == "authors":
                return any(query in author.lower() for author in paper.get('authors', []))
            else:  # search_scope == "all"
                return (query in paper.get('title', '').lower() or 
                       query in paper.get('abstract', '').lower() or
                       any(query in author.lower() for author in paper.get('authors', [])))
        
        filtered_papers = [p for p in filtered_papers if matches_search(p)]
    
    return filtered_papers

def _calculate_stats(papers):
    """Calculate statistics for a list of papers"""
    stats = {
        'total': len(papers),
        'relevant': 0,
        'irrelevant': 0,
        'untagged': 0,
        'by_source': {},
        'by_category': {}
    }
    
    # Define categories by source to prevent cross-source matching
    categories_by_source = {
        'arXiv': ["physics.chem-ph", "cs.AI", "cs.LG", "q-bio"],
        'bioRxiv': ["biochemistry", "bioinformatics", "biophysics", "synthetic biology"],
        'ChemRxiv': ["theoretical_computational", "biological_medicinal"]
    }
    
    # Initialize all categories to 0
    for source_cats in categories_by_source.values():
        for cat in source_cats:
            stats['by_category'][cat] = 0
    
    for paper in papers:
        # Count by relevance
        relevance = paper.get('is_relevant')
        if relevance == 1:
            stats['relevant'] += 1
        elif relevance == 0:
            stats['irrelevant'] += 1
        else:
            stats['untagged'] += 1
        
        # Count by source
        source = paper.get('source', 'Unknown')
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
        
        # Count by categories - only count categories that belong to this paper's source
        paper_source = paper.get('source', '')
        paper_categories = paper.get('categories', [])
        
        if paper_source in categories_by_source:
            source_categories = categories_by_source[paper_source]
            for main_category in source_categories:
                if matches_single_category_with_source(paper_categories, main_category, paper_source):
                    stats['by_category'][main_category] += 1
    
    return stats

def matches_category_filter(paper_categories, selected_categories, paper_source=None):
    """Check if paper categories match any of the selected categories"""
    # Define category mappings by source to prevent cross-source matching
    categories_by_source = {
        'arXiv': {
            'physics.chem-ph': ['physics.chem-ph'],
            'cs.AI': ['cs.ai', 'cs.AI'],  # Handle case variations
            'cs.LG': ['cs.lg', 'cs.LG'],
            'q-bio': []  # Will be handled by startswith logic
        },
        'bioRxiv': {
            'biochemistry': ['biochemistry'],
            'bioinformatics': ['bioinformatics'], 
            'biophysics': ['biophysics'],
            'synthetic biology': ['synthetic biology']
        },
        'ChemRxiv': {
            'theoretical_computational': ['Theoretical and Computational Chemistry', 'Theory - Computational', 'Computational Chemistry and Modeling', 'Chemoinformatics - Computational Chemistry'],
            'biological_medicinal': ['Biological and Medicinal Chemistry', 'Biochemistry', 'Bioinformatics and Computational Biology']
        }
    }
    
    for selected_cat in selected_categories:
        selected_cat_lower = selected_cat.lower()
        
        # Find which source this selected category belongs to
        category_source = None
        for source, cats in categories_by_source.items():
            if selected_cat in cats:
                category_source = source
                break
        
        # If we have paper source info, only match categories from the same source
        if paper_source and category_source and paper_source != category_source:
            continue
            
        # Handle ChemRxiv simplified categories
        if selected_cat in categories_by_source.get('ChemRxiv', {}):
            mapping = categories_by_source['ChemRxiv'][selected_cat]
            for paper_cat in paper_categories:
                if paper_cat in mapping:
                    return True
        else:
            # Handle other categories (arXiv hierarchical, bioRxiv direct match)
            for paper_cat in paper_categories:
                paper_cat_lower = paper_cat.lower()
                # Handle hierarchical categories like q-bio.BM matching q-bio
                if (paper_cat_lower == selected_cat_lower or 
                    paper_cat_lower.startswith(selected_cat_lower + '.')):
                    return True
    return False

def matches_single_category(paper_categories, target_category):
    """Check if paper categories match a single target category"""
    return matches_category_filter(paper_categories, [target_category])

def matches_single_category_with_source(paper_categories, target_category, paper_source):
    """Check if paper categories match a single target category with source constraint"""
    return matches_category_filter(paper_categories, [target_category], paper_source)

def _sort_papers_by_source(papers):
    """Sort papers based on their source type"""
    from datetime import datetime
    
    def parse_paper_date(date_str):
        """Parse paper date string for sorting"""
        if not date_str:
            return datetime.min
        
        date_formats = [
            '%d %B, %Y',
            '%Y-%m-%d', 
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        import re
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day))
        
        return datetime.min
    
    def parse_arxiv_id(paper_id):
        """Parse arXiv ID for sorting"""
        try:
            if not paper_id or '.' not in paper_id:
                return (0, 0, 0)
            
            year_month, sequence = paper_id.split('.', 1)
            if len(year_month) != 4:
                return (0, 0, 0)
            
            year = int('20' + year_month[:2])
            month = int(year_month[2:4])
            
            sequence_num = ''
            for char in sequence:
                if char.isdigit():
                    sequence_num += char
                else:
                    break
            
            seq = int(sequence_num) if sequence_num else 0
            return (year, month, seq)
            
        except (ValueError, IndexError):
            return (0, 0, 0)
    
    # Separate papers by source
    chemrxiv_papers = []
    other_papers = []
    
    for paper in papers:
        if paper.get('source', '').lower() == 'chemrxiv':
            chemrxiv_papers.append(paper)
        else:
            other_papers.append(paper)
    
    # Sort ChemRxiv papers by date (newest first)
    chemrxiv_papers.sort(key=lambda p: parse_paper_date(p.get('published_date', '')), reverse=True)
    
    # Sort other papers (arXiv, bioRxiv) by ID (newest first)
    other_papers.sort(key=lambda p: parse_arxiv_id(p.get('id', '')), reverse=True)
    
    # Combine sorted papers
    return chemrxiv_papers + other_papers