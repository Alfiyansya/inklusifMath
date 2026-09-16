"use client";

import React from "react";

interface ModuleCardProps {
  category: string;
  title: string;
  grade: string;
  teacher: string;
  features: string[];
  status: 'published' | 'draft' | 'review';
  onView?: () => void;
}

export function ModuleCard({ category, title, grade, teacher, features, status, onView }: ModuleCardProps) {
  return (
    <article 
      className="bg-bg-card border border-border-card rounded-lg overflow-hidden shadow-sm flex flex-col h-full"
      aria-label={`Modul: ${title}`}
    >
      <div className="p-6 flex-grow">
        <span className="uppercase text-xs font-semibold text-primary block mb-1">
          {category}
        </span>
        <h3 className="text-lg font-semibold text-text-primary leading-tight mb-2">
          {title}
        </h3>
        <p className="text-sm text-text-secondary mb-4">
          {grade} &middot; {teacher}
        </p>
        
        {features && features.length > 0 && (
          <div className="flex flex-wrap gap-2" aria-label="Fitur aksesibilitas modul">
            {features.map((feature, index) => (
              <span 
                key={index}
                className="bg-tag-bg text-tag-text text-xs font-medium px-2 py-1 rounded-full"
              >
                {feature}
              </span>
            ))}
          </div>
        )}
      </div>
      
      <div className="border-t border-border-card px-6 py-4 flex items-center justify-between mt-auto">
        <button 
          onClick={onView}
          className="flex-grow bg-bg-page border border-border-card rounded-md py-2 text-sm text-center font-medium text-text-primary hover:bg-primary hover:text-white hover:border-primary transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
          aria-label={`Lihat modul ${title}`}
        >
          Lihat
        </button>
        
        {status === 'published' && (
          <span className="ml-4 text-sm font-medium text-success flex items-center gap-1 flex-shrink-0" aria-label="Status: Terbit">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            Terbit
          </span>
        )}
      </div>
    </article>
  );
}
