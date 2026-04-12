import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private base = `${environment.apiUrl}/api/admin`;

  constructor(private http: HttpClient) {}

  // ── Stats ───────────────────────────────────────────────
  getStats(): Observable<any> {
    return this.http.get(`${this.base}/stats`);
  }

  // ── Users ───────────────────────────────────────────────
  getUsers(): Observable<any> {
    return this.http.get(`${this.base}/users`);
  }

  getUser(id: string): Observable<any> {
    return this.http.get(`${this.base}/users/${id}`);
  }

  createUser(payload: any): Observable<any> {
    return this.http.post(`${this.base}/users`, payload);
  }

  updateUser(id: string, payload: any): Observable<any> {
    return this.http.put(`${this.base}/users/${id}`, payload);
  }

  toggleActive(id: string): Observable<any> {
    return this.http.patch(`${this.base}/users/${id}/toggle-active`, {});
  }

  deleteUser(id: string): Observable<any> {
    return this.http.delete(`${this.base}/users/${id}`);
  }

  // ── User detail ─────────────────────────────────────────
  getUserFaqs(id: string): Observable<any> {
    return this.http.get(`${this.base}/users/${id}/faqs`);
  }

  getUserDocuments(id: string): Observable<any> {
    return this.http.get(`${this.base}/users/${id}/documents`);
  }

  getUserChats(id: string): Observable<any> {
    return this.http.get(`${this.base}/users/${id}/chats`);
  }
}