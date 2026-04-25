import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AdminService {

  private base = `${environment.apiUrl}/admin`;

  constructor(private http: HttpClient) { }

  // ─────────────────────────────────────────────
  // 📊 STATS (NOW PAGINATED)
  // ─────────────────────────────────────────────
  getStats(
    topUsersPage: number = 1,
    topUsersPageSize: number = 5,
    recentChatsPage: number = 1,
    recentChatsPageSize: number = 5
  ): Observable<any> {

    let params = new HttpParams()
      .set('topUsersPage', topUsersPage)
      .set('topUsersPageSize', topUsersPageSize)
      .set('recentChatsPage', recentChatsPage)
      .set('recentChatsPageSize', recentChatsPageSize);

    return this.http.get(`${this.base}/stats`, { params });
  }

  getRecentConversations(
    recentPage: number = 1,
    recentPageSize: number = 10
  ): Observable<any> {

    let params = new HttpParams()
      .set('recent_page', recentPage)
      .set('recent_page_size', recentPageSize);

    return this.http.get(`${this.base}/recent-conversations-scroll`, { params });
  }

  getTopUsers(page: number = 1, pageSize: number = 10): Observable<any> {

    let params = new HttpParams()
      .set('page', page)
      .set('page_size', pageSize);

    return this.http.get(`${this.base}/top-users`, { params });
  }


  // ─────────────────────────────────────────────
  // 👤 USERS
  // ─────────────────────────────────────────────
  getUsers(
    page: number = 1,
    pageSize: number = 10,
    search: string = '',
    filter: string = 'all'
  ): Observable<any> {

    let params = new HttpParams()
      .set('page', page)
      .set('page_size', pageSize);

    // ✅ optional search
    if (search && search.trim()) {
      params = params.set('search', search.trim());
    }

    // ✅ optional filter
    if (filter && filter !== 'all') {
      params = params.set('filter', filter);
      // expected values: active | inactive | admin
    }

    return this.http.get(`${this.base}/users`, { params });
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

  // ─────────────────────────────────────────────
  // 📄 USER DETAIL DATA
  // ─────────────────────────────────────────────
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