export interface MLModel {
  id: string;
  name: string;
  model_type: string;
  feature_version: string;
  application_id: string | null;
  status: 'TRAINING' | 'ACTIVE' | 'INACTIVE' | 'FAILED';
  trained_at: string | null;
  training_window_start: string | null;
  training_window_end: string | null;
  training_sample_count: number | null;
  parameters: Record<string, any> | null;
  baseline_statistics: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface MLTrainRequest {
  application_id?: string | null;
  training_days: number;
}
