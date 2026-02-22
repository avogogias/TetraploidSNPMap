/** Operating mode for TetraploidSNPMap */
export type TPMMode = 'SNP' | 'QTL' | 'NONSNP';

/** Types of analyses that can be run */
export type AnalysisType =
  | 'cluster'
  | 'twopoint'
  | 'mds'
  | 'phase'
  | 'qtl'
  | 'anova'
  | 'permutation'
  | 'linkage_map';

/** Status of a running analysis job */
export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

/** Molecular marker types supported */
export type MarkerType = 'SNP' | 'AFLP' | 'SSR' | 'RFLP' | 'UNKNOWN';

/** Navigation tree node types */
export type TreeNodeType =
  | 'project'
  | 'datasets'
  | 'dataset'
  | 'clusters'
  | 'cluster'
  | 'linkage_group'
  | 'analyses'
  | 'analysis'
  | 'ordered_result'
  | 'phase_result'
  | 'qtl_result'
  | 'linkage_maps'
  | 'linkage_map';

/** A TetraploidSNPMap project */
export interface Project {
  id: string;
  name: string;
  mode: TPMMode;
  created_at: string;
  updated_at: string;
  datasets: Dataset[];
}

/** An imported dataset within a project */
export interface Dataset {
  id: string;
  name: string;
  type: string;
  marker_count: number;
  individual_count: number;
  created_at: string;
}

/** A molecular marker with its properties */
export interface Marker {
  name: string;
  safe_name: string;
  type: MarkerType;
  checked: boolean;
  parent_dosage_1: string;
  parent_dosage_2: string;
  chi_sig: number;
  status: string;
  snp_ratio: string;
  nmiss: string;
  snp_patterns: SNPPattern[];
}

/** SNP segregation pattern */
export interface SNPPattern {
  dosage: string;
  count: string;
  proportion: string;
}

/** A linkage group containing markers */
export interface LinkageGroup {
  name: string;
  markers: Marker[];
  marker_count: number;
  selected_count: number;
}

/** A background analysis job */
export interface AnalysisJob {
  id: string;
  analysis_type: AnalysisType;
  status: JobStatus;
  params: Record<string, unknown>;
  created_at: string;
  completed_at?: string;
  error?: string;
  progress?: number;
}

/** Result of cluster analysis */
export interface ClusterResult {
  groups: LinkageGroup[];
  dendrogram?: DendrogramNode;
}

/** A node in a dendrogram tree */
export interface DendrogramNode {
  id: string;
  name?: string;
  distance: number;
  children?: DendrogramNode[];
}

/** Result of two-point ordering analysis */
export interface TwoPointResult {
  ordered_markers: Marker[];
  distances: number[];
  pairwise_data: number[][];
}

/** Result of MDS ordering analysis */
export interface MDSResult {
  ordered_markers: Marker[];
  distances: number[];
  coordinates_3d?: number[][];
  mean_nn_fit: number;
}

/** Result of phase analysis */
export interface PhaseResult {
  ordered_markers: Marker[];
  phases: string[][];
}

/** Data for QTL LOD score chart */
export interface QTLChartData {
  positions: number[];
  lod_scores: number[];
  threshold?: number;
  traits: string[];
}

/** Data for linkage map visualization */
export interface LinkageMapData {
  groups: LinkageMapGroup[];
}

/** A single group in a linkage map */
export interface LinkageMapGroup {
  name: string;
  markers: LinkageMapMarker[];
}

/** A positioned marker in a linkage map */
export interface LinkageMapMarker {
  name: string;
  position: number;
}

/** Navigation tree node */
export interface TreeNode {
  id: string;
  label: string;
  type: TreeNodeType;
  children?: TreeNode[];
  data?: unknown;
  expanded?: boolean;
}

/** Marker selection/filter criteria */
export interface MarkerSelectionCriteria {
  chi_sig_threshold: number;
  include_ok_only: boolean;
  include_fdr: boolean;
  include_fnp: boolean;
  require_both_parents: boolean;
}

/** File upload info */
export interface UploadFile {
  file: File;
  type: 'snploc' | 'qua' | 'loc' | 'map';
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  error?: string;
}

/** Export request */
export interface ExportRequest {
  project_id: string;
  format: 'csv' | 'tsv' | 'json' | 'pdf';
  content_type: 'markers' | 'map' | 'qtl' | 'phase';
  options?: Record<string, unknown>;
}

/** Paginated response wrapper */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** API error response */
export interface ApiError {
  detail: string;
  status_code: number;
}
