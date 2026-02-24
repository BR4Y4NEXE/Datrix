import { useState, useRef, useEffect, useCallback } from 'react';
import {
    Upload, Play, FileText, CheckCircle, XCircle,
    Clock, Database, AlertTriangle, Zap, BarChart3
} from 'lucide-react';
import { launchPipeline, getRuns } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { useTranslation } from '../i18n/LanguageContext';

export default function Dashboard() {
    const { t } = useTranslation();
    const [file, setFile] = useState(null);
    const [dryRun, setDryRun] = useState(false);
    const [autoDetect, setAutoDetect] = useState(false);
    const [isRunning, setIsRunning] = useState(false);
    const [currentRunId, setCurrentRunId] = useState(null);
    const [lastRun, setLastRun] = useState(null);
    const [error, setError] = useState('');
    const [dragOver, setDragOver] = useState(false);
    const fileInputRef = useRef(null);
    const logContainerRef = useRef(null);

    const { logs, isConnected, clearLogs } = useWebSocket(currentRunId);

    // Auto-scroll logs
    useEffect(() => {
        if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [logs]);

    // Poll for run completion
    useEffect(() => {
        if (!currentRunId || !isRunning) return;
        const interval = setInterval(async () => {
            try {
                const runs = await getRuns(1, 0);
                if (runs.length > 0 && runs[0].id === currentRunId) {
                    const run = runs[0];
                    if (run.status === 'SUCCESS' || run.status === 'FAILED') {
                        setLastRun(run);
                        setIsRunning(false);
                    }
                }
            } catch (e) { /* ignore poll errors */ }
        }, 2000);
        return () => clearInterval(interval);
    }, [currentRunId, isRunning]);

    // Load last run on mount
    useEffect(() => {
        getRuns(1, 0).then(runs => {
            if (runs.length > 0) setLastRun(runs[0]);
        }).catch(() => { });
    }, []);

    const handleLaunch = async () => {
        if (!file && !autoDetect) {
            setError(t('dashboard.uploadError'));
            return;
        }
        setError('');
        clearLogs();
        setIsRunning(true);

        try {
            const result = await launchPipeline(file, dryRun, autoDetect);
            setCurrentRunId(result.run_id);
        } catch (e) {
            setError(e.message);
            setIsRunning(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const f = e.dataTransfer.files[0];
        if (f && f.name.endsWith('.csv')) {
            setFile(f);
            setAutoDetect(false);
        }
    };

    const handleFileSelect = (e) => {
        const f = e.target.files[0];
        if (f) {
            setFile(f);
            setAutoDetect(false);
        }
    };

    return (
        <>
            <div className="page-header">
                <h2>{t('dashboard.title')}</h2>
                <p>{t('dashboard.subtitle')}</p>
            </div>

            {/* Metrics */}
            {lastRun && (
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-icon cyan"><FileText size={18} /></div>
                        <div className="metric-content">
                            <div className="metric-value">{lastRun.total_read ?? '—'} <span className="metric-label-inline">{t('dashboard.rows')}</span></div>
                            <div className="metric-label">{t('dashboard.totalRead')}</div>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon green"><CheckCircle size={18} /></div>
                        <div className="metric-content">
                            <div className="metric-value">{lastRun.total_valid ?? '—'} <span className="metric-label-inline">{t('dashboard.valid')}</span></div>
                            <div className="metric-label">{t('dashboard.recordsPassed')}</div>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon red"><XCircle size={18} /></div>
                        <div className="metric-content">
                            <div className="metric-value">{lastRun.total_rejected ?? '—'} <span className="metric-label-inline">{t('dashboard.rejected')}</span></div>
                            <div className="metric-label">{t('dashboard.quarantinedRows')}</div>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon purple"><Database size={18} /></div>
                        <div className="metric-content">
                            <div className="metric-value">{(lastRun.db_inserts ?? 0) + (lastRun.db_updates ?? 0)} <span className="metric-label-inline">{t('dashboard.writes')}</span></div>
                            <div className="metric-label">{t('dashboard.dbOperations')}</div>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon amber"><Clock size={18} /></div>
                        <div className="metric-content">
                            <div className="metric-value">{lastRun.duration ?? '—'}s <span className="metric-label-inline">{t('dashboard.duration')}</span></div>
                            <div className="metric-label">{t('dashboard.executionTime')}</div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid-2">
                {/* Execution Panel */}
                <div className="card">
                    <div className="card-title"><Zap size={16} /> {t('dashboard.pipelineExecution')}</div>

                    {/* File Upload */}
                    <div
                        className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
                        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                        onClick={() => !autoDetect && fileInputRef.current?.click()}
                    >
                        <Upload className="upload-icon" />
                        {file ? (
                            <>
                                <p>{t('dashboard.selectedFile')}</p>
                                <div className="file-name">{file.name}</div>
                            </>
                        ) : (
                            <p>{t('dashboard.dropCsv')}</p>
                        )}
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".csv"
                            style={{ display: 'none' }}
                            onChange={handleFileSelect}
                        />
                    </div>

                    {/* Options */}
                    <div style={{ marginTop: 20 }}>
                        <div className="toggle-group">
                            <div
                                className={`toggle ${autoDetect ? 'active' : ''}`}
                                onClick={() => { setAutoDetect(!autoDetect); if (!autoDetect) setFile(null); }}
                            >
                                <div className="toggle-knob"></div>
                            </div>
                            <span className="toggle-label">{t('dashboard.autoDetect')}</span>
                        </div>

                        <div className="toggle-group">
                            <div
                                className={`toggle ${dryRun ? 'active' : ''}`}
                                onClick={() => setDryRun(!dryRun)}
                            >
                                <div className="toggle-knob"></div>
                            </div>
                            <span className="toggle-label">{t('dashboard.dryRun')}</span>
                        </div>
                    </div>

                    {error && (
                        <div style={{ marginTop: 12, color: 'var(--accent-red)', fontSize: '0.85rem' }}>
                            ⚠ {error}
                        </div>
                    )}

                    <button
                        className="btn btn-primary"
                        style={{ marginTop: 20, width: '100%' }}
                        onClick={handleLaunch}
                        disabled={isRunning}
                    >
                        {isRunning ? (
                            <><div className="spinner"></div> {t('dashboard.pipelineRunning')}</>
                        ) : (
                            <><Play size={16} /> {t('dashboard.launchPipeline')}</>
                        )}
                    </button>

                    {dryRun && (
                        <div style={{
                            marginTop: 8, fontSize: '0.75rem', color: 'var(--accent-amber)',
                            textAlign: 'center'
                        }}>
                            {t('dashboard.dryRunWarning')}
                        </div>
                    )}
                </div>

                {/* Live Log Viewer */}
                <div className="card">
                    <div className="card-title">
                        <BarChart3 size={16} /> {t('dashboard.liveLogStream')}
                        {isConnected && (
                            <span className="badge running" style={{ marginLeft: 'auto', fontSize: '0.65rem' }}>
                                <span className="badge-dot"></span> LIVE
                            </span>
                        )}
                    </div>

                    <div className="log-viewer" ref={logContainerRef}>
                        {logs.length === 0 ? (
                            <div className="log-empty">
                                {t('dashboard.waitingForPipeline')}<br />
                                {t('dashboard.logsWillAppear')}
                            </div>
                        ) : (
                            logs.map((log, i) => (
                                <div key={i} className={`log-line ${log.level}`}>
                                    {log.text}
                                </div>
                            ))
                        )}
                    </div>

                    {lastRun && !isRunning && (
                        <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span className="badge-dot" style={{
                                width: 8, height: 8, borderRadius: '50%', display: 'inline-block',
                                background: lastRun.status === 'SUCCESS' ? 'var(--accent-green)' : 'var(--accent-red)'
                            }}></span>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                {t('dashboard.lastRun')} <strong style={{ color: 'var(--text-secondary)' }}>{lastRun.file_name}</strong>
                                {' — '}{lastRun.status} in {lastRun.duration}s
                            </span>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
