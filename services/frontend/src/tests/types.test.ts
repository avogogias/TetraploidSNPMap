/**
 * Type system validation tests for the TetraploidSNPMap web frontend.
 *
 * These tests verify that TypeScript types and interfaces correctly model
 * the domain concepts from the original desktop application.
 */
import { describe, it, expect } from 'vitest';
import type {
  TPMMode,
  AnalysisType,
  JobStatus,
  MarkerType,
  Project,
  Dataset,
  Marker,
  AnalysisJob,
  ClusterResult,
  TwoPointResult,
  MDSResult,
  PhaseResult,
  QTLChartData,
  LinkageMapData,
  LinkageMapGroup,
  LinkageMapMarker,
  DendrogramNode,
  MarkerSelectionCriteria,
  ExportRequest,
  PaginatedResponse,
} from '../types';

describe('TypeScript domain types', () => {
  it('TPMMode covers all three project modes', () => {
    const modes: TPMMode[] = ['SNP', 'QTL', 'NONSNP'];
    expect(modes).toHaveLength(3);
  });

  it('AnalysisType covers all 8 analysis types', () => {
    const types: AnalysisType[] = [
      'cluster', 'twopoint', 'mds', 'phase',
      'qtl', 'anova', 'permutation', 'linkage_map',
    ];
    expect(types).toHaveLength(8);
  });

  it('JobStatus covers all lifecycle states', () => {
    const statuses: JobStatus[] = ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED'];
    expect(statuses).toHaveLength(4);
  });

  it('MarkerType covers all supported marker types', () => {
    const types: MarkerType[] = ['SNP', 'AFLP', 'SSR', 'RFLP', 'UNKNOWN'];
    expect(types).toHaveLength(5);
  });
});

describe('Project interface', () => {
  it('can create a valid project object', () => {
    const project: Project = {
      id: '1',
      name: 'Test Project',
      mode: 'SNP',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      datasets: [],
    };
    expect(project.name).toBe('Test Project');
    expect(project.mode).toBe('SNP');
  });

  it('supports QTL mode', () => {
    const project: Project = {
      id: '2',
      name: 'QTL Study',
      mode: 'QTL',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      datasets: [],
    };
    expect(project.mode).toBe('QTL');
  });
});

describe('Marker interface', () => {
  it('models a SNP marker with all properties', () => {
    const marker: Marker = {
      name: 'SNP001',
      safe_name: 'mkr000001',
      type: 'SNP',
      checked: true,
      parent_dosage_1: '2',
      parent_dosage_2: '1',
      chi_sig: 0.05,
      status: 'OK',
      snp_ratio: 'Simplex x Nulliplex',
      nmiss: '3',
      snp_patterns: [{ dosage: '0', count: '40', proportion: '0.40' }],
    };
    expect(marker.type).toBe('SNP');
    expect(marker.checked).toBe(true);
    expect(marker.snp_patterns).toHaveLength(1);
  });
});

describe('Analysis result interfaces', () => {
  it('ClusterResult has groups and optional dendrogram', () => {
    const result: ClusterResult = {
      groups: [{
        name: 'LG1',
        markers: [],
        marker_count: 5,
        selected_count: 5,
      }],
      dendrogram: {
        id: 'root',
        distance: 0.8,
        children: [
          { id: '1', name: 'M1', distance: 0 },
          { id: '2', name: 'M2', distance: 0 },
        ],
      },
    };
    expect(result.groups).toHaveLength(1);
    expect(result.dendrogram?.children).toHaveLength(2);
  });

  it('TwoPointResult has ordered markers and pairwise data', () => {
    const result: TwoPointResult = {
      ordered_markers: [],
      distances: [5.0, 10.0],
      pairwise_data: [[0, 0.1], [0.1, 0]],
    };
    expect(result.distances).toHaveLength(2);
    expect(result.pairwise_data).toHaveLength(2);
  });

  it('MDSResult has coordinates and fit statistic', () => {
    const result: MDSResult = {
      ordered_markers: [],
      distances: [3.0, 7.0],
      coordinates_3d: [[1, 2, 3], [4, 5, 6]],
      mean_nn_fit: 0.95,
    };
    expect(result.mean_nn_fit).toBe(0.95);
    expect(result.coordinates_3d).toHaveLength(2);
  });

  it('QTLChartData models LOD score profiles', () => {
    const data: QTLChartData = {
      positions: [0, 5, 10, 15],
      lod_scores: [0.5, 1.2, 3.8, 2.1],
      threshold: 3.0,
      traits: ['yield', 'height'],
    };
    expect(data.lod_scores).toHaveLength(4);
    expect(data.threshold).toBe(3.0);
  });

  it('LinkageMapData models map groups with positioned markers', () => {
    const map: LinkageMapData = {
      groups: [{
        name: 'Chromosome 5',
        markers: [
          { name: 'M1', position: 0.0 },
          { name: 'M2', position: 12.5 },
          { name: 'M3', position: 28.3 },
        ],
      }],
    };
    expect(map.groups[0].markers).toHaveLength(3);
    expect(map.groups[0].markers[2].position).toBe(28.3);
  });
});

describe('MarkerSelectionCriteria', () => {
  it('models chi-square filtering criteria', () => {
    const criteria: MarkerSelectionCriteria = {
      chi_sig_threshold: 0.05,
      include_ok_only: true,
      include_fdr: false,
      include_fnp: false,
      require_both_parents: true,
    };
    expect(criteria.chi_sig_threshold).toBe(0.05);
    expect(criteria.include_ok_only).toBe(true);
  });
});

describe('ExportRequest', () => {
  it('supports all export formats', () => {
    const formats: ExportRequest['format'][] = ['csv', 'tsv', 'json', 'pdf'];
    expect(formats).toHaveLength(4);
  });

  it('supports all content types', () => {
    const types: ExportRequest['content_type'][] = ['markers', 'map', 'qtl', 'phase'];
    expect(types).toHaveLength(4);
  });
});

describe('PaginatedResponse', () => {
  it('wraps typed items with pagination metadata', () => {
    const response: PaginatedResponse<Project> = {
      items: [{
        id: '1',
        name: 'P1',
        mode: 'SNP',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        datasets: [],
      }],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    expect(response.items).toHaveLength(1);
    expect(response.total).toBe(1);
  });
});
