import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AdminService } from '../../services/admin.service';

@Component({
  selector: 'app-admin-overview',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="page">
      <div class="page-header">
        <h2>📊 Platform Overview</h2>
        <span class="refresh-btn" (click)="load()">🔄 Refresh</span>
      </div>

      <div *ngIf="loading" class="loading">Loading platform stats...</div>

      <ng-container *ngIf="!loading && stats">

        <!-- Stats Grid -->
        <div class="stats-grid">
          <div class="stat-card purple">
            <div class="stat-icon">👥</div>
            <div class="stat-num">{{ stats.overview.total_users }}</div>
            <div class="stat-label">Total Users</div>
            <div class="stat-sub">
              {{ stats.overview.active_users }} active ·
              {{ stats.overview.inactive_users }} inactive
            </div>
          </div>
          <div class="stat-card blue">
            <div class="stat-icon">💬</div>
            <div class="stat-num">{{ stats.overview.total_chats }}</div>
            <div class="stat-label">Total Chats</div>
          </div>
          <div class="stat-card green">
            <div class="stat-icon">❓</div>
            <div class="stat-num">{{ stats.overview.total_faqs }}</div>
            <div class="stat-label">Total FAQs</div>
          </div>
          <div class="stat-card orange">
            <div class="stat-icon">📄</div>
            <div class="stat-num">{{ stats.overview.total_documents }}</div>
            <div class="stat-label">Documents</div>
          </div>
          <div class="stat-card teal">
            <div class="stat-icon">📝</div>
            <div class="stat-num">{{ stats.overview.total_kb }}</div>
            <div class="stat-label">KB Articles</div>
          </div>
        </div>

        <div class="two-col">
          <!-- Top Users by Chat Volume -->
          <div class="card">
            <h3>🏆 Top Users by Chat Volume</h3>
            <div *ngIf="stats.top_users.length === 0" class="empty">No data yet.</div>
            <div *ngFor="let u of stats.top_users; let i = index" class="top-user-row">
              <div class="rank">#{{ i + 1 }}</div>
              <div class="user-info">
                <div class="uname">{{ u.name }}</div>
                <div class="uemail">{{ u.email }}</div>
              </div>
              <div class="chat-count">{{ u.chat_count }} chats</div>
            </div>
          </div>

          <!-- Recent Platform Chats -->
          <div class="card">
            <h3>🕐 Recent Conversations</h3>
            <div *ngIf="stats.recent_chats.length === 0" class="empty">No chats yet.</div>
            <div *ngFor="let c of stats.recent_chats" class="chat-row">
              <div class="chat-user">{{ c.user_name }}</div>
              <div class="chat-q">{{ c.question | slice:0:80 }}{{ c.question?.length > 80 ? '...' : '' }}</div>
              <div class="chat-meta">
                <span class="badge">{{ c.source }}</span>
                <span class="badge lang">{{ c.language }}</span>
                <span class="date">{{ c.created_at | date:'short' }}</span>
              </div>
            </div>
          </div>
        </div>

      </ng-container>
    </div>
  `,
  styles: [`
    .page { max-width: 1100px; }
    .page-header {
      display: flex; justify-content: space-between;
      align-items: center; margin-bottom: 28px;
    }
    h2 { color: white; font-size: 22px; margin: 0; }
    .refresh-btn {
      color: #7c3aed; cursor: pointer; font-size: 13px;
      padding: 6px 14px; border: 1px solid #7c3aed;
      border-radius: 6px; transition: all 0.2s;
    }
    .refresh-btn:hover { background: #7c3aed; color: white; }

    .stats-grid {
      display: grid; grid-template-columns: repeat(5, 1fr);
      gap: 16px; margin-bottom: 28px;
    }
    .stat-card {
      border-radius: 12px; padding: 20px;
      text-align: center; border: 1px solid transparent;
    }
    .stat-card.purple { background: #1e1040; border-color: #7c3aed33; }
    .stat-card.blue   { background: #0c1a40; border-color: #3b82f633; }
    .stat-card.green  { background: #0c2010; border-color: #22c55e33; }
    .stat-card.orange { background: #201408; border-color: #f9731633; }
    .stat-card.teal   { background: #061820; border-color: #06b6d433; }

    .stat-icon { font-size: 28px; margin-bottom: 8px; }
    .stat-num  { font-size: 32px; font-weight: 700; color: white; }
    .stat-label{ color: #9ca3af; font-size: 12px; margin-top: 4px; }
    .stat-sub  { color: #6b7280; font-size: 11px; margin-top: 4px; }

    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

    .card {
      background: #0f0f23; border: 1px solid #1a1a3e;
      border-radius: 12px; padding: 22px;
    }
    h3 { color: white; font-size: 15px; margin: 0 0 16px; }

    .top-user-row {
      display: flex; align-items: center; gap: 12px;
      padding: 10px 0; border-bottom: 1px solid #1a1a3e;
    }
    .top-user-row:last-child { border-bottom: none; }
    .rank  { color: #7c3aed; font-weight: 700; font-size: 15px; width: 28px; }
    .user-info { flex: 1; }
    .uname  { color: white; font-size: 13px; font-weight: 600; }
    .uemail { color: #6b7280; font-size: 11px; }
    .chat-count { color: #7c3aed; font-size: 13px; font-weight: 600; white-space: nowrap; }

    .chat-row {
      padding: 10px 0; border-bottom: 1px solid #1a1a3e;
    }
    .chat-row:last-child { border-bottom: none; }
    .chat-user { color: #7c3aed; font-size: 12px; font-weight: 600; margin-bottom: 3px; }
    .chat-q    { color: #d1d5db; font-size: 13px; margin-bottom: 6px; }
    .chat-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .badge {
      background: #1a1a3e; color: #9ca3af;
      padding: 2px 8px; border-radius: 20px; font-size: 11px;
    }
    .badge.lang { background: #1e1040; color: #7c3aed; }
    .date  { color: #6b7280; font-size: 11px; }
    .loading, .empty { color: #6b7280; text-align: center; padding: 30px; }
  `]
})
export class AdminOverviewComponent implements OnInit {
  stats  : any    = null;
  loading = false;

  constructor(private adminSvc: AdminService) {}

  ngOnInit() { this.load(); }

  load() {
    this.loading = true;
    this.adminSvc.getStats().subscribe({
      next: (res: any) => { this.stats = res?.data ?? res; this.loading = false; },
      error: ()        => { this.loading = false; }
    });
  }
}