import axios, { AxiosError, AxiosInstance } from 'axios';
import type {
  Project,
  Dataset,
  Marker,
  AnalysisJob,
  AnalysisType,
  ClusterResult,
  TwoPointResult,
  MDSResult,
  PhaseResult,
  QTLChartData,
  LinkageMapData,
  DendrogramNode,
  TPMMode,
  ApiError,
} from '../types';

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor for consistent error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const message =
      error.response?.data?.detail ?? error.message ?? 'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);

// ---------------------------------------------------------------------------
// Projects API
// ---------------------------------------------------------------------------

export const projectsApi = {
  list: async (): Promise<Project[]> => {
    const { data } = await api.get<Project[]>('/projects');
    return data;
  },

  get: async (id: string): Promise<Project> => {
    const { data } = await api.get<Project>(`/projects/${id}`);
    return data;
  },

  create: async (name: string, mode: TPMMode): Promise<Project> => {
    const { data } = await api.post<Project>('/projects', { name, mode });
    return data;
  },

  update: async (id: string, updates: Partial<Pick<Project, 'name' | 'mode'>>): Promise<Project> => {
    const { data } = await api.patch<Project>(`/projects/${id}`, updates);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`);
  },
};

// ---------------------------------------------------------------------------
// Datasets API
// ---------------------------------------------------------------------------

export const datasetsApi = {
  list: async (projectId: string): Promise<Dataset[]> => {
    const { data } = await api.get<Dataset[]>(`/projects/${projectId}/datasets`);
    return data;
  },

  get: async (projectId: string, datasetId: string): Promise<Dataset> => {
    const { data } = await api.get<Dataset>(`/projects/${projectId}/datasets/${datasetId}`);
    return data;
  },

  upload: async (
    projectId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<Dataset> => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await api.post<Dataset>(
      `/projects/${projectId}/datasets/upload`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (event.total && onProgress) {
            onProgress(Math.round((event.loaded / event.total) * 100));
          }
        },
      }
    );
    return data;
  },

  delete: async (projectId: string, datasetId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}/datasets/${datasetId}`);
  },

  getMarkers: async (
    projectId: string,
    datasetId: string,
    page = 1,
    pageSize = 50,
    sortBy?: string,
    sortOrder?: 'asc' | 'desc'
  ): Promise<{ markers: Marker[]; total: number }> => {
    const params: Record<string, string | number> = { page, page_size: pageSize };
    if (sortBy) params.sort_by = sortBy;
    if (sortOrder) params.sort_order = sortOrder;

    const { data } = await api.get(`/projects/${projectId}/datasets/${datasetId}/markers`, {
      params,
    });
    return data;
  },

  updateMarkerSelection: async (
    projectId: string,
    datasetId: string,
    markerNames: string[],
    checked: boolean
  ): Promise<void> => {
    await api.patch(`/projects/${projectId}/datasets/${datasetId}/markers/selection`, {
      marker_names: markerNames,
      checked,
    });
  },

  selectAll: async (projectId: string, datasetId: string): Promise<void> => {
    await api.post(`/projects/${projectId}/datasets/${datasetId}/markers/select-all`);
  },

  selectNone: async (projectId: string, datasetId: string): Promise<void> => {
    await api.post(`/projects/${projectId}/datasets/${datasetId}/markers/select-none`);
  },

  invertSelection: async (projectId: string, datasetId: string): Promise<void> => {
    await api.post(`/projects/${projectId}/datasets/${datasetId}/markers/invert-selection`);
  },

  applySelectionCriteria: async (
    projectId: string,
    datasetId: string,
    criteria: {
      chi_sig_threshold: number;
      include_ok_only: boolean;
      include_fdr: boolean;
      include_fnp: boolean;
      require_both_parents: boolean;
    }
  ): Promise<{ selected_count: number }> => {
    const { data } = await api.post(
      `/projects/${projectId}/datasets/${datasetId}/markers/apply-criteria`,
      criteria
    );
    return data;
  },
};

// ---------------------------------------------------------------------------
// Analyses API
// ---------------------------------------------------------------------------

export const analysesApi = {
  list: async (projectId: string): Promise<AnalysisJob[]> => {
    const { data } = await api.get<AnalysisJob[]>(`/projects/${projectId}/analyses`);
    return data;
  },

  get: async (projectId: string, analysisId: string): Promise<AnalysisJob> => {
    const { data } = await api.get<AnalysisJob>(
      `/projects/${projectId}/analyses/${analysisId}`
    );
    return data;
  },

  submit: async (
    projectId: string,
    analysisType: AnalysisType,
    params: Record<string, unknown>
  ): Promise<AnalysisJob> => {
    const { data } = await api.post<AnalysisJob>(`/projects/${projectId}/analyses`, {
      analysis_type: analysisType,
      params,
    });
    return data;
  },

  cancel: async (projectId: string, analysisId: string): Promise<void> => {
    await api.post(`/projects/${projectId}/analyses/${analysisId}/cancel`);
  },

  getResults: async (
    projectId: string,
    analysisId: string
  ): Promise<ClusterResult | TwoPointResult | MDSResult | PhaseResult> => {
    const { data } = await api.get(
      `/projects/${projectId}/analyses/${analysisId}/results`
    );
    return data;
  },
};

// ---------------------------------------------------------------------------
// Exports API
// ---------------------------------------------------------------------------

export const exportsApi = {
  create: async (
    projectId: string,
    format: string,
    contentType: string,
    options?: Record<string, unknown>
  ): Promise<{ export_id: string; download_url: string }> => {
    const { data } = await api.post(`/projects/${projectId}/exports`, {
      format,
      content_type: contentType,
      options,
    });
    return data;
  },

  download: (projectId: string, exportId: string): string => {
    return `/api/projects/${projectId}/exports/${exportId}/download`;
  },
};

// ---------------------------------------------------------------------------
// Visualization API
// ---------------------------------------------------------------------------

export const visualizationApi = {
  getDendrogram: async (
    projectId: string,
    analysisId: string
  ): Promise<DendrogramNode> => {
    const { data } = await api.get(
      `/projects/${projectId}/analyses/${analysisId}/visualization/dendrogram`
    );
    return data;
  },

  getLinkageMap: async (
    projectId: string,
    analysisId: string
  ): Promise<LinkageMapData> => {
    const { data } = await api.get(
      `/projects/${projectId}/analyses/${analysisId}/visualization/linkage-map`
    );
    return data;
  },

  getQTLChart: async (
    projectId: string,
    analysisId: string
  ): Promise<QTLChartData> => {
    const { data } = await api.get(
      `/projects/${projectId}/analyses/${analysisId}/visualization/qtl-chart`
    );
    return data;
  },

  getPairwiseMatrix: async (
    projectId: string,
    analysisId: string
  ): Promise<{ labels: string[]; data: number[][] }> => {
    const { data } = await api.get(
      `/projects/${projectId}/analyses/${analysisId}/visualization/pairwise-matrix`
    );
    return data;
  },

  getMDS3D: async (
    projectId: string,
    analysisId: string
  ): Promise<{ labels: string[]; coordinates: number[][]; mean_nn_fit: number }> => {
    const { data } = await api.get(
      `/projects/${projectId}/analyses/${analysisId}/visualization/mds-3d`
    );
    return data;
  },

  getPhaseTable: async (
    projectId: string,
    analysisId: string
  ): Promise<{ markers: string[]; phases: string[][] }> => {
    const { data } = await api.get(
      `/projects/${projectId}/analyses/${analysisId}/visualization/phase-table`
    );
    return data;
  },
};

export default api;
