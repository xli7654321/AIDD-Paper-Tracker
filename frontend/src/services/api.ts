import { Paper, FilterState, PaperStats } from '../types/paper';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface PaginatedPapersResponse {
  papers: any[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface UpdateRequest {
  sources: string[];
  categories?: string[];
  start_date?: string;
  end_date?: string;
}

export interface Category {
  id: string;
  name: string;
}

export interface Source {
  id: string;
  name: string;
  categories: Category[];
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Paper endpoints
  async getPapers(params: {
    source?: string;
    sources?: string[];
    page?: number;
    pageSize?: number;
    categories?: string[];
    relevanceStatus?: string[];
    dateStart?: string;
    dateEnd?: string;
    searchQuery?: string;
    searchScope?: string;
  } = {}): Promise<{papers: Paper[], pagination: {total: number, page: number, pageSize: number, totalPages: number}}> {
    const queryParams = new URLSearchParams();
    
    // Handle sources parameter (supports both single and multiple sources)
    const sourcesToProcess = params.sources || (params.source ? [params.source] : []);
    if (sourcesToProcess.length > 0) {
      // Map frontend source names to backend source names
      const sourceMapping = {
        'arxiv': 'arXiv',
        'biorxiv': 'bioRxiv', 
        'chemrxiv': 'ChemRxiv'
      };
      sourcesToProcess.forEach(source => {
        const mappedSource = sourceMapping[source.toLowerCase()] || source;
        queryParams.append('source', mappedSource);
      });
    }
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.pageSize) queryParams.append('page_size', params.pageSize.toString());
    if (params.dateStart) queryParams.append('date_start', params.dateStart);
    if (params.dateEnd) queryParams.append('date_end', params.dateEnd);
    if (params.searchQuery) queryParams.append('search_query', params.searchQuery);
    if (params.searchScope) queryParams.append('search_scope', params.searchScope);
    
    // Handle array parameters
    if (params.categories) {
      params.categories.forEach(cat => queryParams.append('categories', cat));
    }
    if (params.relevanceStatus) {
      params.relevanceStatus.forEach(status => queryParams.append('relevance_status', status));
    }

    const response = await this.request<PaginatedPapersResponse>(`/papers?${queryParams}`);
    
    // Transform the response to match frontend Paper interface
    const papers = response.papers.map(paper => ({
      id: paper.id,
      title: paper.title,
      authors: paper.authors,
      abstract: paper.abstract,
      publishedDate: new Date(paper.published_date),
      source: paper.source as 'arXiv' | 'bioRxiv' | 'ChemRxiv',
      categories: paper.categories,
      relevanceStatus: paper.is_relevant === 1 ? 'relevant' : 
                      paper.is_relevant === 0 ? 'irrelevant' : 'untagged',
      url: paper.url,
      pdfUrl: paper.pdf_url,
      doi: paper.doi,
    }));

    return {
      papers,
      pagination: {
        total: response.total,
        page: response.page,
        pageSize: response.page_size,
        totalPages: response.total_pages
      }
    };
  }

  async getPaperStats(params: {
    source?: string;
    sources?: string[];
    categories?: string[];
    relevanceStatus?: string[];
    dateStart?: string;
    dateEnd?: string;
    searchQuery?: string;
    searchScope?: string;
  } = {}): Promise<PaperStats> {
    const queryParams = new URLSearchParams();
    
    // Handle sources parameter (supports both single and multiple sources)
    const sourcesToProcess = params.sources || (params.source ? [params.source] : []);
    if (sourcesToProcess.length > 0) {
      // Map frontend source names to backend source names
      const sourceMapping = {
        'arxiv': 'arXiv',
        'biorxiv': 'bioRxiv', 
        'chemrxiv': 'ChemRxiv'
      };
      sourcesToProcess.forEach(source => {
        const mappedSource = sourceMapping[source.toLowerCase()] || source;
        queryParams.append('source', mappedSource);
      });
    }
    if (params.dateStart) queryParams.append('date_start', params.dateStart);
    if (params.dateEnd) queryParams.append('date_end', params.dateEnd);
    if (params.searchQuery) queryParams.append('search_query', params.searchQuery);
    if (params.searchScope) queryParams.append('search_scope', params.searchScope);
    
    if (params.categories) {
      params.categories.forEach(cat => queryParams.append('categories', cat));
    }
    if (params.relevanceStatus) {
      params.relevanceStatus.forEach(status => queryParams.append('relevance_status', status));
    }

    const stats = await this.request<any>(`/papers/stats?${queryParams}`);
    
    return {
      total: stats.total,
      relevant: stats.relevant,
      irrelevant: stats.irrelevant,
      untagged: stats.untagged,
      bySource: stats.by_source,
      byCategory: stats.by_category,
    };
  }

  async updatePaperRelevance(paperId: string, isRelevant: number | null): Promise<void> {
    await this.request(`/papers/${paperId}/relevance`, {
      method: 'PUT',
      body: JSON.stringify({ is_relevant: isRelevant }),
    });
  }

  async updatePapers(request: UpdateRequest): Promise<{ message: string; new_papers: number; total_papers: number; updated_sources: string[] }> {
    return this.request('/papers/update', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Configuration endpoints
  async getSources(): Promise<Source[]> {
    const response = await this.request<{ sources: Source[] }>('/sources');
    return response.sources;
  }

  async getCategories(): Promise<string[]> {
    const response = await this.request<{ categories: string[] }>('/categories');
    return response.categories;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health');
  }
}

export const apiService = new ApiService();