import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AdminService } from '../../services/admin.service';

@Component({
  selector: 'app-admin-users',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
   <div class="page">
  <div class="page-header">
    <h2>👥 User Management</h2>
    <button (click)="openCreate()" class="btn-primary">+ Add User</button>
  </div>
  <!-- Search -->
  <div class="search-bar">
    <input [(ngModel)]="search" placeholder="🔍 Search by name or email..." (input)="filterUsers()">
    <div class="filter-tabs">
      <button [class.active]="filter==='all'" (click)="setFilter('all')">All</button>
      <button [class.active]="filter==='active'" (click)="setFilter('active')">Active</button>
      <button [class.active]="filter==='inactive'" (click)="setFilter('inactive')">Inactive</button>
      <button [class.active]="filter==='admin'" (click)="setFilter('admin')">Admins</button>
    </div>
  </div>
  <!-- Table -->
  <div class="content-wrapper">
    <div class="card faq-list-container">
      <div *ngIf="loading" class="loading">Loading users...</div>
      <div *ngIf="!loading && filtered.length === 0" class="empty">No users found.</div>
      <table *ngIf="!loading && filtered.length > 0">
        <thead>
          <tr>
            <th>User</th>
            <th>Plan</th>
            <th>FAQs</th>
            <th>Docs</th>
            <th>Chats</th>
            <th>Status</th>
            <th>Role</th>
            <th>Joined</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let u of filtered">
            <td>
              <div class="user-cell">
                <div class="avatar">{{ u.name.charAt(0).toUpperCase() }}</div>
                <div>
                  <div class="uname">{{ u.name }}</div>
                  <div class="uemail">{{ u.email }}</div>
                </div>
              </div>
            </td>
            <td>
              <span class="plan-badge plan-{{ u.plan }}">{{ u.plan }}</span>
            </td>
            <td class="num">{{ u.stats?.faqs ?? 0 }}</td>
            <td class="num">{{ u.stats?.documents ?? 0 }}</td>
            <td class="num">{{ u.stats?.chats ?? 0 }}</td>
            <td>
              <span class="status-dot" [class.active]="u.is_active" [title]="u.is_active ? 'Active' : 'Inactive'">
                {{ u.is_active ? '🟢 Active' : '🔴 Inactive' }}
              </span>
            </td>
            <td>
              <span *ngIf="u.is_admin" class="role-admin">👑 Admin</span>
              <span *ngIf="!u.is_admin" class="role-user">User</span>
            </td>
            <td class="date">{{ u.created_at | date:'mediumDate' }}</td>
            <td>
              <div class="action-btns">
                <button (click)="viewUser(u)" class="btn-icon" title="View details">👁️</button>
                <button (click)="openEdit(u)" class="btn-icon" title="Edit">✏️</button>
                <button (click)="toggleActive(u)" class="btn-icon" [title]="u.is_active ? 'Deactivate' : 'Activate'">
                  {{ u.is_active ? '🚫' : '✅' }}
                </button>
                <button (click)="deleteUser(u)" class="btn-icon btn-danger" title="Delete">🗑️</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ✅ PAGINATION -->
  <div class="pagination-container" *ngIf="totalItems > 0 && totalPages > 0">
        <div class="pagination-info">
          Showing {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, totalItems) }} of {{ totalItems }} FAQs
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
<!-- ── Modal ─────────────────────────────────────────── -->
<div *ngIf="showModal" class="modal-overlay" (click)="closeModal()">
  <div class="modal" (click)="$event.stopPropagation()">
    <div class="modal-header">
      <h3>{{ editId ? 'Edit User' : 'Create User' }}</h3>
      <button (click)="closeModal()" class="modal-close">✕</button>
    </div>
    <div class="form-group">
      <label>Full Name</label>
      <input [(ngModel)]="form.name" type="text" placeholder="John Doe">
    </div>
    <div class="form-group">
      <label>Email</label>
      <input [(ngModel)]="form.email" type="email" placeholder="user@example.com">
    </div>
    <div class="form-group">
      <label>{{ editId ? 'New Password (leave blank to keep current)' : 'Password' }}</label>
      <input [(ngModel)]="form.password" type="password" placeholder="••••••••">
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Plan</label>
        <select [(ngModel)]="form.plan">
          <option value="free">Free</option>
          <option value="pro">Pro</option>
          <option value="enterprise">Enterprise</option>
        </select>
      </div>
      <div class="check-group">
        <label class="checkbox-label">
          <input type="checkbox" [(ngModel)]="form.is_admin">
          <span>Admin privileges</span>
        </label>
        <label class="checkbox-label" *ngIf="editId">
          <input type="checkbox" [(ngModel)]="form.is_active">
          <span>Account active</span>
        </label>
      </div>
    </div>
    <div class="modal-actions">
      <button (click)="closeModal()" class="btn-ghost">Cancel</button>
      <button (click)="saveUser()" class="btn-primary" [disabled]="saving">
        {{ saving ? 'Saving...' : (editId ? 'Update User' : 'Create User') }}
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

    .search-bar {
      display: flex; gap: 16px; align-items: center;
      margin-bottom: 20px; flex-wrap: wrap;
    }
    .search-bar input {
      flex: 1; min-width: 220px; padding: 10px 14px; border-radius: 8px;
      border: 1px solid #1a1a3e; background: #0f0f23; color: white;
      font-size: 14px;
    }
    .search-bar input:focus { outline: none; border-color: #7c3aed; }

    .filter-tabs { display: flex; gap: 6px; }
    .filter-tabs button {
      padding: 8px 14px; border-radius: 6px; border: 1px solid #1a1a3e;
      background: #0f0f23; color: #9ca3af; cursor: pointer; font-size: 13px;
      transition: all 0.2s;
    }
    .filter-tabs button.active { background: #7c3aed; color: white; border-color: #7c3aed; }
    .filter-tabs button:hover  { border-color: #7c3aed; color: white; }

    .card {
      background: #0f0f23; border: 1px solid #1a1a3e;
      border-radius: 12px; padding: 0; overflow: hidden;
    }
    table { width: 100%; border-collapse: collapse; }
    thead tr { background: #1a1a3e; }
    th {
      padding: 14px 16px; color: #9ca3af; font-size: 12px;
      font-weight: 600; text-align: left; text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    tbody tr { border-bottom: 1px solid #1a1a3e; transition: background 0.15s; }
    tbody tr:last-child { border-bottom: none; }
    tbody tr:hover { background: #141430; }
    td { padding: 14px 16px; color: #d1d5db; font-size: 13px; vertical-align: middle; }

    .user-cell { display: flex; align-items: center; gap: 10px; }
    .avatar {
      width: 34px; height: 34px; background: #7c3aed;
      border-radius: 50%; display: flex; align-items: center;
      justify-content: center; color: white; font-weight: 700;
      font-size: 14px; flex-shrink: 0;
    }
    .uname  { color: white; font-weight: 600; font-size: 13px; }
    .uemail { color: #6b7280; font-size: 11px; }

    .num  { color: #7c3aed; font-weight: 700; text-align: center; }
    .date { color: #6b7280; font-size: 12px; white-space: nowrap; }

    .plan-badge {
      padding: 3px 10px; border-radius: 20px; font-size: 11px;
      font-weight: 600; text-transform: capitalize;
    }
    .plan-free       { background: #1a1a3e; color: #9ca3af; }
    .plan-pro        { background: #1e1040; color: #7c3aed; }
    .plan-enterprise { background: #20100a; color: #f97316; }

    .role-admin { color: #f59e0b; font-size: 12px; font-weight: 600; }
    .role-user  { color: #6b7280; font-size: 12px; }

    .action-btns { display: flex; gap: 4px; }
    .btn-icon {
      background: none; border: none; cursor: pointer;
      font-size: 15px; padding: 4px 6px; border-radius: 6px;
      transition: background 0.15s;
    }
    .btn-icon:hover       { background: #1a1a3e; }
    .btn-icon.btn-danger:hover { background: #2d0a0a; }

    .btn-primary {
      padding: 10px 20px; background: #7c3aed; color: white;
      border: none; border-radius: 8px; cursor: pointer; font-size: 14px;
      transition: background 0.2s;
    }
    .btn-primary:hover    { background: #6d28d9; }
    .btn-primary:disabled { background: #4b5563; cursor: not-allowed; }
    .btn-ghost {
      padding: 10px 20px; background: transparent; color: #9ca3af;
      border: 1px solid #374151; border-radius: 8px; cursor: pointer; font-size: 14px;
    }
    .btn-ghost:hover { border-color: #7c3aed; color: white; }

    .loading, .empty { color: #6b7280; text-align: center; padding: 40px; }

    /* ── Modal ── */
    .modal-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,0.7);
      display: flex; align-items: center; justify-content: center;
      z-index: 1000; backdrop-filter: blur(4px);
    }
    .modal {
      background: #0f0f23; border: 1px solid #2d2d5e;
      border-radius: 16px; padding: 28px; width: 100%;
      max-width: 480px; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    .modal-header {
      display: flex; justify-content: space-between;
      align-items: center; margin-bottom: 22px;
    }
    .modal-header h3 { color: white; font-size: 17px; margin: 0; }
    .modal-close {
      background: none; border: none; color: #6b7280;
      font-size: 18px; cursor: pointer; padding: 4px;
      transition: color 0.2s;
    }
    .modal-close:hover { color: white; }

    .form-group { margin-bottom: 16px; }
    .form-row   { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    label { color: #9ca3af; font-size: 12px; display: block; margin-bottom: 6px; }
    input[type="text"], input[type="email"], input[type="password"], select {
      width: 100%; padding: 10px 12px; border-radius: 8px;
      border: 1px solid #2d2d5e; background: #1a1a3e;
      color: white; font-size: 14px; box-sizing: border-box;
    }
    input:focus, select:focus { outline: none; border-color: #7c3aed; }
    select option { background: #1a1a3e; }

    .check-group { display: flex; flex-direction: column; justify-content: center; }
    .checkbox-label {
      display: flex; align-items: center; gap: 8px; cursor: pointer; 
      color: #9ca3af; font-size: 13px;
      margin-top:8px;
    }
    .checkbox-label input { width: auto; cursor: pointer;  }

    .modal-actions {
      display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px;
    }

/* ───────────────────────────────────────── */
/* FULL PAGE LAYOUT */
/* ───────────────────────────────────────── */
  :host {
      display: block;
      height: 100vh;
      width: 100%;
      overflow: hidden;
    }
 

/* ───────────────────────────────────────── */
/* SCROLLABLE CONTENT */
/* ───────────────────────────────────────── */
.content-wrapper {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* ───────────────────────────────────────── */
/* FIXED HEADER */
/* ───────────────────────────────────────── */
.page-header {
  flex-shrink: 0;
}

/* ───────────────────────────────────────── */
/* FIXED SEARCH */
/* ───────────────────────────────────────── */
.search-bar {
  flex-shrink: 0;
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
export class AdminUsersComponent implements OnInit {
  users: any[] = [];
  filtered: any[] = [];

  // ✅ Pagination State
  currentPage = 1;
  pageSize = 10;
  totalItems = 0;
  totalPages = 0;

  loading = false;
  saving = false;
  showModal = false;
  editId: string | null = null;

  search = '';
  filter = 'all';

  Math = Math; // for template

  form = {
    name: '', email: '', password: '',
    plan: 'free', is_admin: false, is_active: true
  };

  constructor(private adminSvc: AdminService, private router: Router) { }

  ngOnInit() {
    this.loadUsers();
  }

  // ✅ LOAD USERS WITH PAGINATION
  loadUsers() {
    this.loading = true;

    this.adminSvc.getUsers(this.currentPage, this.pageSize, this.search, this.filter)
      .subscribe({
        next: (res: any) => { 
          // Expected response format:
          // { items, total, page, page_size, total_pages }

          this.users = res.data.items;
          this.filtered = res.data.items;

          this.totalItems = res.data.total;
          this.currentPage = res.data.page;
          this.pageSize = res.data.page_size;
          this.totalPages = res.data.total_pages;

          this.loading = false;
        },
        error: () => { this.loading = false; }
      });
  }

  // ✅ FILTER CHANGE (SERVER SIDE)
  setFilter(f: string) {
    this.filter = f;
    this.currentPage = 1;
    this.loadUsers();
  }

  // ✅ SEARCH (SERVER SIDE)
  onSearch() {
    this.currentPage = 1;
    this.loadUsers();
  }

  // ✅ PAGINATION METHODS
  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadUsers();
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadUsers();
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadUsers();
    }
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxPagesToShow = 5;

    let start = Math.max(1, this.currentPage - 2);
    let end = Math.min(this.totalPages, start + maxPagesToShow - 1);

    if (end - start + 1 < maxPagesToShow) {
      start = Math.max(1, end - maxPagesToShow + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }

  // ✅ SEARCH INPUT CHANGE
  filterUsers() {
    this.onSearch(); // redirect to server
  }

  openCreate() {
    this.editId = null;
    this.form = { name: '', email: '', password: '', plan: 'free', is_admin: false, is_active: true };
    this.showModal = true;
  }

  openEdit(u: any) {
    this.editId = u.id;
    this.form = {
      name: u.name, email: u.email, password: '',
      plan: u.plan, is_admin: u.is_admin, is_active: u.is_active
    };
    this.showModal = true;
  }

  closeModal() { this.showModal = false; }

  saveUser() {
    if (!this.form.name || !this.form.email) return;
    if (!this.editId && !this.form.password) return;

    this.saving = true;

    const payload: any = {
      name: this.form.name,
      email: this.form.email,
      plan: this.form.plan,
      is_admin: this.form.is_admin,
    };

    if (this.editId) {
      payload.is_active = this.form.is_active;
      if (this.form.password) payload.password = this.form.password;
    } else {
      payload.password = this.form.password;
    }

    const call = this.editId
      ? this.adminSvc.updateUser(this.editId, payload)
      : this.adminSvc.createUser(payload);

    call.subscribe({
      next: () => {
        this.saving = false;
        this.closeModal();
        this.currentPage = 1;
        this.loadUsers();
      },
      error: (e: any) => {
        alert(e?.error?.message || 'Error saving user');
        this.saving = false;
      }
    });
  }

  toggleActive(u: any) {
    const action = u.is_active ? 'deactivate' : 'activate';
    if (!confirm(`${action} ${u.name}?`)) return;

    this.adminSvc.toggleActive(u.id).subscribe({
      next: () => this.loadUsers(),
      error: () => alert('Error')
    });
  }

  deleteUser(u: any) {
    if (!confirm(`Delete "${u.name}"?`)) return;

    this.adminSvc.deleteUser(u.id).subscribe({
      next: () => this.loadUsers(),
      error: () => alert('Error deleting user')
    });
  }

  viewUser(u: any) {
    this.router.navigate(['/admin/users', u.id]);
  }
}
