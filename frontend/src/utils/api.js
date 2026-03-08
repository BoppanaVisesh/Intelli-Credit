const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = {
  // Applications
  async analyzeCreditApplication(formData) {
    const response = await fetch(`${API_BASE_URL}/applications/analyze-credit`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to analyze application');
    return response.json();
  },

  async createApplication(data) {
    const response = await fetch(`${API_BASE_URL}/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create application');
    return response.json();
  },

  async getApplications() {
    const response = await fetch(`${API_BASE_URL}/applications`);
    if (!response.ok) throw new Error('Failed to fetch applications');
    return response.json();
  },

  async getApplication(id) {
    const response = await fetch(`${API_BASE_URL}/applications/${id}`);
    if (!response.ok) throw new Error('Failed to fetch application');
    return response.json();
  },

  // Due Diligence
  async addDueDiligenceNotes(data) {
    const response = await fetch(`${API_BASE_URL}/due-diligence/add-notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to add notes');
    return response.json();
  },

  async getDueDiligenceNotes(applicationId) {
    const response = await fetch(`${API_BASE_URL}/due-diligence/${applicationId}/notes`);
    if (!response.ok) throw new Error('Failed to fetch notes');
    return response.json();
  },

  // CAM
  async generateCAM(applicationId) {
    const response = await fetch(`${API_BASE_URL}/cam/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ application_id: applicationId }),
    });
    if (!response.ok) throw new Error('Failed to generate CAM');
    return response.json();
  },

  async downloadCAM(applicationId) {
    const response = await fetch(`${API_BASE_URL}/cam/${applicationId}/download`);
    if (!response.ok) throw new Error('Failed to download CAM');
    return response.blob();
  },
};
