import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // ── FAQs ─────────────────────────────────────────────
  getFaqs(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/api/faqs/`);
  }

  addFaq(data: { question: string; answer: string; category: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/faqs/`, data);
  }

  updateFaq(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/api/faqs/${id}`, data);
  }

  deleteFaq(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/api/faqs/${id}`);
  }

  // ── Documents ─────────────────────────────────────────
  getDocuments(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/api/documents/`);
  }

  uploadDocument(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/api/documents/`, formData);
  }

  deleteDocument(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/api/documents/${id}`);
  }

  // ── Analytics ─────────────────────────────────────────
  getAnalytics(): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/analytics/`);
  }
}