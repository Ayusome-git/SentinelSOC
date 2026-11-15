'use client';

import { useState, useEffect } from 'react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/card';
import { mlApi } from '@/lib/api/ml';
import { applicationsApi } from '@/lib/api/applications';
import { MLModel } from '@/lib/types/ml';
import { Application } from '@/lib/types/application';
import { useAuth } from '@/lib/auth';

export default function MLSettingsPage() {
  const { user } = useAuth();
  const [models, setModels] = useState<MLModel[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [trainingDays, setTrainingDays] = useState(7);
  const [selectedAppId, setSelectedAppId] = useState<string>('');
  const [isTraining, setIsTraining] = useState(false);

  const fetchData = async () => {
    try {
      const [modelsData, appsData] = await Promise.all([
        mlApi.getModels(),
        applicationsApi.list()
      ]);
      setModels(modelsData);
      setApplications(appsData.items);
    } catch (error) {
      console.error('Failed to fetch ML data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTrainModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isTraining) return;
    setIsTraining(true);
    try {
      await mlApi.trainModel({
        application_id: selectedAppId || null,
        training_days: trainingDays
      });
      alert('Model training started in the background!');
      await fetchData();
    } catch (error: any) {
      alert(error.message || 'Failed to start training');
    } finally {
      setIsTraining(false);
    }
  };

  const hasManagePerm = user?.role === 'ADMIN';

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Machine Learning Configuration" 
        description="Manage ML anomaly detection models and baseline settings" 
      />

      {hasManagePerm && (
        <Card>
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4 text-white">Train New Model</h2>
            <form onSubmit={handleTrainModel} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Target Application
                  </label>
                  <select
                    className="w-full bg-slate-800 border border-slate-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={selectedAppId}
                    onChange={(e) => setSelectedAppId(e.target.value)}
                  >
                    <option value="">Global (All Applications)</option>
                    {applications.map(app => (
                      <option key={app.id} value={app.id}>{app.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Training History (Days)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="90"
                    className="w-full bg-slate-800 border border-slate-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={trainingDays}
                    onChange={(e) => setTrainingDays(parseInt(e.target.value))}
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isTraining}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50"
                >
                  {isTraining ? 'Starting...' : 'Train Model'}
                </button>
              </div>
            </form>
          </div>
        </Card>
      )}

      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4 text-white">Model Inventory</h2>
          {loading ? (
            <p className="text-gray-400">Loading models...</p>
          ) : models.length === 0 ? (
            <p className="text-gray-400">No ML models found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="py-3 px-4 font-semibold text-gray-300">Name</th>
                    <th className="py-3 px-4 font-semibold text-gray-300">Type</th>
                    <th className="py-3 px-4 font-semibold text-gray-300">Application</th>
                    <th className="py-3 px-4 font-semibold text-gray-300">Status</th>
                    <th className="py-3 px-4 font-semibold text-gray-300">Training Date</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((model) => (
                    <tr key={model.id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                      <td className="py-3 px-4 text-white font-medium">{model.name}</td>
                      <td className="py-3 px-4 text-gray-400 text-sm">{model.model_type} ({model.feature_version})</td>
                      <td className="py-3 px-4 text-gray-300">
                        {model.application_id 
                          ? applications.find(a => a.id === model.application_id)?.name || model.application_id.slice(0,8)
                          : <span className="text-gray-500 italic">Global</span>}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium
                          ${model.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-400' :
                            model.status === 'TRAINING' ? 'bg-blue-500/20 text-blue-400' :
                            model.status === 'FAILED' ? 'bg-red-500/20 text-red-400' :
                            'bg-slate-500/20 text-slate-400'}
                        `}>
                          {model.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-400 text-sm">
                        {model.trained_at ? new Date(model.trained_at).toLocaleString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
