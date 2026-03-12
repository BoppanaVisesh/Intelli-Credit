const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/** Extract the best human-readable error message from a failed response. */
async function extractError(response, fallback) {
  try {
    const body = await response.json();
    return new Error(body.detail || body.message || fallback);
  } catch {
    return new Error(fallback);
  }
}

export const api = {
  // Applications
  async analyzeCreditApplication(formData) {
    const response = await fetch(`${API_BASE_URL}/applications/analyze-credit`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw await extractError(response, 'Failed to analyze application');
    return response.json();
  },

  async createApplication(data) {
    const response = await fetch(`${API_BASE_URL}/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw await extractError(response, 'Failed to create application');
    return response.json();
  },

  async getApplications() {
    const response = await fetch(`${API_BASE_URL}/applications`);
    if (!response.ok) throw await extractError(response, 'Failed to fetch applications');
    return response.json();
  },

  async getApplication(id) {
    const response = await fetch(`${API_BASE_URL}/applications/${id}`);
    if (!response.ok) throw await extractError(response, 'Failed to fetch application');
    return response.json();
  },

  async getApplicationSummary(id) {
    const response = await fetch(`${API_BASE_URL}/applications/${id}/summary`);
    if (!response.ok) throw await extractError(response, 'Failed to fetch application summary');
    return response.json();
  },

  // Due Diligence
  async addDueDiligenceNotes(data) {
    const response = await fetch(`${API_BASE_URL}/due-diligence/add-notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw await extractError(response, 'Failed to add notes');
    return response.json();
  },

  async getDueDiligenceNotes(applicationId) {
    const response = await fetch(`${API_BASE_URL}/due-diligence/${applicationId}/notes`);
    if (!response.ok) throw await extractError(response, 'Failed to fetch notes');
    return response.json();
  },

  async deleteDueDiligenceNote(applicationId, noteId) {
    const response = await fetch(`${API_BASE_URL}/due-diligence/${applicationId}/notes/${noteId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw await extractError(response, 'Failed to delete note');
    return response.json();
  },

  // CAM
  async generateCAM(applicationId) {
    const response = await fetch(`${API_BASE_URL}/cam/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ application_id: applicationId }),
    });
    if (!response.ok) throw await extractError(response, 'Failed to generate CAM');
    return response.json();
  },

  async downloadCAM(applicationId) {
    const response = await fetch(`${API_BASE_URL}/cam/${applicationId}/download`);
    if (!response.ok) throw await extractError(response, 'Failed to download CAM');
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
    if (!response.ok) throw await extractError(response, 'Failed to fetch research results');
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
    if (!response.ok) throw await extractError(response, 'Failed to fetch fraud results');
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

  // Extraction & Schema Mapping
  async getExtractionDocuments(applicationId) {
    const response = await fetch(`${API_BASE_URL}/extraction/documents/${applicationId}`);
    if (!response.ok) throw await extractError(response, 'Failed to fetch extraction documents');
    return response.json();
  },

  async reviewClassification(documentId, data) {
    const response = await fetch(`${API_BASE_URL}/extraction/documents/${documentId}/review`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw await extractError(response, 'Failed to review classification');
    return response.json();
  },

  async getDefaultSchemas() {
    const response = await fetch(`${API_BASE_URL}/extraction/schemas/defaults`);
    if (!response.ok) throw await extractError(response, 'Failed to fetch default schemas');
    return response.json();
  },

  async getExtractionSchemas(applicationId) {
    const response = await fetch(`${API_BASE_URL}/extraction/schemas/${applicationId}`);
    if (!response.ok) throw await extractError(response, 'Failed to fetch schemas');
    return response.json();
  },

  async createExtractionSchema(applicationId, data) {
    const response = await fetch(`${API_BASE_URL}/extraction/schemas/${applicationId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw await extractError(response, 'Failed to create schema');
    return response.json();
  },

  async updateExtractionSchema(schemaId, data) {
    const response = await fetch(`${API_BASE_URL}/extraction/schemas/${schemaId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw await extractError(response, 'Failed to update schema');
    return response.json();
  },

  async deleteExtractionSchema(schemaId) {
    const response = await fetch(`${API_BASE_URL}/extraction/schemas/${schemaId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw await extractError(response, 'Failed to delete schema');
    return response.json();
  },

  async extractDocument(documentId, data) {
    const response = await fetch(`${API_BASE_URL}/extraction/extract/${documentId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw await extractError(response, 'Failed to extract document');
    return response.json();
  },

  async updateExtractedFields(documentId, data) {
    const response = await fetch(`${API_BASE_URL}/extraction/extract/${documentId}/fields`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw await extractError(response, 'Failed to update extracted fields');
    return response.json();
  },

  // Analysis
  async runAnalysis(applicationId) {
    const response = await fetch(`${API_BASE_URL}/analysis/run/${applicationId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ use_llm: true }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to run analysis');
    }
    return response.json();
  },

  async getAnalysis(applicationId) {
    const response = await fetch(`${API_BASE_URL}/analysis/${applicationId}`);
    if (!response.ok) throw await extractError(response, 'Failed to fetch analysis');
    return response.json();
  },

  async generateInvestmentReport(applicationId) {
    const response = await fetch(`${API_BASE_URL}/analysis/${applicationId}/report`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate report');
    }
    return response.json();
  },

  async downloadInvestmentReport(applicationId) {
    const response = await fetch(`${API_BASE_URL}/analysis/${applicationId}/report/download`);
    if (!response.ok) throw await extractError(response, 'Failed to download report');
    return response.blob();
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
  getExtractionDocuments,
  reviewClassification,
  getDefaultSchemas,
  getExtractionSchemas,
  createExtractionSchema,
  updateExtractionSchema,
  deleteExtractionSchema,
  extractDocument,
  updateExtractedFields,
} = api;
