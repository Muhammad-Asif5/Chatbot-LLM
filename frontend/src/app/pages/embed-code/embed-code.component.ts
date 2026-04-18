import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-embed-code',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">
      <h2>🔗 Embed Code</h2>
      <p class="sub">Copy and paste this code before &lt;/body&gt; tag on your website.</p>

      <div class="card">
        <h3>Your Embed Code</h3>
        <div class="code-block">
          <pre>{{ embedCode }}</pre>
          <button (click)="copy()" class="btn-copy">
            {{ copied ? '✅ Copied!' : '📋 Copy' }}
          </button>
        </div>

        <div class="info-box">
          <p>🔑 <strong>Owner ID:</strong> {{ userId }}</p>
          <p>🌐 <strong>API URL:</strong> {{ baseUrl }}</p>
        </div>
      </div>

      <div class="card preview-card">
        <h3>📋 How to use</h3>
        <ol>
          <li>Copy the embed code above</li>
          <li>Open your website's HTML file</li>
          <li>Paste it before the <code>&lt;/body&gt;</code> tag</li>
          <li>Save and refresh — chatbot will appear! 🎉</li>
        </ol>
      </div>
    </div>
  `,
  styles: [`
    h2 { color: white; font-size: 22px; margin-bottom: 8px; }
    .sub { color: #888; font-size: 14px; margin-bottom: 24px; }
    .card {
      background: #16213e; border-radius: 12px;
      padding: 24px; margin-bottom: 20px;
    }
    h3 { color: white; margin-bottom: 16px; }
    .code-block {
      background: #0f3460; border-radius: 8px; padding: 16px;
      position: relative;
    }
    pre {
      color: #e94560; font-size: 13px; white-space: pre-wrap;
      word-break: break-all; margin: 0; font-family: monospace;
    }
    .btn-copy {
      position: absolute; top: 12px; right: 12px;
      padding: 6px 14px; background: #e94560; color: white;
      border: none; border-radius: 6px; cursor: pointer; font-size: 12px;
    }
    .info-box {
      margin-top: 16px; padding: 14px; background: #0f3460;
      border-radius: 8px;
    }
    .info-box p { color: #aaa; font-size: 13px; margin: 4px 0; }
    .info-box strong { color: white; }
    ol { color: #aaa; font-size: 14px; padding-left: 20px; }
    ol li { margin-bottom: 10px; }
    code {
      background: #0f3460; color: #e94560; padding: 2px 6px; border-radius: 4px;
    }
    .preview-card ol li { line-height: 1.6; }
  `]
})
export class EmbedCodeComponent {
  userId   : string = '';
  copied   = false;
  embedCode: string = '';
  baseUrl: string = environment.production ? environment.apiUrl : environment.apiUrl;

  constructor(private auth: AuthService) {

    this.userId    = this.auth.getCurrentUser()?.id || '';
    this.embedCode = `<script\n  src="${this.baseUrl}/static/chatbot.js"\n  data-owner-id="${this.userId}"\n  data-api="${this.baseUrl}/docs">\n<\/script>`;
  }

  copy() {
    navigator.clipboard.writeText(this.embedCode);
    this.copied = true;
    setTimeout(() => this.copied = false, 2000);
  }
}