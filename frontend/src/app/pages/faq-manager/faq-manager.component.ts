import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { FAQ, PaginatedFAQResponse } from '../../models/faq.model';

@Component({
  selector: 'app-faq-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="page">
      <!-- Header: Fixed at Top -->
      <div class="page-header">
        <h2>❓ FAQ Manager</h2>
        <div class="header-actions">
          <button
            *ngIf="totalItems > 0"
            (click)="deleteAllFaqs()"
            class="btn-delete-all"
            [disabled]="deletingAll">
            {{ deletingAll ? '🗑️ Deleting...' : '🗑️ Delete All' }}
          </button>
          <button (click)="showForm = !showForm" class="btn-add">
            {{ showForm ? '✕ Cancel' : '+ Add FAQ' }}
          </button>
        </div>
      </div>

      <!-- Form: Fixed (appears/hides above scrollable area) -->
      <div *ngIf="showForm" class="card form-card">
        <h3>{{ editId ? 'Edit FAQ' : 'Add New FAQ' }}</h3>
        <div class="form-group">
          <label>Question</label>
          <input [(ngModel)]="form.question" placeholder="Enter question...">
        </div>
        <div class="form-group">
          <label>Answer</label>
          <textarea [(ngModel)]="form.answer" rows="4" placeholder="Enter answer..."></textarea>
        </div>
        <div class="form-group">
          <label>Category</label>
          <input [(ngModel)]="form.category" placeholder="general">
        </div>
        <div class="form-actions">
          <button (click)="saveFaq()" class="btn-primary" [disabled]="saving">
            {{ saving ? 'Saving...' : (editId ? 'Update' : 'Add FAQ') }}
          </button>
        </div>
      </div>

      <!-- Content Wrapper: Scrollable FAQ Section -->
      <div class="content-wrapper">
        <div class="card faq-list-container">
          <div *ngIf="loading" class="loading">Loading FAQs...</div>
          
          <div *ngIf="!loading && totalItems === 0" class="empty">
            No FAQs yet. Add your first FAQ above!
          </div>

          <!-- FAQ Items: Scrollable -->
          <div *ngIf="!loading && faqs.length > 0" class="faq-items-wrapper">
            <div *ngFor="let faq of faqs" class="faq-item">
              <div class="faq-content">
                <div class="faq-q">{{ faq.question }}</div>
                <div class="faq-a">{{ faq.answer }}</div>
                <span class="badge">{{ faq.category }}</span>
              </div>
              <div class="faq-actions">
                <button (click)="editFaq(faq)" class="btn-edit" title="Edit FAQ">✏️</button>
                <button (click)="deleteFaq(faq.id)" class="btn-del" title="Delete FAQ">🗑️</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination Controls: Fixed at Bottom -->
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
  `,
  styles: [`
    /* ─────────────────────────────────────────────────────── */
    /* COMPONENT HOST: Ensure full height */
    /* ─────────────────────────────────────────────────────── */
    :host {
      display: block;
      max-height: 80vh;
      width: 100%;
      overflow: hidden;
    }

    /* ─────────────────────────────────────────────────────── */
    /* LAYOUT: Page Container */
    /* ─────────────────────────────────────────────────────── */
    .page {
      display: flex;
      flex-direction: column;
      height: 100%;
      width: 100%;
      overflow: hidden;
      background: #0f1419;
    }

    /* ─────────────────────────────────────────────────────── */
    /* HEADER: Fixed at Top */
    /* ─────────────────────────────────────────────────────── */
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 24px;
      background: #16213e;
      border-bottom: 1px solid #0f3460;
      flex-shrink: 0;
      gap: 20px;
      min-height: fit-content;
    }
    h2 {
      color: white;
      font-size: 22px;
      margin: 0;
      white-space: nowrap;
    }
    .header-actions {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }

    /* ─────────────────────────────────────────────────────── */
    /* FORM: Fixed Below Header */
    /* ─────────────────────────────────────────────────────── */
    .form-card {
      background: #16213e;
      border-radius: 0;
      padding: 24px;
      margin: 0;
      flex-shrink: 0;
      border-bottom: 1px solid #0f3460;
      overflow: visible;
      display: flex;
      flex-direction: column;
      min-height: fit-content;
    }

    .form-card h3 {
      color: white;
      margin: 0 0 20px 0;
    }

    /* ─────────────────────────────────────────────────────── */
    /* CONTENT WRAPPER: Scrollable Middle Section */
    /* ─────────────────────────────────────────────────────── */
    .content-wrapper {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      scroll-behavior: smooth;
      display: flex;
      flex-direction: column;
    }

    /* ─────────────────────────────────────────────────────── */
    /* CARD: FAQ List Container */
    /* ─────────────────────────────────────────────────────── */
    .card {
      background: #16213e;
      border-radius: 12px;
      padding: 24px;
      margin: 0;
      display: flex;
      flex-direction: column;
      min-height: fit-content;
    }

    .faq-list-container {
      flex: 1;
      overflow: visible;
      display: flex;
      flex-direction: column;
    }

    .faq-items-wrapper {
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    /* ─────────────────────────────────────────────────────── */
    /* FORM STYLES */
    /* ─────────────────────────────────────────────────────── */
    .form-group {
      margin-bottom: 16px;
    }
    label {
      color: #aaa;
      font-size: 13px;
      display: block;
      margin-bottom: 6px;
      font-weight: 500;
    }
    input, textarea {
      width: 100%;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid #0f3460;
      background: #1a1a2e;
      color: white;
      font-size: 14px;
      box-sizing: border-box;
      resize: vertical;
      transition: border-color 0.2s;
      margin: 0;
    }
    input:focus, textarea:focus {
      outline: none;
      border-color: #e94560;
      box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.1);
    }
    .form-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 20px;
    }

    /* ─────────────────────────────────────────────────────── */
    /* BUTTONS */
    /* ─────────────────────────────────────────────────────── */
    .btn-primary {
      padding: 10px 24px;
      background: #e94560;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      transition: background 0.2s;
      margin: 0;
    }
    .btn-primary:hover:not(:disabled) {
      background: #d43a50;
    }
    .btn-primary:disabled {
      background: #888;
      cursor: not-allowed;
      opacity: 0.6;
    }

    .btn-add {
      padding: 10px 20px;
      background: #e94560;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      transition: background 0.2s;
      white-space: nowrap;
      margin: 0;
    }
    .btn-add:hover {
      background: #d43a50;
    }

    .btn-delete-all {
      padding: 10px 20px;
      background: transparent;
      color: #e94560;
      border: 1px solid #e94560;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      transition: all 0.2s;
      white-space: nowrap;
      margin: 0;
    }
    .btn-delete-all:hover {
      background: rgba(233, 69, 96, 0.15);
    }
    .btn-delete-all:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* ─────────────────────────────────────────────────────── */
    /* FAQ ITEMS */
    /* ─────────────────────────────────────────────────────── */
    .faq-item {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 16px 0;
      border-bottom: 1px solid #0f3460;
      gap: 16px;
      flex-shrink: 0;
      margin: 0;
    }
    .faq-item:last-child {
      border-bottom: none;
    }

    .faq-content {
      flex-grow: 1;
      min-width: 0;
      margin: 0;
    }
    .faq-q {
      color: white;
      font-weight: 600;
      font-size: 14px;
      margin: 0 0 6px 0;
      word-break: break-word;
    }
    .faq-a {
      color: #aaa;
      font-size: 13px;
      margin: 0 0 8px 0;
      line-height: 1.4;
      word-break: break-word;
    }
    .badge {
      display: inline-block;
      background: #0f3460;
      color: #aaa;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 500;
      margin: 0;
    }

    .faq-actions {
      display: flex;
      gap: 8px;
      flex-shrink: 0;
      margin: 0;
    }
    .btn-edit, .btn-del {
      background: none;
      border: none;
      cursor: pointer;
      font-size: 16px;
      padding: 6px 8px;
      border-radius: 4px;
      transition: background 0.2s;
      margin: 0;
    }
    .btn-edit:hover, .btn-del:hover {
      background: rgba(233, 69, 96, 0.15);
    }

    /* ─────────────────────────────────────────────────────── */
    /* EMPTY / LOADING STATES */
    /* ─────────────────────────────────────────────────────── */
    .loading, .empty {
      color: #888;
      text-align: center;
      padding: 60px 30px;
      flex-grow: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      margin: 0;
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

    /* Firefox Scrollbar */
    .content-wrapper {
      scrollbar-color: #0f3460 #0f1419;
      scrollbar-width: thin;
    }

    /* ─────────────────────────────────────────────────────── */
    /* RESPONSIVE DESIGN */
    /* ─────────────────────────────────────────────────────── */
    @media (max-width: 768px) {
      .page-header {
        flex-direction: column;
        gap: 16px;
        align-items: flex-start;
        padding: 16px;
      }
      h2 {
        font-size: 18px;
      }
      .header-actions {
        width: 100%;
      }
      .card, .form-card {
        padding: 16px;
        border-radius: 8px;
      }
      .faq-item {
        flex-direction: column;
      }
      .faq-actions {
        width: 100%;
        justify-content: flex-end;
      }
      .pagination-container {
        padding: 12px 16px;
      }
    }

    @media (max-width: 480px) {
      :host {
        height: 100vh;
      }
      .page {
        height: 100%;
      }
      .page-header {
        padding: 12px;
      }
      h2 {
        font-size: 16px;
      }
      .card, .form-card {
        padding: 12px;
      }
      .btn-add, .btn-delete-all, .btn-pagination {
        padding: 8px 12px;
        font-size: 12px;
      }
      .btn-page {
        width: 32px;
        height: 32px;
        font-size: 12px;
      }
      .pagination-container {
        padding: 10px 12px;
      }
      .pagination-info {
        font-size: 12px;
      }
    }

    /* ─────────────────────────────────────────────────────── */
    /* MOBILE VIEWPORT FIX: Prevent vh issues on mobile */
    /* ─────────────────────────────────────────────────────── */
    @supports (height: 100dvh) {
      :host {
        height: 100dvh;
      }
    }
  `]
})
export class FaqManagerComponent implements OnInit {
  // FAQ Data
  faqs: FAQ[] = [];
  totalItems = 0;
  
  // Pagination State
  currentPage = 1;
  pageSize = 20;
  totalPages = 0;
  
  // UI State
  loading = false;
  saving = false;
  deletingAll = false;
  showForm = false;
  editId: number | null = null;
  
  // Form State
  form = { question: '', answer: '', category: 'general' };

  // Math reference for template
  Math = Math;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadFaqs();
  }

  /**
   * Load FAQs from the API with pagination
   */
  loadFaqs() {
    this.loading = true;
    this.api.getFaqs(this.currentPage, this.pageSize).subscribe({
      next: (res: PaginatedFAQResponse) => {
        this.faqs = res.items;
        this.totalItems = res.total;
        this.currentPage = res.page;
        this.pageSize = res.page_size;
        this.totalPages = res.total_pages;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading FAQs:', err);
        this.loading = false;
      }
    });
  }

  /**
   * Save a new FAQ or update an existing one
   */
  saveFaq() {
    if (!this.form.question || !this.form.answer) return;
    this.saving = true;

    const call = this.editId
      ? this.api.updateFaq(this.editId, this.form)
      : this.api.addFaq(this.form);

    call.subscribe({
      next: () => {
        this.saving = false;
        this.showForm = false;
        this.editId = null;
        this.form = { question: '', answer: '', category: 'general' };
        // Reset to first page after adding/updating
        this.currentPage = 1;
        this.loadFaqs();
      },
      error: (err) => {
        console.error('Error saving FAQ:', err);
        this.saving = false;
      }
    });
  }

  /**
   * Edit an existing FAQ
   */
  editFaq(faq: FAQ) {
    this.editId = faq.id;
    this.form = {
      question: faq.question,
      answer: faq.answer,
      category: faq.category
    };
    this.showForm = true;
  }

  /**
   * Delete a single FAQ
   */
  deleteFaq(id: number) {
    if (!confirm('Delete this FAQ?')) return;
    this.api.deleteFaq(id).subscribe({
      next: () => this.loadFaqs(),
      error: (err) => console.error('Error deleting FAQ:', err)
    });
  }

  /**
   * Delete all FAQs for the current user
   */
  deleteAllFaqs() {
    if (!confirm(`Delete ALL ${this.totalItems} FAQs? This cannot be undone.`)) return;
    this.deletingAll = true;
    this.api.deleteAllFaqs().subscribe({
      next: () => {
        this.deletingAll = false;
        this.currentPage = 1;
        this.loadFaqs();
      },
      error: (err) => {
        console.error('Error deleting all FAQs:', err);
        this.deletingAll = false;
      }
    });
  }

  /**
   * Navigate to the next page
   */
  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadFaqs();
    }
  }

  /**
   * Navigate to the previous page
   */
  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadFaqs();
    }
  }

  /**
   * Go to a specific page
   */
  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadFaqs();
    }
  }

  /**
   * Generate array of page numbers to display
   * Shows max 5 page numbers (current, ±2 pages)
   */
  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxPagesToShow = 5;
    let startPage = Math.max(1, this.currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(this.totalPages, startPage + maxPagesToShow - 1);

    // Adjust start if we're near the end
    if (endPage - startPage + 1 < maxPagesToShow) {
      startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    return pages;
  }
}
