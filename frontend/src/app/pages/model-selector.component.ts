// model-selector.component.ts
// Lets each user choose which LLM powers their chatbot.
// Also displays their current plan and its daily query limit.
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ModelInfo, AVAILABLE_MODELS, ModelName, ModelService } from '../services/model.service';
import { AuthService } from '../services/auth.service';

const PLAN_LIMITS: Record<string, number> = {
  free:       50,
  pro:        500,
  enterprise: 99999,
};

@Component({
  selector: 'app-model-selector',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="model-selector">

      <!-- Plan badge -->
      <div class="plan-bar">
        <span class="plan-label plan-{{ plan }}">{{ plan | titlecase }} Plan</span>
        <span class="plan-limit">
          {{ planLimit | number }} LLM queries / day
          <span class="plan-note">(direct FAQ hits are always free)</span>
        </span>
        <a class="upgrade-link" *ngIf="plan === 'free'" href="/dashboard/embed">
          Upgrade for more ↗
        </a>
      </div>

      <h3>AI Model</h3>
      <p class="subtitle">Choose the model powering your chatbot</p>

      <div class="model-cards">
        <div
          *ngFor="let m of models"
          class="model-card"
          [class.active]="selected === m.id"
          [class.disabled]="m.requiresGpu && !gpuAvailable"
          (click)="select(m.id)"
        >
          <div class="model-header">
            <span class="model-name">{{ m.label }}</span>
            <span class="model-badge" [class.active-badge]="selected === m.id">
              {{ selected === m.id ? '✓ Active' : 'Select' }}
            </span>
          </div>
          <p class="model-desc">{{ m.description }}</p>
          <div class="model-meta">
            <span>{{ m.speed }}</span>
            <span>{{ m.quality }}</span>
            <span>{{ m.ram }}</span>
          </div>
          <div *ngIf="m.requiresGpu && !gpuAvailable" class="gpu-warn">
            ⚠ Requires GPU
          </div>
        </div>
      </div>

      <p class="hint" *ngIf="message">{{ message }}</p>
    </div>
  `,
  styles: [`
    .model-selector { padding: 24px; }

    .plan-bar {
      display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
      background: #1a1a3e; padding: 12px 16px;
      border-radius: 10px; margin-bottom: 24px;
    }
    .plan-label {
      padding: 4px 12px; border-radius: 20px;
      font-size: 12px; font-weight: 700; text-transform: uppercase;
    }
    .plan-free       { background: #374151; color: #9ca3af; }
    .plan-pro        { background: #1e1040; color: #a78bfa; }
    .plan-enterprise { background: #1a2510; color: #86efac; }
    .plan-limit { color: #9ca3af; font-size: 13px; }
    .plan-note  { color: #6b7280; font-size: 11px; }
    .upgrade-link {
      color: #7c3aed; font-size: 12px; text-decoration: none;
      margin-left: auto; border: 1px solid #7c3aed33;
      padding: 4px 10px; border-radius: 6px;
    }
    .upgrade-link:hover { background: #7c3aed22; }

    h3 { margin: 0 0 4px; font-size: 18px; font-weight: 500; }
    .subtitle { color: #9ca3af; margin: 0 0 20px; font-size: 14px; }
    .model-cards { display: flex; flex-direction: column; gap: 12px; }
    .model-card {
      border: 1px solid #1a1a3e; border-radius: 12px;
      padding: 16px; cursor: pointer; transition: all .2s;
      background: #0f0f23;
    }
    .model-card:hover:not(.disabled) { border-color: #7c3aed; background: #1a1a3e; }
    .model-card.active { border-color: #7c3aed; background: #1e1040; }
    .model-card.disabled { opacity: .45; cursor: not-allowed; }

    .model-header {
      display: flex; justify-content: space-between;
      align-items: center; margin-bottom: 6px;
    }
    .model-name { font-weight: 600; font-size: 15px; color: white; }
    .model-badge {
      font-size: 12px; padding: 3px 10px; border-radius: 20px;
      background: #1a1a3e; color: #9ca3af;
    }
    .model-badge.active-badge { background: #7c3aed; color: white; }

    .model-desc { font-size: 13px; color: #9ca3af; margin: 0 0 10px; }
    .model-meta { display: flex; gap: 12px; font-size: 12px; color: #6b7280; }
    .gpu-warn   { color: #f97316; font-size: 11px; margin-top: 6px; }
    .hint { margin-top: 12px; font-size: 13px; color: #7c3aed; }
  `]
})
export class ModelSelectorComponent implements OnInit {
  models: ModelInfo[] = AVAILABLE_MODELS;
  selected: ModelName = 'flan-t5-large';
  loading     = false;
  message     = '';
  plan        = 'free';
  planLimit   = 50;
  gpuAvailable = true;   // set to true once backend provides GPU info

  constructor(
    private modelService: ModelService,
    private auth: AuthService,
  ) {}

  ngOnInit() {
    const user   = this.auth.getCurrentUser();
    this.plan      = user?.plan || 'free';
    this.planLimit = PLAN_LIMITS[this.plan] ?? 50;

    this.modelService.getModel().subscribe(res => {
      this.selected = res.data.model;
    });
  }

  select(model: ModelName) {
    debugger
    const info = this.models.find(m => m.id === model);
    if (info?.requiresGpu && !this.gpuAvailable) return;
    if (this.selected === model || this.loading) return;

    this.loading = true;
    this.message = '';

    this.modelService.setModel(model).subscribe({
      next: () => {
        this.selected = model;
        this.message  = `Switched to ${model}. New chats will use this model.`;
        this.loading  = false;
      },
      error: (e: any) => {
        this.message = e?.error?.message || 'Failed to switch model. Try again.';
        this.loading = false;
      },
    });
  }
}