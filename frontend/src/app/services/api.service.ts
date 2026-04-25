import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { PaginatedFAQResponse } from '../models/faq.model';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // ── FAQs ─────────────────────────────────────────────
  /**
   * Get paginated FAQs for the current user
   * @param page Page number (1-indexed)
   * @param pageSize Items per page
   */
  getFaqs(page: number = 1, pageSize: number = 10): Observable<PaginatedFAQResponse> {
    return this.http.get<PaginatedFAQResponse>(
      `${this.apiUrl}/faqs/`,
      {
        params: {
          page: page.toString(),
          page_size: pageSize.toString()
        }
      }
    );
  }

  addFaq(data: { question: string; answer: string; category: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/faqs/`, data);
  }

  updateFaq(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/faqs/${id}`, data);
  }

  deleteFaq(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/faqs/${id}`);
  }

  deleteAllFaqs(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/faqs/all/`);
  }

  // ─────────────────────────────────────────────
  // Documents
  // ─────────────────────────────────────────────

  getDocuments(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/documents/`);
  }

  uploadDocument(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/documents/`, formData);
  }

  deleteDocument(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/documents/${id}`);
  }

  // ─────────────────────────────────────────────
  // Analytics (🔥 FIXED WITH PAGINATION)
  // ─────────────────────────────────────────────

  getAnalytics(page: number = 1, pageSize: number = 10): Observable<any> {
    return this.http.get(`${this.apiUrl}/analytics/`, {
      params: {
        page: page.toString(),
        page_size: pageSize.toString()
      }
    });
  }
}