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
    id: 'flan-t5-large',
    label: 'Flan-T5 Large',
    description: 'Fast, lightweight — works on CPU. Best for simple support FAQs.',
    speed: '⚡⚡ Very fast',
    quality: '★★★☆☆',
    ram: '~1 GB RAM',
    requiresGpu: false,
  },
  {
    id: 'gemma-2b',
    label: 'Gemma 2B (Lightweight & Fast)',
    description: 'Small open-weight LLM by Google, suitable for chatbots, basic Q&A, and low-resource environments.',
    speed: '⚡Fast (CPU), Very Fast (GPU)',
    quality: '★★★☆☆',
    ram: '4–8 GB (4-bit quantized recommended)',
    requiresGpu: false
  },
  {
    id: 'phi-3-mini',
    label: 'Phi-3 Mini (Fast & Smart)',
    description: 'Lightweight model by Microsoft with strong reasoning and chat quality, ideal for efficient local AI apps.',
    speed: 'Fast (CPU), Very Fast (GPU)',
    quality: '★★★★☆',
    ram: '4–8 GB (4-bit quantized recommended)',
    requiresGpu: false
  },
  {
    id: 'mistral-7b',
    label: 'Mistral 7B (High Quality Reasoning)',
    description: 'Powerful open-weight LLM with strong reasoning, coding ability, and natural conversational output.',
    speed: '🔥Moderate (CPU), Fast (GPU)',
    quality: '★★★★☆',
    ram: '8–16 GB (4-bit quantized recommended)',
    requiresGpu: true
  },
  {
    id: 'llama-3-8b',
    label: 'Llama 3 8B (Strong General Purpose Model)',
    description: 'High-quality open-weight model by Meta, excellent for reasoning, coding, and natural conversation.',
    speed: '🧠 Slower (CPU), Fast (GPU)',
    quality: '★★★★☆',
    ram: '8–16 GB (4-bit quantized recommended)',
    requiresGpu: true
  }
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
