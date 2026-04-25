import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="layout">
      <!-- Sidebar -->
      <div class="sidebar">
        <div class="brand">🛡️ Admin Panel</div>

        <div class="admin-badge">
          <div class="avatar">{{ adminInitial }}</div>
          <div>
            <div class="aname">{{ admin?.name }}</div>
            <div class="arole">Super Admin</div>
          </div>
        </div>

        <nav>
          <a routerLink="overview"  routerLinkActive="active"><span>📊</span> Overview</a>
          <a routerLink="users"     routerLinkActive="active"><span>👥</span> Users</a>
          <a routerLink="chats"     routerLinkActive="active"><span>💬</span> All Chats</a>
        </nav>

        <div class="sidebar-footer">
          <a class="back-btn" (click)="goToDashboard()">← Back to App</a>
          <button (click)="logout()" class="logout-btn">🚪 Logout</button>
        </div>
      </div>

      <!-- Content -->
      <div class="content">
        <router-outlet />
      </div>
    </div>
  `,
  styles: [`
    .layout { display: flex; min-height: 100vh; background: #0d0d1a; }

    .sidebar {
      width: 240px; background: #0f0f23; padding: 24px 16px;
      display: flex; flex-direction: column; gap: 8px;
      border-right: 1px solid #1a1a3e; position: fixed;
      height: 100vh; overflow-y: auto;
    }

    .brand {
      color: #7c3aed; font-size: 18px; font-weight: 700;
      padding: 8px 12px; margin-bottom: 16px; letter-spacing: 0.5px;
    }

    .admin-badge {
      display: flex; align-items: center; gap: 10px;
      padding: 12px; background: #1a1a3e; border-radius: 10px;
      margin-bottom: 24px; border: 1px solid #2d2d5e;
    }
    .avatar {
      width: 36px; height: 36px; background: #7c3aed;
      border-radius: 50%; display: flex; align-items: center;
      justify-content: center; color: white; font-weight: bold;
      font-size: 15px; flex-shrink: 0;
    }
    .aname  { color: white; font-size: 13px; font-weight: 600; }
    .arole  { color: #7c3aed; font-size: 11px; margin-top: 2px; }

    nav { display: flex; flex-direction: column; gap: 4px; flex: 1; }
    nav a {
      color: #9ca3af; text-decoration: none; padding: 10px 14px;
      border-radius: 8px; font-size: 14px; display: flex;
      align-items: center; gap: 10px; transition: all 0.2s; cursor: pointer;
    }
    nav a:hover  { background: #1a1a3e; color: white; }
    nav a.active { background: #7c3aed; color: white; }

    .sidebar-footer { display: flex; flex-direction: column; gap: 8px; margin-top: auto; }

    .back-btn {
      color: #6b7280; font-size: 13px; cursor: pointer; padding: 8px 14px;
      border-radius: 8px; text-decoration: none; display: block;
      transition: all 0.2s;
    }
    .back-btn:hover { background: #1a1a3e; color: white; }

    .logout-btn {
      background: none; border: 1px solid #7c3aed; color: #7c3aed;
      padding: 10px; border-radius: 8px; cursor: pointer;
      font-size: 13px; transition: all 0.2s;
    }
    .logout-btn:hover { background: #7c3aed; color: white; }

    .content { margin-left: 250px; flex: 1; padding: 10px; color: white; }
  `]
})
export class AdminDashboardComponent {
  admin       : any;
  adminInitial: string = 'A';

  constructor(private auth: AuthService, private router: Router) {
    this.admin        = this.auth.getCurrentUser();
    this.adminInitial = this.admin?.name?.charAt(0)?.toUpperCase() || 'A';
  }

  goToDashboard() { this.router.navigate(['/dashboard']); }
  logout()        { this.auth.logout(); }
}