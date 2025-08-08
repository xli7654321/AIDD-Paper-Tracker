export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  publishedDate: Date;
  source: 'arXiv' | 'bioRxiv' | 'ChemRxiv';
  categories: string[];
  relevanceStatus: 'relevant' | 'irrelevant' | 'untagged';
  url: string;
  pdfUrl?: string;
  doi?: string;
}

export interface FilterState {
  sources: string[];
  categories: string[];
  relevanceStatus: string[];
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  searchQuery: string;
  searchScope: 'title' | 'abstract' | 'authors' | 'all';
}

export interface PaperStats {
  total: number;
  relevant: number;
  irrelevant: number;
  untagged: number;
  bySource: Record<string, number>;
  byCategory: Record<string, number>;
}