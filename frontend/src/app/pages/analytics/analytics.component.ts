import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">

      <!-- Header -->
      <div class="page-header">
        <h2>📊 Analytics</h2>
      </div>

      <!-- Stats Section -->
      <div class="stats-section">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">💬</div>
            <div class="stat-num">{{ data?.total_questions || 0 }}</div>
            <div class="stat-label">Total Questions</div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">❓</div>
            <div class="stat-num">{{ data?.total_faqs || 0 }}</div>
            <div class="stat-label">Total FAQs</div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">📄</div>
            <div class="stat-num">{{ data?.total_documents || 0 }}</div>
            <div class="stat-label">Documents</div>
          </div>
        </div>
      </div>

      <!-- Content -->
      <div class="content-wrapper">
        <div class="card chats-container">

          <h3>Recent Conversations</h3>

          <div *ngIf="loading" class="loading">
            Loading conversations...
          </div>

          <div *ngIf="!loading && chats.length === 0" class="empty">
            No conversations yet.
          </div>

          <div *ngIf="!loading && chats.length > 0" class="chats-wrapper">

            <div *ngFor="let chat of chats" class="chat-item">
              <div class="chat-q">❓ {{ chat.question }}</div>
              <div class="chat-a">💬 {{ chat.answer }}</div>

              <div class="chat-meta">
                <span class="badge">{{ chat.source }}</span>
                <span class="date">{{ chat.created_at | date:'short' }}</span>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="pagination-container"
           *ngIf="totalChats > 0 && totalPages > 1">

        <div class="pagination-info">
          Showing {{ (currentPage - 1) * pageSize + 1 }}
          -
          {{ Math.min(currentPage * pageSize, totalChats) }}
          of {{ totalChats }} conversations
        </div>

        <div class="pagination-controls">

          <button
            class="btn-pagination"
            (click)="previousPage()"
            [disabled]="currentPage === 1">
            ← Previous
          </button>

          <div class="page-numbers">
            <button
              *ngFor="let page of getPageNumbers()"
              class="btn-page"
              [class.active]="page === currentPage"
              (click)="goToPage(page)">
              {{ page }}
            </button>
          </div>

          <button
            class="btn-pagination"
            (click)="nextPage()"
            [disabled]="currentPage === totalPages">
            Next →
          </button>

        </div>
      </div>

    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100vh;
      overflow: hidden;
    }

    .page {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: #0f1419;
      overflow: hidden;
      padding-bottom: 30px;
    }

    /* Header */
    .page-header {
      padding: 24px;
      background: #16213e;
      border-bottom: 1px solid #0f3460;
      flex-shrink: 0;
    }

    h2 {
      color: white;
      margin: 0;
      font-size: 22px;
    }

    /* Stats */
    .stats-section {
      padding: 24px;
      background: #16213e;
      border-bottom: 1px solid #0f3460;
      flex-shrink: 0;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
    }

    .stat-card {
      background: #0f3460;
      padding: 20px;
      border-radius: 12px;
      text-align: center;
    }

    .stat-icon { font-size: 28px; }
    .stat-num { color: #e94560; font-size: 32px; font-weight: bold; }
    .stat-label { color: #aaa; font-size: 13px; }

    /* Content */
    .content-wrapper {
      flex: 1;
      overflow-y: auto;
      min-height: 0;
    }

    .card {
      background: #16213e;
      margin: 0;
      padding: 24px;
      display: flex;
      flex-direction: column;
    }

    h3 {
      color: white;
      margin-bottom: 16px;
    }

    /* Chats */
    .chat-item {
      padding: 14px 0;
      border-bottom: 1px solid #0f3460;
    }

    .chat-q {
      color: white;
      font-weight: bold;
    }

    .chat-a {
      color: #aaa;
      margin-top: 4px;
    }

    .chat-meta {
      margin-top: 6px;
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .badge {
      background: #0f3460;
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 11px;
      color: #aaa;
    }

    .date {
      color: #666;
      font-size: 11px;
    }

    /* Pagination */
    .pagination-container {
      background: #16213e;
      border-top: 1px solid #0f3460;
      padding: 16px 24px;
      flex-shrink: 0;
    }

    .pagination-info {
      color: #aaa;
      text-align: center;
      margin-bottom: 10px;
      font-size: 13px;
    }

    .pagination-controls {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    .btn-pagination {
      background: #0f3460;
      border: 1px solid #e94560;
      color: white;
      padding: 8px 14px;
      border-radius: 6px;
      cursor: pointer;
    }

    .btn-pagination:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .page-numbers {
      display: flex;
      gap: 6px;
    }

    .btn-page {
      width: 34px;
      height: 34px;
      border: none;
      border-radius: 6px;
      background: #0f3460;
      color: #aaa;
      cursor: pointer;
    }

    .btn-page.active {
      background: #e94560;
      color: white;
    }

    /* States */
    .loading, .empty {
      color: #888;
      text-align: center;
      padding: 60px;
    }
  `]
})
export class AnalyticsComponent implements OnInit {

  chats: any[] = [];

  totalChats = 0;
  totalPages = 0;
  currentPage = 1;
  pageSize = 20;

  loading = false;

  Math = Math;

  data: any;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadAnalytics();
  }

  loadAnalytics() {
    this.loading = true;

    this.api.getAnalytics(this.currentPage, this.pageSize).subscribe({
      next: (res: any) => {

        this.data = res;

        const recent = res?.recent_chats;

        this.chats = recent?.items || [];
        this.totalChats = recent?.total || 0;
        this.totalPages = recent?.total_pages || 0;
        this.currentPage = recent?.page || 1;
        this.pageSize = recent?.page_size || 10;

        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.loading = false;
      }
    });
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadAnalytics();
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadAnalytics();
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadAnalytics();
    }
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const max = 5;

    let start = Math.max(1, this.currentPage - Math.floor(max / 2));
    let end = Math.min(this.totalPages, start + max - 1);

    if (end - start < max) {
      start = Math.max(1, end - max + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }
}