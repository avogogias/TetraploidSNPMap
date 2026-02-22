import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '../services/api';
import type { TPMMode } from '../types';
import toast from 'react-hot-toast';

const PROJECTS_KEY = ['projects'] as const;

/** Fetch all projects */
export function useProjects() {
  return useQuery({
    queryKey: PROJECTS_KEY,
    queryFn: projectsApi.list,
  });
}

/** Fetch a single project by ID */
export function useProject(id: string | undefined) {
  return useQuery({
    queryKey: [...PROJECTS_KEY, id],
    queryFn: () => projectsApi.get(id!),
    enabled: !!id,
  });
}

/** Create a new project */
export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ name, mode }: { name: string; mode: TPMMode }) =>
      projectsApi.create(name, mode),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_KEY });
      toast.success(`Project "${project.name}" created`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to create project: ${error.message}`);
    },
  });
}

/** Update a project */
export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      updates,
    }: {
      id: string;
      updates: Partial<{ name: string; mode: TPMMode }>;
    }) => projectsApi.update(id, updates),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_KEY });
      queryClient.invalidateQueries({ queryKey: [...PROJECTS_KEY, project.id] });
      toast.success('Project updated');
    },
    onError: (error: Error) => {
      toast.error(`Failed to update project: ${error.message}`);
    },
  });
}

/** Delete a project */
export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_KEY });
      toast.success('Project deleted');
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete project: ${error.message}`);
    },
  });
}
