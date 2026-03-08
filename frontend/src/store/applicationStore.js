import { create } from 'zustand';

export const useApplicationStore = create((set, get) => ({
  applications: [],
  currentApplication: null,
  loading: false,
  error: null,

  setApplications: (applications) => set({ applications }),
  
  setCurrentApplication: (application) => set({ currentApplication: application }),
  
  setLoading: (loading) => set({ loading }),
  
  setError: (error) => set({ error }),
  
  addApplication: (application) => set((state) => ({
    applications: [application, ...state.applications],
  })),
  
  updateApplication: (id, updates) => set((state) => ({
    applications: state.applications.map((app) =>
      app.application_id === id ? { ...app, ...updates } : app
    ),
    currentApplication:
      state.currentApplication?.application_id === id
        ? { ...state.currentApplication, ...updates }
        : state.currentApplication,
  })),
}));
