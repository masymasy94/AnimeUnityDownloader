import { useState, useEffect, useRef } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (query.trim().length >= 2) {
      debounceRef.current = setTimeout(() => {
        onSearch(query.trim());
      }, 400);
    }
    return () => clearTimeout(debounceRef.current);
  }, [query, onSearch]);

  return (
    <div className="w-full max-w-[660px] mx-auto">
      <div
        className="flex items-center rounded-[5px]"
        style={{ boxShadow: '0 0 14px 1px rgba(16,16,16,0.2)' }}
      >
        {/* Search icon */}
        <div className="flex items-center justify-center w-[46px] h-[51px] bg-bg-card rounded-l-[5px]">
          {isLoading ? (
            <span className="inline-block w-[14px] h-[14px] border-2 border-text-secondary/30 border-t-text-secondary rounded-full animate-spin" />
          ) : (
            <svg
              className="w-[14px] h-[14px] text-text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          )}
        </div>
        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Cerca un anime"
          autoComplete="off"
          className="flex-1 h-[51px] bg-bg-card text-text-white text-[15px] border-none outline-none rounded-r-[5px] px-3 placeholder-text-secondary"
        />
      </div>
    </div>
  );
}
