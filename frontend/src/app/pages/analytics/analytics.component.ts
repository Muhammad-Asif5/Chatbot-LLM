import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">
      <h2>📊 Analytics</h2>

      <!-- Stats Cards -->
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

      <!-- Recent Chats -->
      <div class="card">
        <h3>Recent Conversations</h3>
        <div *ngIf="loading" class="loading">Loading...</div>
        <div *ngIf="!loading && data?.recent_chats?.length === 0" class="empty">
          No conversations yet.
        </div>
        <div *ngFor="let chat of data?.recent_chats" class="chat-item">
          <div class="chat-q">❓ {{ chat.question }}</div>
          <div class="chat-a">💬 {{ chat.answer }}</div>
          <div class="chat-meta">
            <span class="badge">{{ chat.source }}</span>
            <span class="date">{{ chat.created_at | date:'short' }}</span>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    
    h2 { color: white; font-size: 22px; margin-bottom: 24px; }
    .stats-grid {
      display: grid; grid-template-columns: repeat(3, 1fr);
      gap: 16px; margin-bottom: 24px;
    }
    .stat-card {
      background: #16213e; border-radius: 12px; padding: 24px;
      text-align: center;
    }
    .stat-icon { font-size: 32px; margin-bottom: 8px; }
    .stat-num  { color: #e94560; font-size: 36px; font-weight: bold; }
    .stat-label{ color: #888; font-size: 13px; margin-top: 4px; }
    .card {
      background: #16213e; border-radius: 12px; padding: 24px;
    }
    h3 { color: white; margin-bottom: 16px; }
    .chat-item {
      padding: 14px 0; border-bottom: 1px solid #0f3460;
    }
    .chat-item:last-child { border-bottom: none; }
    .chat-q { color: white; font-size: 14px; font-weight: bold; margin-bottom: 6px; }
    .chat-a { color: #aaa; font-size: 13px; margin-bottom: 8px; }
    .chat-meta { display: flex; gap: 10px; align-items: center; }
    .badge {
      background: #0f3460; color: #aaa;
      padding: 3px 10px; border-radius: 20px; font-size: 11px;
    }
    .date { color: #666; font-size: 11px; }
    .loading, .empty { color: #888; text-align: center; padding: 30px; }
  `]
})
export class AnalyticsComponent implements OnInit {
  data    : any = null;
  loading = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loading = true;
    this.api.getAnalytics().subscribe({
      next: (data) => { this.data = data; this.loading = false; },
      error: ()    => { this.loading = false; }
    });
  }
}