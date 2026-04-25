import { Component, OnInit } from '@angular/core';
import { AdminService } from '../../../services/admin.service';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-admin-overview',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './admin-overview.component.html',
  styleUrl: './admin-overview.component.css',
})
export class AdminOverviewComponent implements OnInit {

  // =========================
  // GLOBAL
  // =========================
  stats: any = null;
  loading = false;

  // =========================
  // TOP USERS (NEW SCROLL + PAGINATION)
  // =========================
  topUsers: any[] = [];
  topUsersPage = 1;
  topUsersPageSize = 10;

  topUsersLoading = false;
  hasMoreTopUsers = true;

  // =========================
  // RECENT CHATS
  // =========================
  recentChats: any[] = [];
  recentChatsPage = 1;
  recentChatsPageSize = 10;

  recentChatsLoading = false;
  hasMoreChats = true;

  constructor(private adminSvc: AdminService) { }

  ngOnInit(): void {
    this.loadStats();
  }

  // =========================
  // LOAD INITIAL STATS
  // =========================
  loadStats(): void {
    this.loading = true;

    this.topUsers = [];
    this.recentChats = [];
    this.topUsersPage = 1;
    this.recentChatsPage = 1;
    this.hasMoreTopUsers = true;
    this.hasMoreChats = true;

    this.adminSvc.getStats(
      this.topUsersPage,
      this.topUsersPageSize,
      this.recentChatsPage,
      this.recentChatsPageSize
    )
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (res: any) => {
          const data = res?.data ?? res;

          this.stats = data;

          this.topUsers = data.top_users_preview || [];
          this.recentChats = data.recent_chats_preview || [];

          this.hasMoreChats = this.recentChats.length < data.overview.total_chats;
          this.hasMoreTopUsers = this.topUsers.length < data.overview.total_users;
        },
        error: () => {
          this.stats = null;
        }
      });
  }

  // =========================
  // TOP USERS - SCROLL
  // =========================
  onTopUsersScroll(event: any): void {
    const el = event.target;

    const atBottom =
      el.scrollTop + el.clientHeight >= el.scrollHeight - 50;

    if (atBottom) {
      this.loadMoreTopUsers();
    }
  }

  loadMoreTopUsers(): void {
    if (this.topUsersLoading || !this.hasMoreTopUsers) return;

    this.topUsersLoading = true;
    this.topUsersPage++;

    this.adminSvc.getTopUsers(this.topUsersPage, this.topUsersPageSize)
      .pipe(finalize(() => (this.topUsersLoading = false)))
      .subscribe({
        next: (res: any) => {
          const data = res?.data ?? res;
          const newUsers = data.top_users || [];
          this.topUsers = [...this.topUsers, ...newUsers];
          
          if (newUsers.length < this.topUsersPageSize) {
            this.hasMoreTopUsers = false;
          }
        },
        error: () => {
          this.topUsersPage--;
        }
      });
  }

  // pagination buttons (optional manual control)
  nextTopPage(): void {
    this.loadMoreTopUsers();
  }

  prevTopPage(): void {
    if (this.topUsersPage > 1) {
      this.topUsersPage--;
      this.topUsers = [];
      this.hasMoreTopUsers = true;
      this.loadStats();
    }
  }

  // =========================
  // RECENT CHATS
  // =========================
  onRecentChatScroll(event: any): void {

    const el = event.target;

    const atBottom =
      el.scrollTop + el.clientHeight >= el.scrollHeight - 50;

    if (atBottom) {

      this.loadMoreChats();
    }
  }

  loadMoreChats(): void {
    
    if (this.recentChatsLoading || !this.hasMoreChats) return;

    this.recentChatsLoading = true;
    this.recentChatsPage++;

    this.adminSvc.getRecentConversations(this.recentChatsPage, this.recentChatsPageSize)
      .pipe(finalize(() => (this.recentChatsLoading = false)))
      .subscribe({
        next: (res: any) => {

          const data = res?.data ?? res;
          const newChats = data.recent_chats || [];

          this.recentChats = [...this.recentChats, ...newChats];
          
          if (newChats.length < this.recentChatsPageSize) {
            this.hasMoreChats = false;
          }
        },
        error: () => {
          this.recentChatsPage--;
        }
      });
  }

  prevRecentPage(): void {
    if (this.recentChatsPage > 1) {
      this.recentChatsPage--;
      this.recentChats = [];
      this.hasMoreChats = true;
      this.loadStats();
    }
  }

  nextRecentPage(): void {
    this.loadMoreChats();
  }

  // =========================
  // TRACKING
  // =========================
  trackByUser(index: number, item: any): any {
    return item?.id ?? index;
  }

  trackByChat(index: number, item: any): any {
    return item?.id ?? index;
  }
}