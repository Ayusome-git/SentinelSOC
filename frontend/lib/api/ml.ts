import { api } from '../api';
import { MLModel, MLTrainRequest } from '../types/ml';

export const mlApi = {
  getModels: async (applicationId?: string): Promise<MLModel[]> => {
    let url = '/api/v1/ml/models';
    if (applicationId) {
      url += `?application_id=${encodeURIComponent(applicationId)}`;
    }
    return api.get(url);
  },

  getModel: async (id: string): Promise<MLModel> => {
    return api.get(`/api/v1/ml/models/${id}`);
  },

  trainModel: async (request: MLTrainRequest): Promise<{ message: string }> => {
    return api.post('/api/v1/ml/models/train', request);
  },
};
