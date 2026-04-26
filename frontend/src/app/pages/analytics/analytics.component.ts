import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analytics.component.html',
  // styleUrls: ['./analytics.component.css']
})
export class AnalyticsComponent implements OnInit {

  chats: any[] = [];

  totalChats = 0;
  totalPages = 0;
  currentPage = 1;
  pageSize = 20;

  loading = false;

  Math = Math;

  data: any;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadAnalytics();
  }

  loadAnalytics() {
    this.loading = true;

    this.api.getAnalytics(this.currentPage, this.pageSize).subscribe({
      next: (res: any) => {

        this.data = res;

        const recent = res?.recent_chats;

        this.chats = recent?.items || [];
        this.totalChats = recent?.total || 0;
        this.totalPages = recent?.total_pages || 0;
        this.currentPage = recent?.page || 1;
        this.pageSize = recent?.page_size || 10;

        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.loading = false;
      }
    });
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadAnalytics();
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadAnalytics();
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadAnalytics();
    }
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const max = 5;

    let start = Math.max(1, this.currentPage - Math.floor(max / 2));
    let end = Math.min(this.totalPages, start + max - 1);

    if (end - start < max) {
      start = Math.max(1, end - max + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }
}