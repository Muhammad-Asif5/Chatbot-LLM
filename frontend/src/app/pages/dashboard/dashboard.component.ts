import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="layout">
      <!-- Sidebar -->
      <div class="sidebar">
        <div class="brand">🤖 VST AI</div>
        <div class="user-info">
          <div class="avatar">{{ userInitial }}</div>
          <div>
            <div class="uname">{{ user?.name }}</div>
            <div class="uplan plan-{{ user?.plan }}">{{ user?.plan | titlecase }}</div>
          </div>
        </div>

        <nav>
          <a routerLink="faqs"      routerLinkActive="active"><span>❓</span> FAQs</a>
          <a routerLink="documents" routerLinkActive="active"><span>📄</span> Documents</a>
          <a routerLink="knowledge" routerLinkActive="active"><span>📝</span> Knowledge Base</a>
          <a routerLink="model"     routerLinkActive="active"><span>🤖</span> AI Model</a>
          <a routerLink="embed"     routerLinkActive="active"><span>🔗</span> Embed Code</a>
          <a routerLink="analytics" routerLinkActive="active"><span>📊</span> Analytics</a>
        </nav>

        <!-- Admin shortcut — only for admins -->
        <a *ngIf="user?.is_admin"
           (click)="goToAdmin()"
           class="admin-link">
          🛡️ Admin Panel
        </a>

        <button (click)="logout()" class="logout-btn">🚪 Logout</button>
      </div>

      <!-- Content -->
      <div class="content">
        <router-outlet />
      </div>
    </div>
  `,
  styles: [`
    .layout { display: flex; min-height: 100vh; background: #1a1a2e; }
    .sidebar {
      width: 250px; background: #16213e; padding: 24px 16px;
      display: flex; flex-direction: column; gap: 8px;
      border-right: 1px solid #0f3460; position: fixed;
      height: 100vh; overflow-y: auto;
    }
    .brand { color: #e94560; font-size: 20px; font-weight: bold; padding: 8px 12px; margin-bottom: 16px; }
    .user-info {
      display: flex; align-items: center; gap: 10px;
      padding: 12px; background: #1a1a2e; border-radius: 10px; margin-bottom: 20px;
    }
    .avatar {
      width: 38px; height: 38px; background: #e94560;
      border-radius: 50%; display: flex; align-items: center;
      justify-content: center; color: white; font-weight: bold; font-size: 16px;
    }
    .uname  { color: white; font-size: 13px; font-weight: bold; }
    .uplan  {
      font-size: 10px; padding: 2px 8px; border-radius: 20px;
      display: inline-block; margin-top: 3px; text-transform: uppercase; font-weight: 700;
    }
    .plan-free       { background: #374151; color: #9ca3af; }
    .plan-pro        { background: #1e1040; color: #a78bfa; }
    .plan-enterprise { background: #1a2510; color: #86efac; }

    nav { display: flex; flex-direction: column; gap: 4px; flex: 1; }
    nav a {
      color: #aaa; text-decoration: none; padding: 10px 14px;
      border-radius: 8px; font-size: 14px; display: flex;
      align-items: center; gap: 10px; transition: all 0.2s;
    }
    nav a:hover  { background: #1a1a2e; color: white; }
    nav a.active { background: #e94560; color: white; }

    .admin-link {
      display: flex; align-items: center; gap: 8px;
      padding: 10px 14px; border-radius: 8px; font-size: 14px;
      color: #7c3aed; border: 1px solid #7c3aed33;
      cursor: pointer; transition: all 0.2s; margin-top: 4px;
      text-decoration: none;
    }
    .admin-link:hover { background: #7c3aed22; color: #a78bfa; }
    .logout-btn {
      background: none; border: 1px solid #e94560; color: #e94560;
      padding: 10px; border-radius: 8px; cursor: pointer;
      font-size: 13px; margin-top: auto; transition: all 0.2s;
    }
    .logout-btn:hover { background: #e94560; color: white; }
    .content { margin-left: 250px; flex: 1; padding: 30px; color: white; }
  `]
})
export class DashboardComponent {
  user        : any;
  userInitial : string = 'U';

  constructor(private auth: AuthService, private router: Router) {
    this.user        = this.auth.getCurrentUser();
    this.userInitial = this.user?.name?.charAt(0)?.toUpperCase() || 'U';
  }

  goToAdmin() { this.router.navigate(['/admin']); }
  logout()    { this.auth.logout(); }
}