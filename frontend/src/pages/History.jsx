import { useState, useEffect } from 'react';
import { History, Clock, RefreshCw } from 'lucide-react';
import { getRuns } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';

export default function HistoryPage() {
    const { t } = useTranslation();
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchRuns = async () => {
        setLoading(true);
        try {
            const data = await getRuns(50, 0);
            setRuns(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchRuns(); }, []);

    const statusBadge = (status) => {
        const cls = status === 'SUCCESS' ? 'success' :
            status === 'FAILED' ? 'failed' :
                status === 'RUNNING' ? 'running' : 'pending';
        return (
            <span className={`badge ${cls}`}>
                <span className="badge-dot"></span>
                {status}
            </span>
        );
    };

    return (
        <>
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                    <h2>{t('history.title')}</h2>
                    <p>{t('history.subtitle')}</p>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={fetchRuns} disabled={loading}>
                    <RefreshCw size={14} /> {t('history.refresh')}
                </button>
            </div>

            <div className="card">
                {loading ? (
                    <div className="empty-state"><div className="spinner" style={{ margin: '0 auto' }}></div></div>
                ) : runs.length === 0 ? (
                    <div className="empty-state">
                        <History size={48} />
                        <h3>{t('history.noRunsTitle')}</h3>
                        <p>{t('history.noRunsDesc')}</p>
                    </div>
                ) : (
                    <div className="data-table-wrapper">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('history.status')}</th>
                                    <th>{t('history.file')}</th>
                                    <th>{t('history.mode')}</th>
                                    <th>{t('history.read')}</th>
                                    <th>{t('history.valid')}</th>
                                    <th>{t('history.rejected')}</th>
                                    <th>{t('history.dbInserts')}</th>
                                    <th>{t('history.dbUpdates')}</th>
                                    <th>{t('history.duration')}</th>
                                    <th>{t('history.started')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {runs.map((run) => (
                                    <tr key={run.id}>
                                        <td>{statusBadge(run.status)}</td>
                                        <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{run.file_name}</td>
                                        <td>
                                            {run.dry_run ? (
                                                <span className="badge pending" style={{ fontSize: '0.65rem' }}>{t('history.dryRun')}</span>
                                            ) : (
                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{t('history.live')}</span>
                                            )}
                                        </td>
                                        <td>{run.total_read ?? '—'}</td>
                                        <td style={{ color: 'var(--accent-green)' }}>{run.total_valid ?? '—'}</td>
                                        <td style={{ color: run.total_rejected > 0 ? 'var(--accent-red)' : 'var(--text-muted)' }}>
                                            {run.total_rejected ?? '—'}
                                        </td>
                                        <td>{run.db_inserts ?? '—'}</td>
                                        <td>{run.db_updates ?? '—'}</td>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                                <Clock size={12} style={{ color: 'var(--text-muted)' }} />
                                                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                                                    {run.duration ? `${run.duration}s` : '—'}
                                                </span>
                                            </div>
                                        </td>
                                        <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                            {run.started_at?.replace('T', ' ').split('.')[0]}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {runs.length > 0 && (
                <div style={{
                    marginTop: 16, fontSize: '0.8rem', color: 'var(--text-muted)',
                    display: 'flex', alignItems: 'center', gap: 6
                }}>
                    <History size={14} />
                    {runs.length === 1
                        ? t('history.showingRuns', { count: runs.length })
                        : t('history.showingRunsPlural', { count: runs.length })
                    }
                </div>
            )}
        </>
    );
}
