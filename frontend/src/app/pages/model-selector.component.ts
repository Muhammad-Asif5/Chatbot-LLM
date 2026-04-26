import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ModelInfo, AVAILABLE_MODELS, ModelName, ModelService } from '../services/model.service';
import { AuthService } from '../services/auth.service';

const PLAN_LIMITS: Record<string, number> = {
  free: 50,
  pro: 500,
  enterprise: 99999,
};

@Component({
  selector: 'app-model-selector',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './model-selector.component.html',
  styleUrls: ['./model-selector.component.css']
})
export class ModelSelectorComponent implements OnInit {

  models: ModelInfo[] = AVAILABLE_MODELS;
  selected: ModelName = 'flan-t5-large';
  loading = false;
  message = '';
  plan = 'free';
  planLimit = 50;
  gpuAvailable = true;

  constructor(
    private modelService: ModelService,
    private auth: AuthService,
  ) {}

  ngOnInit() {
    const user = this.auth.getCurrentUser();
    this.plan = user?.plan || 'free';
    this.planLimit = PLAN_LIMITS[this.plan] ?? 50;

    this.modelService.getModel().subscribe(res => {
      this.selected = res.data.model;
    });
  }

  select(model: ModelName) {
    const info = this.models.find(m => m.id === model);
    if (info?.requiresGpu && !this.gpuAvailable) return;
    if (this.selected === model || this.loading) return;

    this.loading = true;
    this.message = '';

    this.modelService.setModel(model).subscribe({
      next: () => {
        this.selected = model;
        this.message = `Switched to ${model}. New chats will use this model.`;
        this.loading = false;
      },
      error: (e: any) => {
        this.message = e?.error?.message || 'Failed to switch model. Try again.';
        this.loading = false;
      },
    });
  }
}