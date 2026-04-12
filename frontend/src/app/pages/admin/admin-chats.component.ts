import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService } from '../../services/admin.service';

@Component({
  selector: 'app-admin-chats',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">
      <div class="page-header">
        <h2>💬 All Conversations</h2>
        <span class="refresh-btn" (click)="load()">🔄 Refresh</span>
      </div>

      <div *ngIf="loading" class="loading">Loading conversations...</div>

      <div *ngIf="!loading && chats.length === 0" class="empty">
        No conversations on the platform yet.
      </div>

      <div *ngFor="let c of chats" class="chat-card">
        <div class="chat-header">
          <div class="user-pill">
            <span class="uavatar">{{ c.user_name?.charAt(0)?.toUpperCase() }}</span>
            <span class="uname">{{ c.user_name }}</span>
            <span class="uemail">{{ c.user_email }}</span>
          </div>
          <div class="chat-meta">
            <span class="badge">{{ c.source }}</span>
            <span class="badge lang">{{ c.language }}</span>
            <span class="date">{{ c.created_at | date:'medium' }}</span>
          </div>
        </div>
        <div class="chat-q">❓ {{ c.question }}</div>
        <div class="chat-a">💬 {{ c.answer }}</div>
      </div>
    </div>
  `,
  styles: [`
    .page { max-width: 860px; }
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
  `]
})
export class AdminChatsComponent implements OnInit {
  chats  : any[] = [];
  loading = false;

  constructor(private adminSvc: AdminService) {}

  ngOnInit() { this.load(); }

  load() {
    this.loading = true;
    this.adminSvc.getStats().subscribe({
      next: (res: any) => {
        this.chats   = (res?.data ?? res)?.recent_chats ?? [];
        this.loading = false;
      },
      error: () => { this.loading = false; }
    });
  }
}