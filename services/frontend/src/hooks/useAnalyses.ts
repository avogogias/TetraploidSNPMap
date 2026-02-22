import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { analysesApi } from '../services/api';
import type { AnalysisType } from '../types';
import toast from 'react-hot-toast';

const ANALYSES_KEY = 'analyses' as const;

/** Fetch all analysis jobs for a project */
export function useAnalyses(projectId: string | undefined) {
  return useQuery({
    queryKey: [ANALYSES_KEY, projectId],
    queryFn: () => analysesApi.list(projectId!),
    enabled: !!projectId,
  });
}

/** Fetch a single analysis job with auto-polling when it is PENDING or RUNNING */
export function useAnalysis(projectId: string | undefined, analysisId: string | undefined) {
  return useQuery({
    queryKey: [ANALYSES_KEY, projectId, analysisId],
    queryFn: () => analysesApi.get(projectId!, analysisId!),
    enabled: !!projectId && !!analysisId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'PENDING' || status === 'RUNNING') {
        return 2000; // poll every 2 seconds while active
      }
      return false;
    },
  });
}

/** Submit a new analysis job */
export function useSubmitAnalysis(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      analysisType,
      params,
    }: {
      analysisType: AnalysisType;
      params: Record<string, unknown>;
    }) => analysesApi.submit(projectId, analysisType, params),
    onSuccess: (job) => {
      queryClient.invalidateQueries({ queryKey: [ANALYSES_KEY, projectId] });
      toast.success(`Analysis "${job.analysis_type}" submitted`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to submit analysis: ${error.message}`);
    },
  });
}

/** Cancel a running analysis job */
export function useCancelAnalysis(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (analysisId: string) => analysesApi.cancel(projectId, analysisId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ANALYSES_KEY, projectId] });
      toast.success('Analysis cancelled');
    },
    onError: (error: Error) => {
      toast.error(`Failed to cancel analysis: ${error.message}`);
    },
  });
}

/** Fetch analysis results */
export function useAnalysisResults(
  projectId: string | undefined,
  analysisId: string | undefined,
  enabled = true
) {
  return useQuery({
    queryKey: [ANALYSES_KEY, projectId, analysisId, 'results'],
    queryFn: () => analysesApi.getResults(projectId!, analysisId!),
    enabled: !!projectId && !!analysisId && enabled,
  });
}
