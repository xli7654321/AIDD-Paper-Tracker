import { Search, Database, Activity, ChevronDown } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Clock } from '@/components/ui/clock';
import { FilterState } from '@/types/paper';
interface HeaderProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  totalPapers: number;
  onUpdatePapers: () => void;
  isUpdating: boolean;
}
export function Header({
  filters,
  onFiltersChange,
  totalPapers,
  onUpdatePapers,
  isUpdating
}: HeaderProps) {
  const handleSearchChange = (value: string) => {
    onFiltersChange({
      ...filters,
      searchQuery: value
    });
  };

  const handleSearchScopeChange = (scope: 'title' | 'abstract' | 'authors' | 'all') => {
    onFiltersChange({
      ...filters,
      searchScope: scope
    });
  };
  const activeFiltersCount = filters.sources.length + filters.categories.length + filters.relevanceStatus.length + (filters.searchQuery ? 1 : 0) + (filters.dateRange.start || filters.dateRange.end ? 1 : 0);
  
  // Check if we're in "All Time" mode (no date range selected)
  const isAllTimeMode = !filters.dateRange.start && !filters.dateRange.end;
  
  // Check if all required filters are selected for update
  const hasDataSources = filters.sources.length > 0;
  const hasDateRange = filters.dateRange.start && filters.dateRange.end;
  const hasCategories = filters.categories.length > 0;
  const canUpdate = hasDataSources && hasDateRange && hasCategories;
  return <header className="bg-card border-b border-border shadow-sm">
      <div className="px-4 sm:px-6 py-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex items-center gap-2">
              <Activity className="h-6 w-6 text-primary" />
              <h1 className="text-xl sm:text-2xl font-bold text-foreground">
                AIDD Paper Tracker
              </h1>
            </div>
            <div className="flex gap-2">
              <Badge variant="secondary" className="text-sm">
                {totalPapers} papers
              </Badge>
              {activeFiltersCount > 0 && <Badge variant="outline" className="text-sm">
                  {activeFiltersCount} filter{activeFiltersCount !== 1 ? 's' : ''} active
                </Badge>}
            </div>
          </div>
          {/* Real-time Clock */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-background/60 border rounded-lg">
            <Clock format="24" showSeconds={true} className="text-sm" />
          </div>
        </div>

        <div className="flex flex-col lg:flex-row items-stretch justify-between lg:items-center gap-4">
          {/* Search and Actions */}
          <div className="flex flex-col sm:flex-row gap-2 lg:gap-4 flex-1">
            <div className="flex-1 lg:max-w-md">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    placeholder={`Search in ${filters.searchScope === 'all' ? 'all fields' : filters.searchScope}...`}
                    value={filters.searchQuery} 
                    onChange={e => handleSearchChange(e.target.value)} 
                    className="pl-10 bg-background" 
                  />
                </div>
                <Select value={filters.searchScope} onValueChange={handleSearchScopeChange}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="title">Title</SelectItem>
                    <SelectItem value="abstract">Abstract</SelectItem>
                    <SelectItem value="authors">Authors</SelectItem>
                    <SelectItem value="all">All Fields</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="flex-1 sm:flex-none">
                <span className="hidden sm:inline">Export Results</span>
                <span className="sm:hidden">Export</span>
              </Button>
              <Button 
                variant="default" 
                size="sm" 
                className="flex-1 sm:flex-none bg-teal-600 hover:bg-teal-700 border-teal-600 hover:border-teal-700"
                onClick={onUpdatePapers}
                disabled={isUpdating || !canUpdate}
                title={
                  !hasDataSources ? "Please select at least one data source" :
                  !hasDateRange ? "Please select a date range" :
                  !hasCategories ? "Please select at least one category" :
                  "Update papers from external sources"
                }
              >
                {isUpdating ? (
                  <>
                    <div className="animate-spin h-4 w-4 mr-2 border-2 border-white border-t-transparent rounded-full"></div>
                    <span className="hidden sm:inline">Updating...</span>
                    <span className="sm:hidden">...</span>
                  </>
                ) : (
                  <>
                    <span className="hidden sm:inline">Update Papers</span>
                    <span className="sm:hidden">Update</span>
                  </>
                )}
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4 lg:self-end">
            {/* Powered by credits */}
            <div className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground/70 bg-muted/30 px-3 py-1.5 rounded-full border">
              <span className="font-medium">Powered by</span>
              <a 
                href="https://claude.ai/code" 
                target="_blank" 
                rel="noopener noreferrer"
                className="transition-colors font-semibold hover:underline flex items-center gap-1"
                style={{ color: '#D97757' }}
                onMouseEnter={(e) => e.target.style.color = '#C1654F'}
                onMouseLeave={(e) => e.target.style.color = '#D97757'}
              >
                <img src="/claude.svg" alt="Claude" className="w-4 h-4" />
                Claude Code
              </a>
              <span className="text-muted-foreground/50">&</span>
              <a 
                href="https://lovable.dev" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-pink-500 hover:text-pink-600 transition-colors font-semibold hover:underline flex items-center gap-1"
              >
                <img src="/lovable.svg" alt="Lovable" className="w-4 h-4" />
                Lovable
              </a>
            </div>
          </div>
        </div>
      </div>
    </header>;
}