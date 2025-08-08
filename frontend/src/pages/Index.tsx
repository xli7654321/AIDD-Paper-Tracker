import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { PaperCard } from '@/components/paper/PaperCard';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import { Paper, FilterState } from '@/types/paper';
import { apiService } from '@/services/api';
import { toast } from '@/hooks/use-toast';

// Helper function to format date as YYYY-MM-DD without timezone conversion
const formatDateForAPI = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const Index = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<FilterState>({
    sources: [],
    categories: [],
    relevanceStatus: [],
    dateRange: { start: null, end: null },
    searchQuery: '',
    searchScope: 'title',
  });

  const queryClient = useQueryClient();
  const papersPerPage = 6;

  // Query papers from API
  const { data: papersData, isLoading, error, refetch } = useQuery({
    queryKey: ['papers', filters, currentPage],
    queryFn: async () => {
      const params = {
        page: currentPage,
        pageSize: papersPerPage,
        sources: filters.sources.length > 0 ? filters.sources : undefined,
        categories: filters.categories.length > 0 ? filters.categories : undefined,
        relevanceStatus: filters.relevanceStatus.length > 0 ? filters.relevanceStatus : undefined,
        dateStart: filters.dateRange.start ? formatDateForAPI(filters.dateRange.start) : undefined,
        dateEnd: filters.dateRange.end ? formatDateForAPI(filters.dateRange.end) : undefined,
        searchQuery: filters.searchQuery || undefined,
        searchScope: filters.searchScope,
      };
      return apiService.getPapers(params);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const rawPapers = papersData?.papers || [];
  const paginationInfo = papersData?.pagination;

  // Sort papers with ChemRxiv papers by published date descending
  const papers = rawPapers.sort((a: Paper, b: Paper) => {
    // Only sort ChemRxiv papers by date, keep other sources as-is
    if (a.source === 'chemrxiv' && b.source === 'chemrxiv') {
      const dateA = new Date(a.published_date).getTime();
      const dateB = new Date(b.published_date).getTime();
      return dateB - dateA; // Descending order (newest first)
    }
    return 0; // Keep original order for other sources
  });

  // Query stats - use same filters as papers query
  const { data: stats } = useQuery({
    queryKey: ['paper-stats', filters],
    queryFn: async () => {
      const params = {
        sources: filters.sources.length > 0 ? filters.sources : undefined,
        categories: filters.categories.length > 0 ? filters.categories : undefined,
        relevanceStatus: filters.relevanceStatus.length > 0 ? filters.relevanceStatus : undefined,
        dateStart: filters.dateRange.start ? formatDateForAPI(filters.dateRange.start) : undefined,
        dateEnd: filters.dateRange.end ? formatDateForAPI(filters.dateRange.end) : undefined,
        searchQuery: filters.searchQuery || undefined,
        searchScope: filters.searchScope,
      };
      return apiService.getPaperStats(params);
    },
    staleTime: 5 * 60 * 1000,
  });

  // Mutation for updating paper relevance
  const updateRelevanceMutation = useMutation({
    mutationFn: async ({ paperId, status }: { paperId: string, status: 'relevant' | 'irrelevant' | 'untagged' }) => {
      const isRelevant = status === 'relevant' ? 1 : status === 'irrelevant' ? 0 : null;
      return { result: await apiService.updatePaperRelevance(paperId, isRelevant), status };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      queryClient.invalidateQueries({ queryKey: ['paper-stats'] });
      
      const { status } = data;
      const messages = {
        relevant: {
          title: "✅ Marked as Relevant",
          description: "This paper has been added to your relevant collection"
        },
        irrelevant: {
          title: "❌ Marked as Not Relevant", 
          description: "This paper has been marked as not relevant to your research"
        },
        untagged: {
          title: "🏷️ Tag Cleared",
          description: "Paper relevance tag has been removed"
        }
      };
      
      toast({
        title: messages[status].title,
        description: messages[status].description,
      });
    },
    onError: (error) => {
      toast({
        title: "❌ Error",
        description: "Failed to update paper relevance. Please try again.",
        variant: "destructive",
      });
      console.error('Failed to update paper relevance:', error);
    },
  });

  // Update papers mutation
  const updatePapersMutation = useMutation({
    mutationFn: async () => {
      const updateRequest = {
        sources: filters.sources.length > 0 ? filters.sources : ['arxiv', 'biorxiv', 'chemrxiv'],
        categories: filters.categories.length > 0 ? filters.categories : undefined,
        start_date: filters.dateRange.start ? formatDateForAPI(filters.dateRange.start) : undefined,
        end_date: filters.dateRange.end ? formatDateForAPI(filters.dateRange.end) : undefined,
      };
      return apiService.updatePapers(updateRequest);
    },
    onSuccess: (result) => {
      // Refetch papers and stats to get updated data
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      queryClient.invalidateQueries({ queryKey: ['paper-stats'] });
      
      // Format source names with proper capitalization
      const formatSourceName = (source: string) => {
        switch (source.toLowerCase()) {
          case 'arxiv': return 'arXiv';
          case 'biorxiv': return 'bioRxiv';
          case 'chemrxiv': return 'ChemRxiv';
          default: return source;
        }
      };
      
      const formattedSources = result.updated_sources.map(formatSourceName).join(', ');
      const newCount = result.new_papers;
      
      if (newCount === 0) {
        toast({
          title: "🔍 Update Complete",
          description: `No new papers found from ${formattedSources}. Your collection is up to date!`,
        });
      } else if (newCount === 1) {
        toast({
          title: "🎉 Found New Paper!",
          description: `Successfully added 1 new paper from ${formattedSources}`,
        });
      } else {
        toast({
          title: `🎉 Found ${newCount} New Papers!`,
          description: `Successfully added ${newCount} new papers from ${formattedSources}. Happy reading! 📚`,
        });
      }
    },
    onError: (error) => {
      toast({
        title: "💥 Update Failed", 
        description: "Couldn't fetch new papers. Check your connection and try again.",
        variant: "destructive",
      });
      console.error('Failed to update papers:', error);
    },
  });

  const handleRelevanceChange = (paperId: string, status: 'relevant' | 'irrelevant' | 'untagged') => {
    updateRelevanceMutation.mutate({ paperId, status });
  };

  const handleUpdatePapers = () => {
    // Check if all required filters are selected
    const hasDataSources = filters.sources.length > 0;
    const hasDateRange = filters.dateRange.start && filters.dateRange.end;
    const hasCategories = filters.categories.length > 0;
    
    if (!hasDataSources) {
      toast({
        title: "📚 Select Data Sources",
        description: "Choose at least one source (arXiv, bioRxiv, or ChemRxiv) to fetch papers from.",
        variant: "destructive",
      });
      return;
    }
    
    if (!hasDateRange) {
      toast({
        title: "📅 Select Date Range",
        description: "Pick a date range to specify which papers to fetch.",
        variant: "destructive",
      });
      return;
    }
    
    if (!hasCategories) {
      toast({
        title: "🏷️ Select Categories",
        description: "Choose at least one category to narrow down your search.",
        variant: "destructive",
      });
      return;
    }
    
    updatePapersMutation.mutate();
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Use pagination info from API response
  const totalPages = paginationInfo?.totalPages || 1;

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [filters]);

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-xl font-semibold text-foreground mb-2">Failed to load papers</h3>
          <p className="text-muted-foreground mb-4">
            Please check your connection and try again
          </p>
          <Button onClick={() => refetch()}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-background flex flex-col">
      <Header 
        filters={filters} 
        onFiltersChange={setFilters} 
        totalPapers={stats?.total || 0}
        onUpdatePapers={handleUpdatePapers}
        isUpdating={updatePapersMutation.isPending}
      />
      
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop Sidebar */}
        <div className="hidden lg:block">
          <Sidebar
            filters={filters}
            onFiltersChange={setFilters}
            stats={stats || { total: 0, relevant: 0, irrelevant: 0, untagged: 0, bySource: {}, byCategory: {} }}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          />
        </div>
        
        <main className="flex-1 p-4 sm:p-6 overflow-y-auto h-full">
          {/* Mobile Filter Button */}
          <div className="lg:hidden mb-4">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" className="w-full justify-start">
                  <Filter className="h-4 w-4 mr-2" />
                  Filters {filters.sources.length + filters.categories.length + filters.relevanceStatus.length > 0 && 
                    `(${filters.sources.length + filters.categories.length + filters.relevanceStatus.length})`}
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-80 p-0">
                <Sidebar
                  filters={filters}
                  onFiltersChange={setFilters}
                  stats={stats || { total: 0, relevant: 0, irrelevant: 0, untagged: 0, bySource: {}, byCategory: {} }}
                  isCollapsed={false}
                  onToggleCollapse={() => {}}
                />
              </SheetContent>
            </Sheet>
          </div>
          <div className="max-w-7xl mx-auto">
            {isLoading ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">⏳</div>
                <h3 className="text-xl font-semibold text-foreground mb-2">Loading papers...</h3>
                <p className="text-muted-foreground">
                  Please wait while we fetch the latest papers
                </p>
              </div>
            ) : papers.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📄</div>
                <h3 className="text-xl font-semibold text-foreground mb-2">No papers found</h3>
                <p className="text-muted-foreground">
                  Try adjusting your filters or search criteria
                </p>
              </div>
            ) : (
              <>
                <div className="grid gap-4 sm:gap-6 grid-cols-1 xl:grid-cols-2">
                  {papers.map((paper) => (
                    <PaperCard
                      key={paper.id}
                      paper={paper}
                      onRelevanceChange={handleRelevanceChange}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex flex-col sm:flex-row items-center justify-center gap-2 mt-8">
                    {/* First Page Button */}
                    <Button
                      variant="outline"
                      onClick={() => handlePageChange(1)}
                      disabled={currentPage === 1}
                      className="flex items-center gap-1 w-full sm:w-auto"
                    >
                      First
                    </Button>
                    
                    {/* Previous Button */}
                    <Button
                      variant="outline"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="flex items-center gap-1 w-full sm:w-auto"
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </Button>
                    
                    {/* Page Numbers */}
                    <div className="flex gap-1 overflow-x-auto">
                      {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                        let page;
                        if (totalPages <= 7) {
                          page = i + 1;
                        } else if (currentPage <= 4) {
                          page = i + 1;
                        } else if (currentPage >= totalPages - 3) {
                          page = totalPages - 6 + i;
                        } else {
                          page = currentPage - 3 + i;
                        }
                        return (
                          <Button
                            key={page}
                            variant={page === currentPage ? 'default' : 'outline'}
                            onClick={() => handlePageChange(page)}
                            className="w-10 h-10 flex-shrink-0"
                          >
                            {page}
                          </Button>
                        );
                      })}
                    </div>
                    
                    {/* Next Button */}
                    <Button
                      variant="outline"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="flex items-center gap-1 w-full sm:w-auto"
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                    
                    {/* Last Page Button */}
                    <Button
                      variant="outline"
                      onClick={() => handlePageChange(totalPages)}
                      disabled={currentPage === totalPages}
                      className="flex items-center gap-1 w-full sm:w-auto"
                    >
                      Last
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Index;
