import { useMemo } from 'react';
import { Paper, FilterState, PaperStats } from '@/types/paper';

export function usePaperFilters(papers: Paper[], filters: FilterState) {
  const filteredPapers = useMemo(() => {
    return papers.filter((paper) => {
      // Search filter
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        const searchableText = [
          paper.title,
          paper.authors.join(' '),
          paper.abstract,
          ...paper.categories,
        ].join(' ').toLowerCase();
        
        if (!searchableText.includes(query)) {
          return false;
        }
      }

      // Source filter
      if (filters.sources.length > 0 && !filters.sources.includes(paper.source)) {
        return false;
      }

      // Category filter
      if (filters.categories.length > 0) {
        const hasCategory = paper.categories.some(category => 
          filters.categories.includes(category)
        );
        if (!hasCategory) {
          return false;
        }
      }

      // Relevance status filter
      if (filters.relevanceStatus.length > 0 && !filters.relevanceStatus.includes(paper.relevanceStatus)) {
        return false;
      }

      // Date range filter
      if (filters.dateRange.start && paper.publishedDate < filters.dateRange.start) {
        return false;
      }
      if (filters.dateRange.end && paper.publishedDate > filters.dateRange.end) {
        return false;
      }

      return true;
    });
  }, [papers, filters]);

  const stats: PaperStats = useMemo(() => {
    const total = filteredPapers.length;
    const relevant = filteredPapers.filter(p => p.relevanceStatus === 'relevant').length;
    const irrelevant = filteredPapers.filter(p => p.relevanceStatus === 'irrelevant').length;
    const untagged = filteredPapers.filter(p => p.relevanceStatus === 'untagged').length;

    const bySource = filteredPapers.reduce((acc, paper) => {
      acc[paper.source] = (acc[paper.source] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const byCategory = filteredPapers.reduce((acc, paper) => {
      paper.categories.forEach(category => {
        acc[category] = (acc[category] || 0) + 1;
      });
      return acc;
    }, {} as Record<string, number>);

    return {
      total,
      relevant,
      irrelevant,
      untagged,
      bySource,
      byCategory,
    };
  }, [filteredPapers]);

  return { filteredPapers, stats };
}