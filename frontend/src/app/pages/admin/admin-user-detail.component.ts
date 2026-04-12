import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { AdminService } from '../../services/admin.service';

@Component({
  selector: 'app-admin-user-detail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">

      <!-- Back -->
      <div class="back-row" (click)="router.navigate(['/admin/users'])">
        ← Back to Users
      </div>

      <div *ngIf="loading" class="loading">Loading user...</div>

      <ng-container *ngIf="!loading && user">

        <!-- User Header -->
        <div class="user-header">
          <div class="big-avatar">{{ user.name.charAt(0).toUpperCase() }}</div>
          <div class="user-meta">
            <h2>{{ user.name }}
              <span *ngIf="user.is_admin" class="role-badge admin">👑 Admin</span>
              <span *ngIf="!user.is_admin" class="role-badge user">User</span>
            </h2>
            <div class="meta-row">
              <span>📧 {{ user.email }}</span>
              <span class="plan-badge plan-{{ user.plan }}">{{ user.plan }}</span>
              <span [class]="user.is_active ? 'active-dot on' : 'active-dot off'">
                {{ user.is_active ? '🟢 Active' : '🔴 Inactive' }}
              </span>
            </div>
            <div class="joined">Joined {{ user.created_at | date:'longDate' }}</div>
          </div>

          <!-- Quick Stats -->
          <div class="quick-stats">
            <div class="qs-item">
              <div class="qs-num">{{ user.stats?.faqs ?? 0 }}</div>
              <div class="qs-label">FAQs</div>
            </div>
            <div class="qs-item">
              <div class="qs-num">{{ user.stats?.documents ?? 0 }}</div>
              <div class="qs-label">Docs</div>
            </div>
            <div class="qs-item">
              <div class="qs-num">{{ user.stats?.chats ?? 0 }}</div>
              <div class="qs-label">Chats</div>
            </div>
            <div class="qs-item">
              <div class="qs-num">{{ user.stats?.kb ?? 0 }}</div>
              <div class="qs-label">KB</div>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tabs">
          <button [class.active]="tab==='faqs'"  (click)="switchTab('faqs')">❓ FAQs</button>
          <button [class.active]="tab==='docs'"  (click)="switchTab('docs')">📄 Documents</button>
          <button [class.active]="tab==='chats'" (click)="switchTab('chats')">💬 Chat Logs</button>
        </div>

        <!-- Tab Content -->
        <div class="card">

          <!-- FAQs Tab -->
          <ng-container *ngIf="tab==='faqs'">
            <div *ngIf="tabLoading" class="loading">Loading FAQs...</div>
            <div *ngIf="!tabLoading && faqs.length === 0" class="empty">No FAQs yet.</div>
            <div *ngFor="let f of faqs" class="faq-item">
              <div class="faq-q">{{ f.question }}</div>
              <div class="faq-a">{{ f.answer }}</div>
              <span class="badge">{{ f.category }}</span>
            </div>
          </ng-container>

          <!-- Documents Tab -->
          <ng-container *ngIf="tab==='docs'">
            <div *ngIf="tabLoading" class="loading">Loading documents...</div>
            <div *ngIf="!tabLoading && docs.length === 0" class="empty">No documents yet.</div>
            <div *ngFor="let d of docs" class="doc-item">
              <span class="doc-icon">📄</span>
              <div class="doc-info">
                <div class="doc-name">{{ d.filename }}</div>
                <div class="doc-date">{{ d.created_at | date:'medium' }}</div>
              </div>
            </div>
          </ng-container>

          <!-- Chats Tab -->
          <ng-container *ngIf="tab==='chats'">
            <div *ngIf="tabLoading" class="loading">Loading chats...</div>
            <div *ngIf="!tabLoading && chats.length === 0" class="empty">No chat history yet.</div>
            <div *ngFor="let c of chats" class="chat-item">
              <div class="chat-q">❓ {{ c.question }}</div>
              <div class="chat-a">💬 {{ c.answer }}</div>
              <div class="chat-meta">
                <span class="badge">{{ c.source }}</span>
                <span class="badge lang">{{ c.language }}</span>
                <span class="date">{{ c.created_at | date:'short' }}</span>
              </div>
            </div>
          </ng-container>

        </div>
      </ng-container>
    </div>
  `,
  styles: [`

    .back-row {
      color: #7c3aed; cursor: pointer; font-size: 13px;
      margin-bottom: 24px; display: inline-flex; align-items: center; gap: 6px;
    }
    .back-row:hover { text-decoration: underline; }

    .user-header {
      background: #0f0f23; border: 1px solid #1a1a3e;
      border-radius: 14px; padding: 24px;
      display: flex; align-items: flex-start; gap: 20px;
      margin-bottom: 24px; flex-wrap: wrap;
    }
    .big-avatar {
      width: 60px; height: 60px; background: #7c3aed;
      border-radius: 50%; display: flex; align-items: center;
      justify-content: center; color: white; font-weight: 700;
      font-size: 24px; flex-shrink: 0;
    }
    .user-meta { flex: 1; }
    h2 { color: white; font-size: 20px; margin: 0 0 8px; display: flex; align-items: center; gap: 10px; }

    .role-badge {
      font-size: 11px; padding: 3px 10px; border-radius: 20px; font-weight: 600;
    }
    .role-badge.admin { background: #1e1040; color: #f59e0b; }
    .role-badge.user  { background: #1a1a3e; color: #9ca3af; }

    .meta-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; color: #9ca3af; font-size: 13px; }
    .plan-badge {
      padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;
    }
    .plan-free       { background: #1a1a3e; color: #9ca3af; }
    .plan-pro        { background: #1e1040; color: #7c3aed; }
    .plan-enterprise { background: #20100a; color: #f97316; }

    .active-dot { font-size: 12px; }
    .joined { color: #6b7280; font-size: 12px; margin-top: 8px; }

    .quick-stats {
      display: flex; gap: 16px; margin-left: auto;
    }
    .qs-item { text-align: center; }
    .qs-num  { color: #7c3aed; font-size: 24px; font-weight: 700; }
    .qs-label{ color: #6b7280; font-size: 11px; }

    .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
    .tabs button {
      padding: 10px 18px; border-radius: 8px;
      border: 1px solid #1a1a3e; background: #0f0f23;
      color: #9ca3af; cursor: pointer; font-size: 14px; transition: all 0.2s;
    }
    .tabs button.active { background: #7c3aed; color: white; border-color: #7c3aed; }
    .tabs button:hover   { border-color: #7c3aed; color: white; }

    .card {
      background: #0f0f23; border: 1px solid #1a1a3e;
      border-radius: 12px; padding: 24px;
    }

    .faq-item { padding: 14px 0; border-bottom: 1px solid #1a1a3e; }
    .faq-item:last-child { border-bottom: none; }
    .faq-q { color: white; font-weight: 600; font-size: 14px; margin-bottom: 6px; }
    .faq-a { color: #9ca3af; font-size: 13px; margin-bottom: 8px; }

    .doc-item {
      display: flex; align-items: center; gap: 12px;
      padding: 12px 0; border-bottom: 1px solid #1a1a3e;
    }
    .doc-item:last-child { border-bottom: none; }
    .doc-icon { font-size: 24px; }
    .doc-name { color: white; font-size: 14px; font-weight: 600; }
    .doc-date { color: #6b7280; font-size: 12px; }

    .chat-item { padding: 14px 0; border-bottom: 1px solid #1a1a3e; }
    .chat-item:last-child { border-bottom: none; }
    .chat-q { color: white; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
    .chat-a { color: #9ca3af; font-size: 12px; margin-bottom: 8px; }
    .chat-meta { display: flex; gap: 8px; align-items: center; }

    .badge {
      background: #1a1a3e; color: #9ca3af;
      padding: 2px 8px; border-radius: 20px; font-size: 11px;
    }
    .badge.lang { background: #1e1040; color: #7c3aed; }
    .date { color: #6b7280; font-size: 11px; }
    .loading, .empty { color: #6b7280; text-align: center; padding: 30px; }
  `]
})
export class AdminUserDetailComponent implements OnInit {
  user      : any    = null;
  loading    = true;
  tab        = 'faqs';
  tabLoading = false;
  faqs : any[] = [];
  docs : any[] = [];
  chats: any[] = [];

  constructor(
    private route:    ActivatedRoute,
    public  router:   Router,
    private adminSvc: AdminService
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.adminSvc.getUser(id).subscribe({
      next: (res: any) => { this.user = res?.data ?? res; this.loading = false; this.switchTab('faqs'); },
      error: () => { this.loading = false; }
    });
  }

  switchTab(t: string) {
    this.tab = t;
    const id = this.user?.id;
    if (!id) return;
    this.tabLoading = true;

    const call =
      t === 'faqs'  ? this.adminSvc.getUserFaqs(id) :
      t === 'docs'  ? this.adminSvc.getUserDocuments(id) :
                      this.adminSvc.getUserChats(id);

    call.subscribe({
      next: (res: any) => {
        const data = res?.data ?? res;
        if (t === 'faqs')  this.faqs  = data;
        if (t === 'docs')  this.docs  = data;
        if (t === 'chats') this.chats = data;
        this.tabLoading = false;
      },
      error: () => { this.tabLoading = false; }
    });
  }
}