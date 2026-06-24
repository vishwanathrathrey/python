export type PredictPayload = {
  features: Record<string, number | string | null>;
};

export type PredictResponse = {
  default_probability: number;
  risk_level: 'low' | 'medium' | 'high' | string;
  selected_model: string;
  missing_feature_count: number;
};

export type MetricsPayload = {
  selected_model: string;
  model_path: string;
  train_shape: [number, number];
  test_shape: [number, number];
  train_target_distribution: Record<string, number>;
  test_target_distribution: Record<string, number>;
  metrics: Record<string, {
    roc_auc: number;
    accuracy: number;
    precision: number;
    recall: number;
    classification_report: Record<string, unknown>;
  }>;
};

const API_BASE_URL = '';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function fetchHealth() {
  return requestJson<{ status: string; model_loaded: boolean; feature_count: number }>('/health');
}

export function fetchMetrics() {
  return requestJson<MetricsPayload>('/metrics');
}

export function predictRisk(features: PredictPayload['features']) {
  return requestJson<PredictResponse>('/predict', {
    method: 'POST',
    body: JSON.stringify({ features }),
  });
}