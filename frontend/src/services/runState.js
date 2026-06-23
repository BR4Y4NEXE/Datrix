// Per-visitor run isolation, no login. sessionStorage gives the "ephemeral"
// feel: closing the tab resets the visitor back to the demo run only.
const ACTIVE_KEY = 'datrix_active_run';
const SESSION_RUNS_KEY = 'datrix_session_runs';

export function getActiveRunId() {
    return sessionStorage.getItem(ACTIVE_KEY) || 'demo';
}

export function getSessionRunIds() {
    try {
        return JSON.parse(sessionStorage.getItem(SESSION_RUNS_KEY)) || [];
    } catch {
        return [];
    }
}

export function setActiveRunId(runId) {
    sessionStorage.setItem(ACTIVE_KEY, runId);
    if (runId === 'demo') return;
    const runs = getSessionRunIds();
    if (!runs.includes(runId)) {
        runs.push(runId);
        sessionStorage.setItem(SESSION_RUNS_KEY, JSON.stringify(runs));
    }
}
