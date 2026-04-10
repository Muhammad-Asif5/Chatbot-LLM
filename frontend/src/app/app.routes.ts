import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '',         redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'login',    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent) },
  { path: 'register', loadComponent: () => import('./pages/register/register.component').then(m => m.RegisterComponent) },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
    children: [
      { path: '',         redirectTo: 'faqs', pathMatch: 'full' },
      { path: 'faqs',     loadComponent: () => import('./pages/faq-manager/faq-manager.component').then(m => m.FaqManagerComponent) },
      { path: 'documents',loadComponent: () => import('./pages/documents/documents.component').then(m => m.DocumentsComponent) },
      { path: 'embed',    loadComponent: () => import('./pages/embed-code/embed-code.component').then(m => m.EmbedCodeComponent) },
      { path: 'analytics',loadComponent: () => import('./pages/analytics/analytics.component').then(m => m.AnalyticsComponent) },
      { path: 'knowledge',loadComponent: () => import('./pages/knowledge/knowledge.component').then(m => m.KnowledgeComponent) }
    ]
  },
  { path: '**', redirectTo: 'login' }
];