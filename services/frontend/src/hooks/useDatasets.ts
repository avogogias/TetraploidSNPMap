import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { datasetsApi } from '../services/api';
import type { MarkerSelectionCriteria } from '../types';
import toast from 'react-hot-toast';

const DATASETS_KEY = 'datasets' as const;
const MARKERS_KEY = 'markers' as const;

/** Fetch all datasets for a project */
export function useDatasets(projectId: string | undefined) {
  return useQuery({
    queryKey: [DATASETS_KEY, projectId],
    queryFn: () => datasetsApi.list(projectId!),
    enabled: !!projectId,
  });
}

/** Fetch a single dataset */
export function useDataset(projectId: string | undefined, datasetId: string | undefined) {
  return useQuery({
    queryKey: [DATASETS_KEY, projectId, datasetId],
    queryFn: () => datasetsApi.get(projectId!, datasetId!),
    enabled: !!projectId && !!datasetId,
  });
}

/** Upload a dataset file */
export function useUploadDataset(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      file,
      onProgress,
    }: {
      file: File;
      onProgress?: (progress: number) => void;
    }) => datasetsApi.upload(projectId, file, onProgress),
    onSuccess: (dataset) => {
      queryClient.invalidateQueries({ queryKey: [DATASETS_KEY, projectId] });
      toast.success(`Dataset "${dataset.name}" imported (${dataset.marker_count} markers)`);
    },
    onError: (error: Error) => {
      toast.error(`Import failed: ${error.message}`);
    },
  });
}

/** Delete a dataset */
export function useDeleteDataset(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (datasetId: string) => datasetsApi.delete(projectId, datasetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [DATASETS_KEY, projectId] });
      toast.success('Dataset deleted');
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete dataset: ${error.message}`);
    },
  });
}

/** Fetch markers for a dataset with pagination and sorting */
export function useMarkers(
  projectId: string | undefined,
  datasetId: string | undefined,
  page = 1,
  pageSize = 50,
  sortBy?: string,
  sortOrder?: 'asc' | 'desc'
) {
  return useQuery({
    queryKey: [MARKERS_KEY, projectId, datasetId, page, pageSize, sortBy, sortOrder],
    queryFn: () =>
      datasetsApi.getMarkers(projectId!, datasetId!, page, pageSize, sortBy, sortOrder),
    enabled: !!projectId && !!datasetId,
    placeholderData: (previousData) => previousData,
  });
}

/** Update marker selection */
export function useUpdateMarkerSelection(projectId: string, datasetId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      markerNames,
      checked,
    }: {
      markerNames: string[];
      checked: boolean;
    }) => datasetsApi.updateMarkerSelection(projectId, datasetId, markerNames, checked),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [MARKERS_KEY, projectId, datasetId],
      });
    },
  });
}

/** Select all markers */
export function useSelectAllMarkers(projectId: string, datasetId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => datasetsApi.selectAll(projectId, datasetId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [MARKERS_KEY, projectId, datasetId],
      });
      toast.success('All markers selected');
    },
  });
}

/** Select no markers */
export function useSelectNoneMarkers(projectId: string, datasetId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => datasetsApi.selectNone(projectId, datasetId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [MARKERS_KEY, projectId, datasetId],
      });
      toast.success('All markers deselected');
    },
  });
}

/** Invert marker selection */
export function useInvertMarkerSelection(projectId: string, datasetId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => datasetsApi.invertSelection(projectId, datasetId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [MARKERS_KEY, projectId, datasetId],
      });
      toast.success('Selection inverted');
    },
  });
}

/** Apply marker selection criteria */
export function useApplySelectionCriteria(projectId: string, datasetId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (criteria: MarkerSelectionCriteria) =>
      datasetsApi.applySelectionCriteria(projectId, datasetId, criteria),
    onSuccess: (result) => {
      queryClient.invalidateQueries({
        queryKey: [MARKERS_KEY, projectId, datasetId],
      });
      toast.success(`${result.selected_count} markers selected`);
    },
    onError: (error: Error) => {
      toast.error(`Selection failed: ${error.message}`);
    },
  });
}
