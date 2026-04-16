// model.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export type ModelName = 'flan-t5-large' | 'phi-3-mini' | 'gemma-2b' | 'mistral-7b' | 'llama-3-8b';

export interface ModelInfo {
  id:          ModelName;
  label:       string;
  description: string;
  speed:       string;
  quality:     string;
  ram:         string;
  requiresGpu: boolean;
}

export const AVAILABLE_MODELS: ModelInfo[] = [
  {
    id:          'flan-t5-large',
    label:       'Flan-T5 Large',
    description: 'Fast, lightweight — works on CPU. Best for simple support FAQs.',
    speed:       '⚡ Very fast',
    quality:     '★★★☆☆',
    ram:         '~1 GB RAM',
    requiresGpu: false,
  },
  {
    id:          'gemma-2b',
    label:       'gemma-2b',
    description: 'Fast, lightweight — google/gemma-2b-it',
    speed:       '⚡ Very fast',
    quality:     '★★★☆☆',
    ram:         '~1 GB RAM',
    requiresGpu: false,
  },
  {
    id:          'phi-3-mini',
    label:       'phi-3-mini',
    description: 'Fast, lightweight — works on CPU. Best for simple support FAQs.',
    speed:       '⚡ Very fast',
    quality:     '★★★☆☆',
    ram:         '~1 GB RAM',
    requiresGpu: false,
  },
  {
    id:          'mistral-7b',
    label:       'Mistral 7B',
    description: 'Human-like responses, instruction-tuned. Requires GPU.',
    speed:       '🔥 Medium',
    quality:     '★★★★☆',
    ram:         '~4 GB (4-bit)',
    requiresGpu: true,
  },
  {
    id:          'llama-3-8b',
    label:       'Llama 3 8B',
    description: 'Best quality answers, advanced reasoning. Requires GPU.',
    speed:       '🧠 Slower',
    quality:     '★★★★★',
    ram:         '~5 GB (4-bit)',
    requiresGpu: true,
  },
];

@Injectable({ providedIn: 'root' })
export class ModelService {
  private api           = environment.apiUrl;
  private currentModel$ = new BehaviorSubject<ModelName>('flan-t5-large');

  constructor(private http: HttpClient) {}

  getModel(): Observable<{ data: { model: ModelName } }> {
    return this.http.get<any>(`${this.api}/model/`).pipe(
      tap(res => this.currentModel$.next(res?.data?.model ?? 'flan-t5-large'))
    );
  }

  setModel(model: ModelName): Observable<any> {
    return this.http.post<any>(`${this.api}/model/`, { model_name: model }).pipe(
      tap(() => this.currentModel$.next(model))
    );
  }

  get currentModel(): Observable<ModelName> {
    return this.currentModel$.asObservable();
  }
}