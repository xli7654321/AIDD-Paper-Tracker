import React, { useState, useEffect } from 'react';
import { Clock as ClockIcon } from 'lucide-react';

interface ClockProps {
  format?: '12' | '24';
  showSeconds?: boolean;
  showDate?: boolean;
  className?: string;
}

export function Clock({ 
  format = '24', 
  showSeconds = true, 
  showDate = false,
  className = '' 
}: ClockProps) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    const options: Intl.DateTimeFormatOptions = {
      hour: '2-digit',
      minute: '2-digit',
      ...(showSeconds && { second: '2-digit' }),
      hour12: format === '12',
    };
    
    return date.toLocaleTimeString([], options);
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString([], { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <ClockIcon className="h-4 w-4 text-muted-foreground" />
      <div className="flex flex-col text-sm">
        <span className="font-mono tabular-nums text-foreground">
          {formatTime(time)}
        </span>
        {showDate && (
          <span className="text-xs text-muted-foreground">
            {formatDate(time)}
          </span>
        )}
      </div>
    </div>
  );
}