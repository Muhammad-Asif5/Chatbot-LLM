import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-embed-code',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './embed-code.component.html',
  styleUrls: ['./embed-code.component.css']
})
export class EmbedCodeComponent {
  userId: string = '';
  copied = false;
  embedCode: string = '';
  baseUrl: string = environment.production ? environment.apiUrl : environment.apiUrl;

  constructor(private auth: AuthService) {

    this.userId = this.auth.getCurrentUser()?.id || '';
    this.embedCode = `<script\n  src="${this.baseUrl}/static/chatbot.js"\n  data-owner-id="${this.userId}"\n  data-api="${this.baseUrl}/docs">\n<\/script>`;
  }

  copy() {
    navigator.clipboard.writeText(this.embedCode);
    this.copied = true;
    setTimeout(() => this.copied = false, 2000);
  }
}