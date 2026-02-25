import { useState, useEffect } from 'react';
import { AlertTriangle, FileWarning, ChevronDown, ChevronUp } from 'lucide-react';
import { getQuarantineFiles, getQuarantineDetail } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';

export default function Quarantine() {
    const { t } = useTranslation();
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedFile, setExpandedFile] = useState(null);
    const [detail, setDetail] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);

    useEffect(() => {
        setLoading(true);
        getQuarantineFiles()
            .then(setFiles)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const toggleFile = async (filename) => {
        if (expandedFile === filename) {
            setExpandedFile(null);
            setDetail(null);
            return;
        }

        setExpandedFile(filename);
        setDetailLoading(true);
        try {
            const data = await getQuarantineDetail(filename);
            setDetail(data);
        } catch (e) {
            console.error(e);
        } finally {
            setDetailLoading(false);
        }
    };

    if (loading) {
        return (
            <>
                <div className="page-header">
                    <h2>{t('quarantine.title')}</h2>
                    <p>{t('quarantine.subtitleShort')}</p>
                </div>
                <div className="empty-state"><div className="spinner" style={{ margin: '0 auto' }}></div></div>
            </>
        );
    }

    return (
        <>
            <div className="page-header">
                <h2>{t('quarantine.title')}</h2>
                <p>{t('quarantine.subtitle')}</p>
            </div>

            {files.length === 0 ? (
                <div className="card">
                    <div className="empty-state">
                        <AlertTriangle size={48} />
                        <h3>{t('quarantine.noDataTitle')}</h3>
                        <p>{t('quarantine.noDataDesc')}</p>
                    </div>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {files.map((file) => (
                        <div key={file.filename} className="card" style={{ padding: 0, overflow: 'hidden' }}>
                            {/* File header */}
                            <div
                                onClick={() => toggleFile(file.filename)}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: 14,
                                    padding: '16px 20px', cursor: 'pointer',
                                    transition: 'background 150ms',
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99,102,241,0.06)'}
                                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                            >
                                <div className="metric-icon red" style={{ width: 36, height: 36, flexShrink: 0 }}>
                                    <FileWarning size={16} />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 2 }}>
                                        {file.filename}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                        {file.row_count} {t('quarantine.rejectedRows')} — {file.created_at?.split('T')[0]}
                                    </div>
                                </div>
                                <span className="badge failed">{file.row_count} {t('quarantine.rows')}</span>
                                {expandedFile === file.filename ?
                                    <ChevronUp size={18} style={{ color: 'var(--text-muted)' }} /> :
                                    <ChevronDown size={18} style={{ color: 'var(--text-muted)' }} />
                                }
                            </div>

                            {/* Expanded detail - dynamic columns */}
                            {expandedFile === file.filename && (
                                <div style={{ padding: '0 20px 20px', borderTop: '1px solid var(--border-subtle)' }}>
                                    {detailLoading ? (
                                        <div className="empty-state" style={{ padding: 24 }}>
                                            <div className="spinner" style={{ margin: '0 auto' }}></div>
                                        </div>
                                    ) : detail && (
                                        <div className="data-table-wrapper" style={{ marginTop: 12 }}>
                                            <table className="data-table">
                                                <thead>
                                                    <tr>
                                                        {(detail.columns || []).map((col) => (
                                                            <th key={col}>
                                                                {col === 'reject_reason'
                                                                    ? t('quarantine.rejectReason')
                                                                    : col
                                                                }
                                                            </th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {detail.rows.map((row, i) => (
                                                        <tr key={i}>
                                                            {(detail.columns || []).map((col) => (
                                                                <td key={col}>
                                                                    {col === 'reject_reason' ? (
                                                                        <span style={{
                                                                            color: 'var(--accent-red)', fontSize: '0.8rem',
                                                                            fontWeight: 500
                                                                        }}>
                                                                            {row[col]}
                                                                        </span>
                                                                    ) : (
                                                                        row[col] || <span style={{ color: 'var(--accent-red)' }}>{t('quarantine.empty')}</span>
                                                                    )}
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
