import { getActiveRunId } from './runState';

const API_BASE = import.meta.env.VITE_API_URL || '';

async function request(url, options = {}) {
    const response = await fetch(`${API_BASE}${url}`, {
        headers: {
            'Accept': 'application/json',
            ...options.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

export async function launchPipeline(file, dryRun = false, autoDetect = false) {
    const formData = new FormData();
    if (file) formData.append('file', file);
    formData.append('dry_run', dryRun.toString());
    formData.append('auto_detect', autoDetect.toString());

    return request('/pipeline/run', {
        method: 'POST',
        body: formData,
    });
}

export async function getRuns(limit = 50, offset = 0) {
    return request(`/pipeline/runs?limit=${limit}&offset=${offset}`);
}

export async function getRun(runId) {
    return request(`/pipeline/runs/${runId}`);
}

export async function getRecords(params = {}) {
    const searchParams = new URLSearchParams();
    const withRun = { run_id: getActiveRunId(), ...params };
    Object.entries(withRun).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
            searchParams.set(key, val);
        }
    });
    return request(`/data/records?${searchParams.toString()}`);
}

export async function getQuarantineFiles() {
    return request('/quarantine');
}

export async function getQuarantineDetail(filename) {
    return request(`/quarantine/${filename}`);
}

export async function getAnalytics() {
    return request(`/data/analytics?run_id=${encodeURIComponent(getActiveRunId())}`);
}

export async function getSchema() {
    return request(`/data/schema?run_id=${encodeURIComponent(getActiveRunId())}`);
}

async function downloadExport(format, filename) {
    const runId = encodeURIComponent(getActiveRunId());
    const response = await fetch(`${API_BASE}/data/export?run_id=${runId}&format=${format}`);
    if (!response.ok) throw new Error('Export failed');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}

export async function exportCSV() {
    return downloadExport('csv', 'datrix_export.csv');
}

export async function exportExcel() {
    return downloadExport('xlsx', 'datrix_export.xlsx');
}

export async function resetData() {
    return request('/data/reset', { method: 'DELETE' });
}
