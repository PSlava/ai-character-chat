import api from './client';

export interface Report {
  id: string;
  reason: string;
  details: string | null;
  status: string;
  created_at: string;
  reporter: { id: string; username: string; email: string } | null;
  character: { id: string; name: string; slug?: string; avatar_url: string | null } | null;
}

export async function createReport(characterId: string, reason: string, details?: string) {
  const { data } = await api.post(`/characters/${characterId}/report`, { reason, details });
  return data;
}

export async function getReports(status?: string) {
  const params = status ? { status } : {};
  const { data } = await api.get<Report[]>('/admin/reports', { params });
  return data;
}

export async function updateReport(reportId: string, status: string) {
  const { data } = await api.put(`/admin/reports/${reportId}`, { status });
  return data;
}
