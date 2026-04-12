import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">
      <div class="page-header">
        <h2>📄 Documents</h2>
        <label class="btn-upload">
          📤 Upload Document
          <input type="file" accept=".txt,.pdf,.docx,.xlsx,.csv" (change)="onFileSelect($event)" hidden>
        </label>
      </div>

      <div *ngIf="uploading" class="uploading">Uploading & processing...</div>

      <div class="card">
        <div *ngIf="loading" class="loading">Loading documents...</div>
        <div *ngIf="!loading && docs.length === 0" class="empty">
          No documents yet. Upload TXT, PDF, or DOCX files.
        </div>
        <div *ngFor="let doc of docs" class="doc-item">
          <div class="doc-icon">📄</div>
          <div class="doc-info">
            <div class="doc-name">{{ doc.filename }}</div>
            <div class="doc-date">{{ doc.created_at | date:'medium' }}</div>
          </div>
          <button (click)="deleteDoc(doc.id)" class="btn-del">🗑️</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page-header {
      display: flex; justify-content: space-between;
      align-items: center; margin-bottom: 24px;
    }
    h2 { color: white; font-size: 22px; }
    .btn-upload {
      padding: 10px 20px; background: #e94560; color: white;
      border-radius: 8px; cursor: pointer; font-size: 14px;
    }
    .card {
      background: #16213e; border-radius: 12px; padding: 24px;
    }
    .doc-item {
      display: flex; align-items: center; gap: 14px;
      padding: 14px 0; border-bottom: 1px solid #0f3460;
    }
    .doc-item:last-child { border-bottom: none; }
    .doc-icon { font-size: 28px; }
    .doc-info { flex: 1; }
    .doc-name { color: white; font-size: 14px; font-weight: bold; }
    .doc-date { color: #888; font-size: 12px; }
    .btn-del { background: none; border: none; cursor: pointer; font-size: 18px; }
    .loading, .empty { color: #888; text-align: center; padding: 30px; }
    .uploading {
      background: rgba(233,69,96,0.1); border: 1px solid #e94560;
      color: #e94560; padding: 12px; border-radius: 8px;
      margin-bottom: 16px; text-align: center;
    }
  `]
})
export class DocumentsComponent implements OnInit {
  docs: any[] = [];
  loading = false;
  uploading = false;

  constructor(private api: ApiService) { }

  ngOnInit() { this.loadDocs(); }

  loadDocs() {
    this.loading = true;
    this.api.getDocuments().subscribe({
      next: (res: any) => {
        this.docs = res?.data ?? res;
        this.loading = false;
      },
      error: () => { this.loading = false; }
    });
  }

  onFileSelect(event: any) {
    const file = event.target.files[0];
    if (!file) return;
    this.uploading = true;
    this.api.uploadDocument(file).subscribe({
      next: () => { this.uploading = false; this.loadDocs(); },
      error: (error: any) => {
        alert(error.error.errors[0]);
        this.uploading = false;
      }
    });
  }

  deleteDoc(id: number) {
    if (!confirm('Delete this document?')) return;
    this.api.deleteDocument(id).subscribe(() => this.loadDocs());
  }
}