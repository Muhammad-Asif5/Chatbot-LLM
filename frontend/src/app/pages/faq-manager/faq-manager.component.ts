import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-faq-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <h2>❓ FAQ Manager</h2>
        <button (click)="showForm = !showForm" class="btn-add">
          {{ showForm ? '✕ Cancel' : '+ Add FAQ' }}
        </button>
      </div>

      <!-- Add Form -->
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

      <!-- FAQ List -->
      <div class="card">
        <div *ngIf="loading" class="loading">Loading FAQs...</div>
        <div *ngIf="!loading && faqs.length === 0" class="empty">
          No FAQs yet. Add your first FAQ above!
        </div>
        <div *ngFor="let faq of faqs" class="faq-item">
          <div class="faq-content">
            <div class="faq-q">{{ faq.question }}</div>
            <div class="faq-a">{{ faq.answer }}</div>
            <span class="badge">{{ faq.category }}</span>
          </div>
          <div class="faq-actions">
            <button (click)="editFaq(faq)" class="btn-edit">✏️</button>
            <button (click)="deleteFaq(faq.id)" class="btn-del">🗑️</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page { max-width: 900px; }
    .page-header {
      display: flex; justify-content: space-between;
      align-items: center; margin-bottom: 24px;
    }
    h2 { color: white; font-size: 22px; }
    .card {
      background: #16213e; border-radius: 12px;
      padding: 24px; margin-bottom: 20px;
    }
    .form-card h3 { color: white; margin-bottom: 20px; }
    .form-group { margin-bottom: 16px; }
    label { color: #aaa; font-size: 13px; display: block; margin-bottom: 6px; }
    input, textarea {
      width: 100%; padding: 10px 14px; border-radius: 8px;
      border: 1px solid #0f3460; background: #1a1a2e;
      color: white; font-size: 14px; box-sizing: border-box;
      resize: vertical;
    }
    input:focus, textarea:focus { outline: none; border-color: #e94560; }
    .form-actions { display: flex; justify-content: flex-end; }
    .btn-primary {
      padding: 10px 24px; background: #e94560; color: white;
      border: none; border-radius: 8px; cursor: pointer; font-size: 14px;
    }
    .btn-primary:disabled { background: #888; cursor: not-allowed; }
    .btn-add {
      padding: 10px 20px; background: #e94560; color: white;
      border: none; border-radius: 8px; cursor: pointer; font-size: 14px;
    }
    .faq-item {
      display: flex; justify-content: space-between; align-items: flex-start;
      padding: 16px 0; border-bottom: 1px solid #0f3460;
    }
    .faq-item:last-child { border-bottom: none; }
    .faq-q { color: white; font-weight: bold; font-size: 14px; margin-bottom: 6px; }
    .faq-a { color: #aaa; font-size: 13px; margin-bottom: 8px; }
    .badge {
      background: #0f3460; color: #aaa; padding: 3px 10px;
      border-radius: 20px; font-size: 11px;
    }
    .faq-actions { display: flex; gap: 8px; margin-left: 16px; flex-shrink: 0; }
    .btn-edit, .btn-del {
      background: none; border: none; cursor: pointer; font-size: 16px; padding: 4px;
    }
    .loading, .empty { color: #888; text-align: center; padding: 30px; }
  `]
})
export class FaqManagerComponent implements OnInit {
  faqs     : any[] = [];
  loading  = false;
  saving   = false;
  showForm = false;
  editId   : number | null = null;
  form     = { question: '', answer: '', category: 'general' };

  constructor(private api: ApiService) {}

  ngOnInit() { this.loadFaqs(); }

  loadFaqs() {
    this.loading = true;
    this.api.getFaqs().subscribe({
      next: (data) => { this.faqs = data; this.loading = false; },
      error: ()    => { this.loading = false; }
    });
  }

  saveFaq() {
    if (!this.form.question || !this.form.answer) return;
    this.saving = true;

    const call = this.editId
      ? this.api.updateFaq(this.editId, this.form)
      : this.api.addFaq(this.form);

    call.subscribe({
      next: () => {
        this.saving   = false;
        this.showForm = false;
        this.editId   = null;
        this.form     = { question: '', answer: '', category: 'general' };
        this.loadFaqs();
      },
      error: () => { this.saving = false; }
    });
  }

  editFaq(faq: any) {
    this.editId   = faq.id;
    this.form     = { question: faq.question, answer: faq.answer, category: faq.category };
    this.showForm = true;
  }

  deleteFaq(id: number) {
    if (!confirm('Delete this FAQ?')) return;
    this.api.deleteFaq(id).subscribe(() => this.loadFaqs());
  }
}