import { Routes } from '@angular/router';
import { AuthGuard }  from './guards/auth.guard';
import { AdminGuard } from './guards/admin.guard';

export const routes: Routes = [

  // ── Public ────────────────────────────────────────
  { path: '',         redirectTo: 'login', pathMatch: 'full' },
  { path: 'login',    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent) },
  { path: 'register', loadComponent: () => import('./pages/register/register.component').then(m => m.RegisterComponent) },

  // ── User Dashboard ────────────────────────────────
  {
    path: 'dashboard',
    canActivate: [AuthGuard],
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
    children: [
      { path: '',          redirectTo: 'faqs', pathMatch: 'full' },
      { path: 'faqs',      loadComponent: () => import('./pages/faq-manager/faq-manager.component').then(m => m.FaqManagerComponent) },
      { path: 'documents', loadComponent: () => import('./pages/documents/documents.component').then(m => m.DocumentsComponent) },
      { path: 'knowledge', loadComponent: () => import('./pages/knowledge/knowledge.component').then(m => m.KnowledgeComponent) },
      { path: 'embed',     loadComponent: () => import('./pages/embed-code/embed-code.component').then(m => m.EmbedCodeComponent) },
      { path: 'analytics', loadComponent: () => import('./pages/analytics/analytics.component').then(m => m.AnalyticsComponent) },
    ]
  },

  // ── Admin Panel ───────────────────────────────────
  {
    path: 'admin',
    canActivate: [AuthGuard, AdminGuard],
    loadComponent: () => import('./pages/admin/admin-dashboard.component').then(m => m.AdminDashboardComponent),
    children: [
      { path: '',               redirectTo: 'overview', pathMatch: 'full' },
      { path: 'overview',       loadComponent: () => import('./pages/admin/admin-overview.component').then(m => m.AdminOverviewComponent) },
      { path: 'users',          loadComponent: () => import('./pages/admin/admin-users.component').then(m => m.AdminUsersComponent) },
      { path: 'users/:id',      loadComponent: () => import('./pages/admin/admin-user-detail.component').then(m => m.AdminUserDetailComponent) },
      { path: 'chats',          loadComponent: () => import('./pages/admin/admin-chats.component').then(m => m.AdminChatsComponent) },
    ]
  },

  { path: '**', redirectTo: 'login' }
];