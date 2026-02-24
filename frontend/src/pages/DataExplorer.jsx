import { useState, useEffect, useCallback } from 'react';
import { Search, Database, ChevronLeft, ChevronRight } from 'lucide-react';
import { getRecords } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';

export default function DataExplorer() {
    const { t } = useTranslation();
    const [records, setRecords] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [perPage] = useState(25);
    const [totalPages, setTotalPages] = useState(1);
    const [loading, setLoading] = useState(false);

    // Filters
    const [search, setSearch] = useState('');
    const [product, setProduct] = useState('');
    const [storeId, setStoreId] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');

    const fetchRecords = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getRecords({
                page, per_page: perPage,
                search: search || undefined,
                product: product || undefined,
                store_id: storeId || undefined,
                date_from: dateFrom || undefined,
                date_to: dateTo || undefined,
            });
            setRecords(data.records);
            setTotal(data.total);
            setTotalPages(data.total_pages);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }, [page, perPage, search, product, storeId, dateFrom, dateTo]);

    useEffect(() => { fetchRecords(); }, [fetchRecords]);

    const handleSearch = () => { setPage(1); fetchRecords(); };

    return (
        <>
            <div className="page-header">
                <h2>{t('dataExplorer.title')}</h2>
                <p>{t('dataExplorer.subtitle')}</p>
            </div>

            {/* Filters */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="filters-bar">
                    <div className="form-group" style={{ flex: 2 }}>
                        <label className="form-label">{t('dataExplorer.search')}</label>
                        <input
                            className="form-input"
                            placeholder={t('dataExplorer.searchPlaceholder')}
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('dataExplorer.product')}</label>
                        <input
                            className="form-input"
                            placeholder={t('dataExplorer.filterProduct')}
                            value={product}
                            onChange={(e) => setProduct(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('dataExplorer.storeId')}</label>
                        <input
                            className="form-input"
                            placeholder={t('dataExplorer.storeIdPlaceholder')}
                            value={storeId}
                            onChange={(e) => setStoreId(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('dataExplorer.dateFrom')}</label>
                        <input
                            className="form-input"
                            type="date"
                            value={dateFrom}
                            onChange={(e) => setDateFrom(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('dataExplorer.dateTo')}</label>
                        <input
                            className="form-input"
                            type="date"
                            value={dateTo}
                            onChange={(e) => setDateTo(e.target.value)}
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
                                        <th>{t('dataExplorer.id')}</th>
                                        <th>{t('dataExplorer.date')}</th>
                                        <th>{t('dataExplorer.product')}</th>
                                        <th>{t('dataExplorer.qty')}</th>
                                        <th>{t('dataExplorer.price')}</th>
                                        <th>{t('dataExplorer.store')}</th>
                                        <th>{t('dataExplorer.lastUpdated')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {records.map((r) => (
                                        <tr key={r.id}>
                                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{r.id}</td>
                                            <td>{r.date}</td>
                                            <td style={{ color: 'var(--text-primary)' }}>{r.product}</td>
                                            <td>{r.qty}</td>
                                            <td style={{ color: 'var(--accent-green)' }}>${Number(r.price).toFixed(2)}</td>
                                            <td><span className="badge pending">{r.store_id}</span></td>
                                            <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                                {r.last_updated?.split('.')[0]}
                                            </td>
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
