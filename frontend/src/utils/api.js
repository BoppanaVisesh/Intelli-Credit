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

  async getApplicationSummary(id) {
    const response = await fetch(`${API_BASE_URL}/applications/${id}/summary`);
    if (!response.ok) throw new Error('Failed to fetch application summary');
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

  async deleteDueDiligenceNote(applicationId, noteId) {
    const response = await fetch(`${API_BASE_URL}/due-diligence/${applicationId}/notes/${noteId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete note');
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

  // Document Ingestion
  async uploadDocuments(formData) {
    const response = await fetch(`${API_BASE_URL}/ingestion/upload-documents`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload documents');
    }
    return response.json();
  },

  async parseDocuments(applicationId) {
    const response = await fetch(`${API_BASE_URL}/ingestion/parse-documents/${applicationId}`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to parse documents');
    }
    return response.json();
  },

  async getDocuments(applicationId) {
    const response = await fetch(`${API_BASE_URL}/ingestion/documents/${applicationId}`);
    if (!response.ok) throw new Error('Failed to fetch documents');
    return response.json();
  },

  // Research / External Intelligence
  async triggerResearch(data) {
    const response = await fetch(`${API_BASE_URL}/research/trigger-research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to trigger research');
    }
    return response.json();
  },

  async getResearchResults(applicationId) {
    const response = await fetch(`${API_BASE_URL}/research/${applicationId}/results`);
    if (!response.ok) throw new Error('Failed to fetch research results');
    return response.json();
  },

  // Fraud Detection
  async runFraudVerification(applicationId) {
    const response = await fetch(`${API_BASE_URL}/fraud/run-verification/${applicationId}`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to run fraud verification');
    }
    return response.json();
  },

  async getFraudResults(applicationId) {
    const response = await fetch(`${API_BASE_URL}/fraud/${applicationId}/results`);
    if (!response.ok) throw new Error('Failed to fetch fraud results');
    return response.json();
  },

  // Credit Scoring
  async calculateScore(applicationId) {
    const response = await fetch(`${API_BASE_URL}/scoring/calculate-score?application_id=${applicationId}`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to calculate score');
    }
    return response.json();
  },
};

// Named exports for convenience
export const {
  analyzeCreditApplication,
  createApplication,
  getApplications,
  getApplication,
  getApplicationSummary,
  addDueDiligenceNotes,
  getDueDiligenceNotes,
  deleteDueDiligenceNote,
  generateCAM,
  downloadCAM,
  uploadDocuments,
  parseDocuments,
  getDocuments,
  triggerResearch,
  getResearchResults,
  runFraudVerification,
  getFraudResults,
  calculateScore,
} = api;
