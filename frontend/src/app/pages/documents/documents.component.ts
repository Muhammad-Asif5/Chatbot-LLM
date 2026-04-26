import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './documents.component.html',
  // styleUrls: ['./documents.component.css']
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