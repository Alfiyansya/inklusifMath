"use client";

import React from "react";

interface HeaderProps {
  userName: string;
  userRole: string;
  userInitial: string;
  onLogout?: () => void;
}

export function Header({ userName, userRole, userInitial, onLogout }: HeaderProps) {
  return (
    <header className="bg-bg-card border-b border-border-card">
      <div className="max-w-[1152px] mx-auto px-6 h-[72px] flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-[44px] h-[44px] bg-primary rounded-xl flex items-center justify-center text-white font-bold" aria-hidden="true">
            IM
          </div>
          <div className="flex flex-col">
            <h1 className="font-bold text-lg text-text-primary leading-tight">Inklusif Math</h1>
            <p className="text-sm text-text-secondary leading-tight">Platform Matematika Inklusif</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-end">
              <span className="font-semibold text-text-primary text-sm">{userName}</span>
              <span className="text-xs text-text-secondary">{userRole}</span>
            </div>
            <div className="w-9 h-9 rounded-full bg-primary text-white flex items-center justify-center font-semibold text-sm" aria-hidden="true">
              {userInitial}
            </div>
          </div>
          <button 
            onClick={onLogout}
            className="flex items-center gap-2 text-text-secondary hover:text-primary transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 rounded-md px-2 py-1"
            aria-label="Keluar dari akun"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            <span className="text-sm font-medium">Keluar</span>
          </button>
        </div>
      </div>
    </header>
  );
}
