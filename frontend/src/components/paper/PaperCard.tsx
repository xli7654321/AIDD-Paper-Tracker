import { useState } from 'react';
import { ExternalLink, Calendar, Users, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Paper } from '@/types/paper';
import { cn } from '@/lib/utils';

interface PaperCardProps {
  paper: Paper;
  onRelevanceChange: (paperId: string, status: 'relevant' | 'irrelevant' | 'untagged') => void;
}

export function PaperCard({ paper, onRelevanceChange }: PaperCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getRelevanceVariant = (status: string) => {
    switch (status) {
      case 'relevant': return 'relevant';
      case 'irrelevant': return 'irrelevant';
      case 'untagged': return 'untagged';
      default: return 'untagged';
    }
  };

  const getSourceColor = (source: string) => {
    switch (source.toLowerCase()) {
      case 'arxiv': return 'bg-orange-100 text-orange-800 border-orange-200 hover:bg-orange-200 hover:text-orange-900';
      case 'biorxiv': return 'bg-green-100 text-green-800 border-green-200 hover:bg-green-200 hover:text-green-900';
      case 'chemrxiv': return 'bg-purple-100 text-purple-800 border-purple-200 hover:bg-purple-200 hover:text-purple-900';
      default: return 'bg-gray-100 text-gray-800 border-gray-200 hover:bg-gray-200 hover:text-gray-900';
    }
  };

  const getSourceDisplayName = (source: string) => {
    switch (source.toLowerCase()) {
      case 'arxiv': return 'arXiv';
      case 'biorxiv': return 'bioRxiv';
      case 'chemrxiv': return 'ChemRxiv';
      default: return source;
    }
  };

  const truncateAbstract = (text: string, maxLength: number = 300) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <Card className="group hover:shadow-card-hover transition-all duration-300 border border-border/50 hover:border-primary/20 animate-fade-in flex flex-col h-full">
      <CardHeader className="pb-0 p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 sm:gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-base sm:text-lg font-semibold text-foreground leading-tight group-hover:text-primary transition-colors duration-300">
              {paper.title}
            </h3>
            
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 mt-3 text-xs sm:text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Users className="h-3 w-3 sm:h-4 sm:w-4" />
                <span className="truncate max-w-[250px] sm:max-w-[300px]">
                  {paper.authors.join(', ')}
                </span>
              </div>
              
              <div className="flex items-center gap-1">
                <Calendar className="h-3 w-3 sm:h-4 sm:w-4" />
                <span>{paper.publishedDate.toLocaleDateString()}</span>
              </div>
            </div>
          </div>
          
          <div className="flex flex-row sm:flex-col gap-2 items-end">
            <Badge className={cn("text-xs font-medium transition-colors duration-200", getSourceColor(paper.source))}>
              {getSourceDisplayName(paper.source)}
            </Badge>
            
            <Button
              variant={getRelevanceVariant(paper.relevanceStatus) as any}
              size="sm"
              className="min-w-[90px] text-xs"
            >
              {paper.relevanceStatus === 'untagged' ? 'Untagged' : 
               paper.relevanceStatus === 'relevant' ? 'Relevant' : 'Not Relevant'}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0 p-4 sm:p-6 flex-1 flex flex-col">
        {/* Categories */}
        <div className="flex flex-wrap gap-1 sm:gap-2 mb-4">
          {paper.categories.map((category) => (
            <Badge key={category} variant="secondary" className="text-xs">
              {category}
            </Badge>
          ))}
        </div>

        {/* Abstract */}
        <div className="space-y-3 flex-1">
          <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
            {isExpanded ? paper.abstract : truncateAbstract(paper.abstract, 200)}
          </p>
          
          {paper.abstract.length > 200 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-0 h-auto text-primary hover:text-primary-light text-xs sm:text-sm"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                  Read more
                </>
              )}
            </Button>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-4 pt-4 border-t border-border/50">
          <div className="flex flex-wrap gap-2">
            <Button
              variant={paper.relevanceStatus === 'relevant' ? 'relevant' : 'outline'}
              size="sm"
              onClick={() => onRelevanceChange(paper.id, 'relevant')}
              className="text-xs flex-1 sm:flex-none"
            >
              Relevant
            </Button>
            <Button
              variant={paper.relevanceStatus === 'irrelevant' ? 'irrelevant' : 'outline'}
              size="sm"
              onClick={() => onRelevanceChange(paper.id, 'irrelevant')}
              className="text-xs flex-1 sm:flex-none"
            >
              Not Relevant
            </Button>
            <Button
              variant={paper.relevanceStatus === 'untagged' ? 'untagged' : 'outline'}
              size="sm"
              onClick={() => onRelevanceChange(paper.id, 'untagged')}
              className="text-xs flex-1 sm:flex-none"
            >
              Clear
            </Button>
          </div>
          
          <div className="flex gap-2 w-full sm:w-auto">
            <Button
              variant="default"
              size="sm"
              asChild
              className="text-xs bg-purple-600 hover:bg-purple-700 text-white border-purple-600 hover:border-purple-700 flex-1 sm:flex-none"
            >
              <a href={paper.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                View Paper
              </a>
            </Button>
            {paper.pdfUrl && (
              <Button
                variant="outline"
                size="sm"
                asChild
                className="text-xs hover:text-primary flex-1 sm:flex-none"
              >
                <a href={paper.pdfUrl} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                  View PDF
                </a>
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}