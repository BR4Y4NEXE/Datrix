import { useState, useEffect, useCallback } from 'react';
import { Search, Database, ChevronLeft, ChevronRight } from 'lucide-react';
import { getRecords, getSchema } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';

export default function DataExplorer() {
    const { t } = useTranslation();
    const [records, setRecords] = useState([]);
    const [columns, setColumns] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [perPage] = useState(25);
    const [totalPages, setTotalPages] = useState(1);
    const [loading, setLoading] = useState(false);

    // Filters
    const [search, setSearch] = useState('');

    // Fetch schema on mount
    useEffect(() => {
        getSchema()
            .then((data) => {
                setColumns(data.columns || []);
            })
            .catch(() => setColumns([]));
    }, []);

    const fetchRecords = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getRecords({
                page, per_page: perPage,
                search: search || undefined,
            });
            setRecords(data.records);
            setTotal(data.total);
            setTotalPages(data.total_pages);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }, [page, perPage, search]);

    useEffect(() => { fetchRecords(); }, [fetchRecords]);

    const handleSearch = () => { setPage(1); fetchRecords(); };

    // Format cell value based on column type
    const formatCell = (value, colType) => {
        if (value === null || value === undefined || value === '') {
            return <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>—</span>;
        }
        if (colType === 'numeric') {
            const num = Number(value);
            if (!isNaN(num)) {
                return num % 1 === 0 ? num.toLocaleString() : num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
        }
        if (colType === 'date') {
            return <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>{value}</span>;
        }
        return String(value);
    };

    return (
        <>
            <div className="page-header">
                <h2>{t('dataExplorer.title')}</h2>
                <p>{t('dataExplorer.subtitle')}</p>
            </div>

            {/* Search Filter */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="filters-bar">
                    <div className="form-group" style={{ flex: 1 }}>
                        <label className="form-label">{t('dataExplorer.search')}</label>
                        <input
                            className="form-input"
                            placeholder={t('dataExplorer.searchPlaceholder')}
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        />
                    </div>
                    <button className="btn btn-primary btn-sm" onClick={handleSearch} style={{ height: 38 }}>
                        <Search size={14} /> {t('dataExplorer.filter')}
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="card">
                <div className="card-title">
                    <Database size={16} /> {t('dataExplorer.records')}
                    <span style={{ marginLeft: 'auto', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
                        {total.toLocaleString()} {t('dataExplorer.total')}
                        {columns.length > 0 && ` · ${columns.length} ${t('dataExplorer.columns')}`}
                    </span>
                </div>

                {loading ? (
                    <div className="empty-state"><div className="spinner" style={{ margin: '0 auto' }}></div></div>
                ) : records.length === 0 ? (
                    <div className="empty-state">
                        <Database size={48} />
                        <h3>{t('dataExplorer.noRecordsTitle')}</h3>
                        <p>{t('dataExplorer.noRecordsDesc')}</p>
                    </div>
                ) : (
                    <>
                        <div className="data-table-wrapper">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        {columns.length > 0
                                            ? columns.map((col) => (
                                                <th key={col.column_name}>
                                                    {col.original_name}
                                                    <span style={{
                                                        display: 'block', fontSize: '0.65rem',
                                                        color: 'var(--text-muted)', fontWeight: 400,
                                                        textTransform: 'uppercase', letterSpacing: '0.5px'
                                                    }}>
                                                        {col.column_type}
                                                    </span>
                                                </th>
                                            ))
                                            : records.length > 0 && Object.keys(records[0]).map((key) => (
                                                <th key={key}>{key}</th>
                                            ))
                                        }
                                    </tr>
                                </thead>
                                <tbody>
                                    {records.map((r, idx) => (
                                        <tr key={idx}>
                                            {columns.length > 0
                                                ? columns.map((col) => (
                                                    <td key={col.column_name}
                                                        style={col.column_type === 'numeric'
                                                            ? { color: 'var(--accent-green)', fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }
                                                            : {}
                                                        }
                                                    >
                                                        {formatCell(r[col.column_name], col.column_type)}
                                                    </td>
                                                ))
                                                : Object.values(r).map((val, i) => (
                                                    <td key={i}>{val !== null ? String(val) : '—'}</td>
                                                ))
                                            }
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <div className="pagination">
                            <div className="pagination-info">
                                {t('dataExplorer.page')} {page} {t('dataExplorer.of')} {totalPages} — {t('dataExplorer.showing')} {records.length} {t('dataExplorer.of')} {total}
                            </div>
                            <div className="pagination-controls">
                                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                                    <ChevronLeft size={14} />
                                </button>
                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                    const start = Math.max(1, Math.min(page - 2, totalPages - 4));
                                    const p = start + i;
                                    if (p > totalPages) return null;
                                    return (
                                        <button
                                            key={p}
                                            className={p === page ? 'active' : ''}
                                            onClick={() => setPage(p)}
                                        >
                                            {p}
                                        </button>
                                    );
                                })}
                                <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                                    <ChevronRight size={14} />
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </>
    );
}
