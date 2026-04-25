import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { AdminService } from '../../services/admin.service';

@Component({
  selector: 'app-admin-chats',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">

      <div class="page-header">
        <h2>💬 All Conversations</h2>
        <span class="refresh-btn" (click)="refreshChats()">🔄 Refresh</span>
      </div>

      <div class="content-wrapper">
        <div *ngIf="loading" class="loading">Loading conversations...</div>

        <div *ngIf="!loading && chats.length === 0" class="empty">
          No conversations on the platform yet.
        </div>

        <div *ngFor="let c of chats; trackBy: trackByChat" class="chat-card">
          <div class="chat-header">
            <div class="user-pill">
              <span class="uavatar">
                {{ c.user_name?.charAt(0)?.toUpperCase() || '?' }}
              </span>
              <span class="uname">{{ c.user_name || 'Unknown User' }}</span>
              <span class="uemail">{{ c.user_email || '-' }}</span>
            </div>

            <div class="chat-meta">
              <span class="badge">{{ c.source || 'web' }}</span>
              <span class="badge lang">{{ c.language || 'en' }}</span>
              <span class="date">{{ c.created_at | date:'medium' }}</span>
            </div>
          </div>

          <div class="chat-q">❓ {{ c.question }}</div>
          <div class="chat-a">💬 {{ c.answer }}</div>
        </div>
      </div>

      <!-- PAGINATION -->
      <div class="pagination-container" *ngIf="totalItems > 0">
        <div class="pagination-info">
          Showing
          {{ (currentPage - 1) * pageSize + 1 }}
          -
          {{ Math.min(currentPage * pageSize, totalItems) }}
          of {{ totalItems }} Conversations
        </div>

        <div class="pagination-controls" *ngIf="totalPages > 1">
          <button
            (click)="previousPage()"
            class="btn-pagination"
            [disabled]="currentPage === 1">
            ← Previous
          </button>

          <div class="page-numbers">
            <button
              *ngFor="let page of getPageNumbers()"
              (click)="goToPage(page)"
              class="btn-page"
              [class.active]="page === currentPage">
              {{ page }}
            </button>
          </div>

          <button
            (click)="nextPage()"
            class="btn-pagination"
            [disabled]="currentPage === totalPages">
            Next →
          </button>
        </div>
      </div>

    </div>
  `,
  styles: [`
     .page {
      display: flex;
      flex-direction: column;
      height: 100%;
      width: 100%;
      overflow: hidden;
      background: #0f1419;
      padding-bottom: 25px;
    }
    .page-header {
      display: flex; justify-content: space-between;
      align-items: center; margin-bottom: 24px;
    }
    h2 { color: white; font-size: 22px; margin: 0; }
    .refresh-btn {
      color: #7c3aed; cursor: pointer; font-size: 13px;
      padding: 6px 14px; border: 1px solid #7c3aed;
      border-radius: 6px; transition: all 0.2s;
    }
    .refresh-btn:hover { background: #7c3aed; color: white; }

    .chat-card {
      background: #0f0f23; border: 1px solid #1a1a3e;
      border-radius: 12px; padding: 18px; margin-bottom: 12px;
    }
    .chat-header {
      display: flex; justify-content: space-between;
      align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;
    }
    .user-pill { display: flex; align-items: center; gap: 8px; }
    .uavatar {
      width: 28px; height: 28px; background: #7c3aed;
      border-radius: 50%; display: flex; align-items: center;
      justify-content: center; color: white; font-weight: 700; font-size: 12px;
    }
    .uname  { color: white; font-size: 13px; font-weight: 600; }
    .uemail { color: #6b7280; font-size: 12px; }
    .chat-meta { display: flex; gap: 8px; align-items: center; }
    .badge {
      background: #1a1a3e; color: #9ca3af;
      padding: 2px 8px; border-radius: 20px; font-size: 11px;
    }
    .badge.lang { background: #1e1040; color: #7c3aed; }
    .date { color: #6b7280; font-size: 11px; }
    .chat-q { color: white; font-size: 14px; font-weight: 600; margin-bottom: 8px; }
    .chat-a { color: #9ca3af; font-size: 13px; line-height: 1.6; }
    .loading, .empty { color: #6b7280; text-align: center; padding: 40px; }

:host {
      display: block;
      height: 100vh;
      width: 100%;
      overflow: hidden;
    }

    /* ─────────────────────────────────────────────────────── */
    /* PAGINATION STYLES: Fixed at Bottom */
    /* ─────────────────────────────────────────────────────── */
     .pagination-container {
      background: #16213e;
      border-top: 1px solid #0f3460;
      padding: 16px 24px;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin: 0;
      min-height: fit-content;
    }
      
    .pagination-info {
      color: #aaa;
      font-size: 13px;
      text-align: center;
      margin: 0;
    }
    .pagination-controls {
      display: flex;
      gap: 12px;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      margin: 0;
    }

    .btn-pagination {
      padding: 8px 16px;
      background: #0f3460;
      color: white;
      border: 1px solid #e94560;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      transition: all 0.2s;
      margin: 0;
    }
    .btn-pagination:hover:not(:disabled) {
      background: #e94560;
      color: white;
    }
    .btn-pagination:disabled {
      opacity: 0.4;
      cursor: not-allowed;
      border-color: #555;
    }

    .page-numbers {
      display: flex;
      gap: 6px;
      margin: 0;
    }
    .btn-page {
      width: 36px;
      height: 36px;
      padding: 0;
      background: #0f3460;
      color: #aaa;
      border: 1px solid #0f3460;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      transition: all 0.2s;
      margin: 0;
    }
    .btn-page:hover {
      border-color: #e94560;
      color: #e94560;
    }
    .btn-page.active {
      background: #e94560;
      color: white;
      border-color: #e94560;
    }


/* ─────────────────────────────────────────────────────── */
    /* SCROLLBAR STYLING */
    /* ─────────────────────────────────────────────────────── */
    .content-wrapper {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}
  
    .content-wrapper::-webkit-scrollbar {
      width: 8px;
    }
    .content-wrapper::-webkit-scrollbar-track {
      background: #0f1419;
      border-radius: 10px;
    }
    .content-wrapper::-webkit-scrollbar-thumb {
      background: #0f3460;
      border-radius: 10px;
      border: 2px solid #0f1419;
    }
    .content-wrapper::-webkit-scrollbar-thumb:hover {
      background: #e94560;
    }

    
  `]
})
export class AdminChatsComponent implements OnInit {

  chats: any[] = [];
  loading = false;

  currentPage = 1;
  pageSize = 10;
  totalItems = 0;
  totalPages = 0;

  Math = Math;

  constructor(private adminSvc: AdminService) {}

  ngOnInit(): void {
    this.loadChats();
  }

  loadChats(): void {
    this.loading = true;

    this.adminSvc
      .getRecentConversations(this.currentPage, this.pageSize)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (res: any) => {
          const data = res?.data ?? res;

          this.chats = data.recent_chats || [];

          this.totalItems = data.pagination?.total || 0;
          this.currentPage = data.pagination?.page || 1;
          this.pageSize = data.pagination?.page_size || 10;

          this.totalPages =
            data.pagination?.total_pages ||
            Math.ceil(this.totalItems / this.pageSize);
        },
        error: (err) => {
          console.error('Failed to load chats:', err);
        }
      });
  }

  refreshChats(): void {
    this.loadChats();
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadChats();
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadChats();
    }
  }

  goToPage(page: number): void {
    if (page !== this.currentPage && page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadChats();
    }
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;

    let start = Math.max(1, this.currentPage - 2);
    let end = Math.min(this.totalPages, start + maxVisible - 1);

    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }

  trackByChat(index: number, item: any): any {
    return item.id || index;
  }
}