import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-knowledge',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <h2>📝 Knowledge Base</h2>
        <button (click)="toggleForm()" class="btn-add">
          {{ showForm ? '✕ Cancel' : '+ Add Article' }}
        </button>
      </div>

      <!-- Editor -->
      <div *ngIf="showForm" class="card editor-card">
        <h3>{{ editId ? 'Edit Article' : 'New Article' }}</h3>

        <div class="form-group">
          <label>Title</label>
          <input [(ngModel)]="form.title" placeholder="e.g. Refund Policy, About Us...">
        </div>

        <div class="form-group">
          <label>Content
            <span class="hint">Markdown supported — **bold**, # Heading, - list</span>
          </label>
          <div class="editor-tabs">
            <button [class.active]="activeTab === 'write'"
              (click)="activeTab = 'write'">✏️ Write</button>
            <button [class.active]="activeTab === 'preview'"
              (click)="activeTab = 'preview'">👁️ Preview</button>
          </div>

          <textarea
            *ngIf="activeTab === 'write'"
            [(ngModel)]="form.content"
            rows="14"
            placeholder="Write your content here...

# Section Heading
Your content here...

## Sub Heading
More details...

- Point 1
- Point 2">
          </textarea>

          <div *ngIf="activeTab === 'preview'"
            class="preview-box"
            [innerHTML]="renderMarkdown(form.content)">
          </div>
        </div>

        <div class="form-actions">
          <button (click)="save()" class="btn-primary" [disabled]="saving">
            {{ saving ? 'Saving...' : (editId ? 'Update' : 'Save Article') }}
          </button>
        </div>
      </div>

      <!-- List -->
      <div class="card">
        <div *ngIf="loading" class="loading">Loading...</div>
        <div *ngIf="!loading && items.length === 0" class="empty">
          No articles yet. Add your first knowledge base article!
        </div>
        <div *ngFor="let item of items" class="kb-item">
          <div class="kb-content">
            <div class="kb-title">📄 {{ item.title }}</div>
            <div class="kb-preview">{{ item.content | slice:0:120 }}...</div>
            <div class="kb-date">{{ item.updated_at | date:'medium' }}</div>
          </div>
          <div class="kb-actions">
            <button (click)="edit(item)" class="btn-edit">✏️</button>
            <button (click)="delete(item.id)" class="btn-del">🗑️</button>
          </div>
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
    .card {
      background: #16213e; border-radius: 12px;
      padding: 24px; margin-bottom: 20px;
    }
    .editor-card h3 { color: white; margin-bottom: 20px; }
    .form-group { margin-bottom: 18px; }
    label {
      color: #aaa; font-size: 13px;
      display: flex; justify-content: space-between;
      margin-bottom: 6px;
    }
    .hint { color: #555; font-size: 11px; }
    input {
      width: 100%; padding: 10px 14px; border-radius: 8px;
      border: 1px solid #0f3460; background: #1a1a2e;
      color: white; font-size: 14px; box-sizing: border-box;
    }
    input:focus { outline: none; border-color: #e94560; }
    .editor-tabs {
      display: flex; gap: 8px; margin-bottom: 8px;
    }
    .editor-tabs button {
      padding: 6px 16px; border-radius: 6px; border: none;
      background: #1a1a2e; color: #888; cursor: pointer; font-size: 13px;
    }
    .editor-tabs button.active { background: #e94560; color: white; }
    textarea {
      width: 100%; padding: 12px; border-radius: 8px;
      border: 1px solid #0f3460; background: #1a1a2e;
      color: white; font-size: 13px; font-family: monospace;
      box-sizing: border-box; resize: vertical; line-height: 1.6;
    }
    textarea:focus { outline: none; border-color: #e94560; }
    .preview-box {
      width: 100%; min-height: 200px; padding: 16px;
      border-radius: 8px; border: 1px solid #0f3460;
      background: #1a1a2e; color: #ddd; font-size: 14px;
      line-height: 1.8; box-sizing: border-box;
    }
    .preview-box h1, .preview-box h2, .preview-box h3 { color: #e94560; margin: 12px 0 6px; }
    .preview-box strong { color: white; }
    .preview-box ul { padding-left: 20px; color: #aaa; }
    .preview-box li { margin-bottom: 4px; }
    .preview-box p  { margin-bottom: 10px; }
    .form-actions { display: flex; justify-content: flex-end; }
    .btn-add, .btn-primary {
      padding: 10px 20px; background: #e94560; color: white;
      border: none; border-radius: 8px; cursor: pointer; font-size: 14px;
    }
    .btn-primary:disabled { background: #888; cursor: not-allowed; }
    .kb-item {
      display: flex; justify-content: space-between;
      align-items: flex-start; padding: 16px 0;
      border-bottom: 1px solid #0f3460;
    }
    .kb-item:last-child { border-bottom: none; }
    .kb-title  { color: white; font-weight: bold; font-size: 15px; margin-bottom: 6px; }
    .kb-preview{ color: #888; font-size: 13px; margin-bottom: 6px; }
    .kb-date   { color: #555; font-size: 11px; }
    .kb-actions{ display: flex; gap: 8px; margin-left: 16px; flex-shrink: 0; }
    .btn-edit, .btn-del {
      background: none; border: none; cursor: pointer; font-size: 16px;
    }
    .loading, .empty { color: #888; text-align: center; padding: 30px; }
  `]
})
export class KnowledgeComponent implements OnInit {
  items     : any[] = [];
  loading   = false;
  saving    = false;
  showForm  = false;
  editId    : number | null = null;
  activeTab = 'write';
  form      = { title: '', content: '' };

  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient, private auth: AuthService) {}

  ngOnInit() { this.load(); }

  load() {
    this.loading = true;
    this.http.get<any[]>(`${this.apiUrl}/knowledge/`).subscribe({
      next: (data:any) => { this.items = data.data; this.loading = false; },
      error: ()    => { this.loading = false; }
    });
  }

  toggleForm() {
    this.showForm = !this.showForm;
    if (!this.showForm) this.resetForm();
  }

  save() {
    if (!this.form.title || !this.form.content) return;
    this.saving = true;

    const call = this.editId
      ? this.http.put(`${this.apiUrl}/knowledge/${this.editId}`, this.form)
      : this.http.post(`${this.apiUrl}/knowledge/`, this.form);

    call.subscribe({
      next: () => {
        this.saving   = false;
        this.showForm = false;
        this.resetForm();
        this.load();
      },
      error: () => { this.saving = false; }
    });
  }

  edit(item: any) {
    this.editId   = item.id;
    this.form     = { title: item.title, content: item.content };
    this.showForm = true;
    this.activeTab = 'write';
  }

  delete(id: number) {
    if (!confirm('Delete this article?')) return;
    this.http.delete(`${this.apiUrl}/knowledge/${id}`).subscribe(() => this.load());
  }

  resetForm() {
    this.editId    = null;
    this.form      = { title: '', content: '' };
    this.activeTab = 'write';
  }

  renderMarkdown(text: string): string {
    if (!text) return '';
    return text
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
      .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g,     '<em>$1</em>')
      .replace(/^- (.+)$/gm,    '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s,'<ul>$1</ul>')
      .replace(/\n\n/g,          '<br><br>')
      .replace(/\n/g,            '<br>');
  }
}