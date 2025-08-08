import { useState, useEffect } from 'react';
import { Calendar, Filter, BarChart3, ChevronLeft, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { format } from 'date-fns';
import { FilterState, PaperStats } from '@/types/paper';
import { categories, sources, categoriesBySource } from '@/data/mockPapers';

interface SidebarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  stats: PaperStats;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export function Sidebar({ filters, onFiltersChange, stats, isCollapsed, onToggleCollapse }: SidebarProps) {
  const [dateRangeOption, setDateRangeOption] = useState<string>('all-time');
  const [isStartCalendarOpen, setIsStartCalendarOpen] = useState(false);
  const [isEndCalendarOpen, setIsEndCalendarOpen] = useState(false);

  // Initialize date range if not set
  useEffect(() => {
    if (!filters.dateRange.start && !filters.dateRange.end) {
      // Default to all-time (no date filtering)
      onFiltersChange({
        ...filters,
        dateRange: { start: null, end: null }
      });
    }
  }, []);

  const handleSourceChange = (source: string, checked: boolean) => {
    let newSources: string[];
    
    if (source === 'all') {
      // If "All Sources" is checked, select all sources; if unchecked, clear all
      newSources = checked ? ['arxiv', 'biorxiv', 'chemrxiv'] : [];
    } else {
      newSources = checked
        ? [...filters.sources, source]
        : filters.sources.filter(s => s !== source);
    }
    
    // Filter out categories that are no longer available based on selected sources
    const availableCategories = newSources.reduce((acc: string[], sourceName) => {
      const sourceKey = Object.keys(categoriesBySource).find(key => 
        key.toLowerCase() === sourceName
      ) as keyof typeof categoriesBySource;
      
      if (sourceKey && categoriesBySource[sourceKey]) {
        acc.push(...categoriesBySource[sourceKey].map(cat => cat.id));
      }
      return acc;
    }, []);
    
    const newCategories = filters.categories.filter(categoryId => 
      availableCategories.includes(categoryId)
    );
    
    onFiltersChange({ 
      ...filters, 
      sources: newSources,
      categories: newCategories
    });
  };

  const handleCategoryChange = (category: string, checked: boolean) => {
    const newCategories = checked
      ? [...filters.categories, category]
      : filters.categories.filter(c => c !== category);
    onFiltersChange({ ...filters, categories: newCategories });
  };

  const handleRelevanceChange = (status: string, checked: boolean) => {
    const newStatus = checked
      ? [...filters.relevanceStatus, status]
      : filters.relevanceStatus.filter(s => s !== status);
    onFiltersChange({ ...filters, relevanceStatus: newStatus });
  };

  const handleDateRangeChange = (option: string) => {
    setDateRangeOption(option);
    const now = new Date();
    const endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate()); // Today at 00:00:00
    let startDate: Date;

    switch (option) {
      case 'all-time':
        // Set to null to indicate no date filtering
        onFiltersChange({
          ...filters,
          dateRange: { start: null, end: null }
        });
        return;
      case 'today':
        startDate = new Date(endDate);
        break;
      case 'last-week':
        startDate = new Date(endDate);
        startDate.setDate(startDate.getDate() - 7);
        break;
      case 'last-month':
        startDate = new Date(endDate);
        startDate.setDate(startDate.getDate() - 30);
        break;
      case 'last-3-months':
        startDate = new Date(endDate);
        startDate.setDate(startDate.getDate() - 90);
        break;
      case 'custom':
        // Don't update dates for custom, let user pick
        return;
      default:
        startDate = new Date(endDate);
        startDate.setDate(startDate.getDate() - 30);
    }

    if (option !== 'custom') {
      onFiltersChange({
        ...filters,
        dateRange: { start: startDate, end: endDate }
      });
    }
  };

  const handleCustomDateChange = (start: Date | null, end: Date | null) => {
    onFiltersChange({
      ...filters,
      dateRange: { start, end }
    });
  };

  const clearAllFilters = () => {
    setDateRangeOption('all-time');
    
    onFiltersChange({
      sources: ['arxiv', 'biorxiv', 'chemrxiv'],
      categories: [],
      relevanceStatus: [],
      dateRange: { start: null, end: null },
      searchQuery: '',
      searchScope: 'title',
    });
  };

  // Helper function to check if a category should be enabled based on selected sources
  const isCategoryEnabled = (categoryId: string) => {
    // Find which source this category belongs to
    const sourceName = Object.keys(categoriesBySource).find(source => 
      categoriesBySource[source as keyof typeof categoriesBySource]?.some(cat => cat.id === categoryId)
    );
    
    if (!sourceName) return false;
    
    // Check if the corresponding source is selected
    return filters.sources.includes(sourceName.toLowerCase());
  };

  if (isCollapsed) {
    return (
      <div className="w-14 bg-card border-r border-border shadow-sidebar flex flex-col items-center py-4 space-y-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="h-8 w-8"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <Separator />
        <div className="flex flex-col items-center space-y-2">
          <Filter className="h-5 w-5 text-muted-foreground" />
          <BarChart3 className="h-5 w-5 text-muted-foreground" />
          <Calendar className="h-5 w-5 text-muted-foreground" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 bg-card border-r border-border shadow-sidebar animate-slide-in h-full">
      <div className="p-4 sm:p-6 space-y-4 sm:space-y-6 h-full overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-5 w-5 text-primary" />
            <h2 className="font-semibold text-foreground">Filters</h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleCollapse}
            className="h-8 w-8"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </div>

        {/* Statistics */}
        <Card className="bg-gradient-to-r from-primary/5 to-primary-light/5 border-primary/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Paper Statistics
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center p-2 bg-card rounded-lg border">
                <div className="text-2xl font-bold text-primary">{stats.total}</div>
                <div className="text-xs text-muted-foreground">Total</div>
              </div>
              <div className="text-center p-2 bg-relevant-light rounded-lg border border-relevant/20">
                <div className="text-2xl font-bold text-relevant">{stats.relevant}</div>
                <div className="text-xs text-relevant">Relevant</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center p-2 bg-irrelevant-light rounded-lg border border-irrelevant/20">
                <div className="text-2xl font-bold text-irrelevant">{stats.irrelevant}</div>
                <div className="text-xs text-irrelevant">Not Relevant</div>
              </div>
              <div className="text-center p-2 bg-untagged-light rounded-lg border border-untagged/20">
                <div className="text-2xl font-bold text-untagged">{stats.untagged}</div>
                <div className="text-xs text-untagged">Untagged</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data Sources */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Data Sources</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* All Sources option */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="source-all"
                  checked={filters.sources.length === 3 && filters.sources.includes('arxiv') && filters.sources.includes('biorxiv') && filters.sources.includes('chemrxiv')}
                  onCheckedChange={(checked) => handleSourceChange('all', checked as boolean)}
                />
                <label
                  htmlFor="source-all"
                  className="text-sm cursor-pointer"
                >
                  All Sources
                </label>
              </div>
              <Badge variant="outline" className="text-xs">
                {stats.total || 0}
              </Badge>
            </div>
            
            {sources.map((source) => (
              <div key={source} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id={`source-${source}`}
                    checked={filters.sources.includes(source.toLowerCase())}
                    onCheckedChange={(checked) => handleSourceChange(source.toLowerCase(), checked as boolean)}
                  />
                  <label
                    htmlFor={`source-${source}`}
                    className="text-sm cursor-pointer"
                  >
                    {source}
                  </label>
                </div>
                <Badge variant="outline" className="text-xs">
                  {stats.bySource[source] || 0}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Date Range */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Date Range</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Select value={dateRangeOption} onValueChange={handleDateRangeChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select date range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all-time">All Time</SelectItem>
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="last-week">Last Week</SelectItem>
                <SelectItem value="last-month">Last Month</SelectItem>
                <SelectItem value="last-3-months">Last 3 Months</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>

            {dateRangeOption === 'custom' && (
              <div className="space-y-3">
                <div className="text-xs font-medium text-muted-foreground">Custom Date Range</div>
                <div className="space-y-2">
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Start Date</div>
                    <Popover open={isStartCalendarOpen} onOpenChange={setIsStartCalendarOpen}>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className="w-full justify-start text-left font-normal"
                          onClick={() => setIsStartCalendarOpen(true)}
                        >
                          <Calendar className="mr-2 h-4 w-4" />
                          {filters.dateRange.start ? format(filters.dateRange.start, 'MMM dd, yyyy') : 'Pick start date'}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <CalendarComponent
                          mode="single"
                          selected={filters.dateRange.start || undefined}
                          onSelect={(date) => {
                            handleCustomDateChange(date || null, filters.dateRange.end);
                            setIsStartCalendarOpen(false);
                          }}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                  
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">End Date</div>
                    <Popover open={isEndCalendarOpen} onOpenChange={setIsEndCalendarOpen}>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className="w-full justify-start text-left font-normal"
                          onClick={() => setIsEndCalendarOpen(true)}
                        >
                          <Calendar className="mr-2 h-4 w-4" />
                          {filters.dateRange.end ? format(filters.dateRange.end, 'MMM dd, yyyy') : 'Pick end date'}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <CalendarComponent
                          mode="single"
                          selected={filters.dateRange.end || undefined}
                          onSelect={(date) => {
                            handleCustomDateChange(filters.dateRange.start, date || null);
                            setIsEndCalendarOpen(false);
                          }}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>
                
                {filters.dateRange.start && filters.dateRange.end && (
                  <div className="text-xs text-muted-foreground">
                    {filters.dateRange.start > filters.dateRange.end ? (
                      <span className="text-red-500">Start date must be before end date</span>
                    ) : (
                      <span>
                        {Math.ceil((filters.dateRange.end.getTime() - filters.dateRange.start.getTime()) / (1000 * 60 * 60 * 24)) + 1} days selected
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}

            {dateRangeOption === 'all-time' ? (
              <div className="text-xs text-muted-foreground">
                All papers regardless of date
              </div>
            ) : dateRangeOption !== 'custom' && filters.dateRange.start && filters.dateRange.end && (
              <div className="text-xs text-muted-foreground">
                {format(filters.dateRange.start, 'MMM dd, yyyy')} - {format(filters.dateRange.end, 'MMM dd, yyyy')}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Categories */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* arXiv Categories */}
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-2">arXiv</div>
              <div className="space-y-2">
                {categoriesBySource.arXiv?.map((category) => {
                  const enabled = isCategoryEnabled(category.id);
                  return (
                    <div key={category.id} className={`flex items-center justify-between ${!enabled ? 'opacity-50' : ''}`}>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={`category-${category.id}`}
                          checked={filters.categories.includes(category.id)}
                          onCheckedChange={(checked) => enabled && handleCategoryChange(category.id, checked as boolean)}
                          disabled={!enabled}
                        />
                        <label
                          htmlFor={`category-${category.id}`}
                          className={`text-sm ${enabled ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                        >
                          {category.id}
                        </label>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {stats.byCategory[category.id] || 0}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </div>

            <Separator />

            {/* bioRxiv Categories */}
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-2">bioRxiv</div>
              <div className="space-y-2">
                {categoriesBySource.bioRxiv?.map((category) => {
                  const enabled = isCategoryEnabled(category.id);
                  return (
                    <div key={category.id} className={`flex items-center justify-between ${!enabled ? 'opacity-50' : ''}`}>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={`category-${category.id}`}
                          checked={filters.categories.includes(category.id)}
                          onCheckedChange={(checked) => enabled && handleCategoryChange(category.id, checked as boolean)}
                          disabled={!enabled}
                        />
                        <label
                          htmlFor={`category-${category.id}`}
                          className={`text-sm ${enabled ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                        >
                          {category.id}
                        </label>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {stats.byCategory[category.id] || 0}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </div>

            <Separator />

            {/* ChemRxiv Categories */}
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-2">ChemRxiv</div>
              <div className="space-y-2">
                {categoriesBySource.ChemRxiv?.map((category) => {
                  const enabled = isCategoryEnabled(category.id);
                  return (
                    <div key={category.id} className={`flex items-center justify-between ${!enabled ? 'opacity-50' : ''}`}>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={`category-${category.id}`}
                          checked={filters.categories.includes(category.id)}
                          onCheckedChange={(checked) => enabled && handleCategoryChange(category.id, checked as boolean)}
                          disabled={!enabled}
                        />
                        <label
                          htmlFor={`category-${category.id}`}
                          className={`text-sm ${enabled ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                        >
                          {category.name}
                        </label>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {stats.byCategory[category.id] || 0}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Relevance Status */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Relevance Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { key: 'relevant', label: 'Relevant', count: stats.relevant },
              { key: 'irrelevant', label: 'Not Relevant', count: stats.irrelevant },
              { key: 'untagged', label: 'Untagged', count: stats.untagged },
            ].map((status) => (
              <div key={status.key} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id={`status-${status.key}`}
                    checked={filters.relevanceStatus.includes(status.key)}
                    onCheckedChange={(checked) => handleRelevanceChange(status.key, checked as boolean)}
                  />
                  <label
                    htmlFor={`status-${status.key}`}
                    className="text-sm cursor-pointer"
                  >
                    {status.label}
                  </label>
                </div>
                <Badge variant="outline" className="text-xs">
                  {status.count}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Clear Filters */}
        <Button
          variant="outline"
          onClick={clearAllFilters}
          className="w-full"
          disabled={
            filters.sources.length === 3 && filters.sources.includes('arxiv') && filters.sources.includes('biorxiv') && filters.sources.includes('chemrxiv') &&
            filters.categories.length === 0 &&
            filters.relevanceStatus.length === 0 &&
            dateRangeOption === 'all-time' &&
            !filters.searchQuery
          }
        >
          Clear All Filters
        </Button>
      </div>
    </div>
  );
}