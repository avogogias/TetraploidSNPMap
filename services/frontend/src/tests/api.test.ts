/**
 * API client module tests.
 *
 * Validates the structure and configuration of the API client
 * that communicates with the backend services.
 */
import { describe, it, expect } from 'vitest';
import api, {
  projectsApi,
  datasetsApi,
  analysesApi,
  exportsApi,
  visualizationApi,
} from '../services/api';

describe('API client configuration', () => {
  it('has correct base URL', () => {
    expect(api.defaults.baseURL).toBe('/api');
  });

  it('has 60 second timeout', () => {
    expect(api.defaults.timeout).toBe(60_000);
  });

  it('sets JSON content type', () => {
    expect(api.defaults.headers['Content-Type']).toBe('application/json');
  });
});

describe('projectsApi', () => {
  it('exposes CRUD methods', () => {
    expect(typeof projectsApi.list).toBe('function');
    expect(typeof projectsApi.get).toBe('function');
    expect(typeof projectsApi.create).toBe('function');
    expect(typeof projectsApi.update).toBe('function');
    expect(typeof projectsApi.delete).toBe('function');
  });
});

describe('datasetsApi', () => {
  it('exposes dataset management methods', () => {
    expect(typeof datasetsApi.list).toBe('function');
    expect(typeof datasetsApi.get).toBe('function');
    expect(typeof datasetsApi.upload).toBe('function');
    expect(typeof datasetsApi.delete).toBe('function');
  });

  it('exposes marker management methods', () => {
    expect(typeof datasetsApi.getMarkers).toBe('function');
    expect(typeof datasetsApi.updateMarkerSelection).toBe('function');
    expect(typeof datasetsApi.selectAll).toBe('function');
    expect(typeof datasetsApi.selectNone).toBe('function');
    expect(typeof datasetsApi.invertSelection).toBe('function');
    expect(typeof datasetsApi.applySelectionCriteria).toBe('function');
  });
});

describe('analysesApi', () => {
  it('exposes analysis job methods', () => {
    expect(typeof analysesApi.list).toBe('function');
    expect(typeof analysesApi.get).toBe('function');
    expect(typeof analysesApi.submit).toBe('function');
    expect(typeof analysesApi.cancel).toBe('function');
    expect(typeof analysesApi.getResults).toBe('function');
  });
});

describe('exportsApi', () => {
  it('exposes export methods', () => {
    expect(typeof exportsApi.create).toBe('function');
    expect(typeof exportsApi.download).toBe('function');
  });

  it('download returns a URL string', () => {
    const url = exportsApi.download('p1', 'e1');
    expect(url).toBe('/api/projects/p1/exports/e1/download');
  });
});

describe('visualizationApi', () => {
  it('exposes all visualization methods', () => {
    expect(typeof visualizationApi.getDendrogram).toBe('function');
    expect(typeof visualizationApi.getLinkageMap).toBe('function');
    expect(typeof visualizationApi.getQTLChart).toBe('function');
    expect(typeof visualizationApi.getPairwiseMatrix).toBe('function');
    expect(typeof visualizationApi.getMDS3D).toBe('function');
    expect(typeof visualizationApi.getPhaseTable).toBe('function');
  });
});
