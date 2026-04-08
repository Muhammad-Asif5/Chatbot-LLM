import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="auth-wrap">
      <div class="auth-card">
        <h2>🤖 VST Support AI</h2>
        <p class="sub">Login to your account</p>

        <div *ngIf="error" class="error">{{ error }}</div>

        <div class="form-group">
          <label>Email</label>
          <input type="email" [(ngModel)]="email" placeholder="you@example.com">
        </div>
        <div class="form-group">
          <label>Password</label>
          <input type="password" [(ngModel)]="password" placeholder="••••••••"
            (keyup.enter)="login()">
        </div>

        <button (click)="login()" [disabled]="loading" class="btn-primary">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>

        <p class="link">Don't have an account? <a routerLink="/register">Register</a></p>
      </div>
    </div>
  `,
  styles: [`
    .auth-wrap {
      min-height: 100vh; background: #1a1a2e;
      display: flex; align-items: center; justify-content: center;
    }
    .auth-card {
      background: #16213e; padding: 40px; border-radius: 16px;
      width: 100%; max-width: 400px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    h2 { color: #e94560; text-align: center; margin-bottom: 6px; }
    .sub { color: #888; text-align: center; margin-bottom: 28px; font-size: 14px; }
    .form-group { margin-bottom: 18px; }
    label { color: #aaa; font-size: 13px; display: block; margin-bottom: 6px; }
    input {
      width: 100%; padding: 10px 14px; border-radius: 8px;
      border: 1px solid #0f3460; background: #1a1a2e;
      color: white; font-size: 14px; box-sizing: border-box;
    }
    input:focus { outline: none; border-color: #e94560; }
    .btn-primary {
      width: 100%; padding: 12px; background: #e94560; color: white;
      border: none; border-radius: 8px; cursor: pointer; font-size: 15px;
      margin-top: 8px; transition: background 0.2s;
    }
    .btn-primary:hover { background: #c73652; }
    .btn-primary:disabled { background: #888; cursor: not-allowed; }
    .error {
      background: rgba(233,69,96,0.15); border: 1px solid #e94560;
      color: #e94560; padding: 10px; border-radius: 8px;
      margin-bottom: 16px; font-size: 13px;
    }
    .link { color: #888; text-align: center; margin-top: 20px; font-size: 13px; }
    a { color: #e94560; text-decoration: none; }
  `]
})
export class LoginComponent {
  email    = '';
  password = '';
  loading  = false;
  error    = '';

  constructor(private auth: AuthService, private router: Router) {}

  login() {
    if (!this.email || !this.password) {
      this.error = 'Please fill all fields';
      return;
    }
    this.loading = true;
    this.error   = '';
    this.auth.login({ email: this.email, password: this.password }).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: (e) => {
        this.error   = e.error?.errors || 'Login failed';
        this.loading = false;
      }
    });
  }
}