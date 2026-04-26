import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
  user: any;
  userInitial: string = 'U';

  constructor(private auth: AuthService, private router: Router) {
    this.user = this.auth.getCurrentUser();
    this.userInitial = this.user?.name?.charAt(0)?.toUpperCase() || 'U';
  }

  goToAdmin() {
    this.router.navigate(['/admin']);
  }

  logout() {
    this.auth.logout();
  }
}