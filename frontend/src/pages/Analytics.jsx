import { useState, useEffect } from 'react';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
    BarChart3, Download, TrendingUp, ShoppingBag,
    Store, PieChart as PieIcon, RefreshCw
} from 'lucide-react';
import { getAnalytics, exportCSV } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';

const CHART_COLORS = [
    '#31cab0', '#a78bfa', '#f7b731', '#fc5c65',
    '#fd9644', '#45aaf2', '#26de81', '#e056a0',
    '#f7d794', '#778ca3'
];

const tooltipStyle = {
    backgroundColor: '#1e3148',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 6,
    color: '#e4e8ee',
    fontSize: '0.8rem',
};

export default function Analytics() {
    const { t } = useTranslation();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [exporting, setExporting] = useState(false);
    const [activeChart, setActiveChart] = useState('revenue'); // 'revenue' or 'qty'

    const fetchData = async () => {
        setLoading(true);
        try {
            const result = await getAnalytics();
            setData(result);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    const handleExport = async () => {
        setExporting(true);
        try {
            await exportCSV();
        } catch (e) {
            console.error(e);
        } finally {
            setExporting(false);
        }
    };

    if (loading) {
        return (
            <>
                <div className="page-header">
                    <h2>{t('analytics.title')}</h2>
                    <p>{t('analytics.loadingSubtitle')}</p>
                </div>
                <div className="empty-state"><div className="spinner" style={{ margin: '0 auto' }}></div></div>
            </>
        );
    }

    if (!data || data.summary.total_records === 0) {
        return (
            <>
                <div className="page-header">
                    <h2>{t('analytics.title')}</h2>
                    <p>{t('analytics.subtitleEmpty')}</p>
                </div>
                <div className="card">
                    <div className="empty-state">
                        <BarChart3 size={48} />
                        <h3>{t('analytics.noDataTitle')}</h3>
                        <p>{t('analytics.noDataDesc')}</p>
                    </div>
                </div>
            </>
        );
    }

    const { by_product, by_store, over_time, summary, quality } = data;

    // Data quality pie chart data
    const qualityTotals = quality.reduce(
        (acc, r) => ({
            valid: acc.valid + (r.total_valid || 0),
            rejected: acc.rejected + (r.total_rejected || 0),
        }),
        { valid: 0, rejected: 0 }
    );
    const qualityPie = [
        { name: t('analytics.validRecords'), value: qualityTotals.valid, color: '#31cab0' },
        { name: t('analytics.rejectedRecords'), value: qualityTotals.rejected, color: '#fc5c65' },
    ];

    return (
        <>
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                    <h2>{t('analytics.title')}</h2>
                    <p>{t('analytics.subtitle')}</p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-secondary btn-sm" onClick={fetchData}>
                        <RefreshCw size={14} /> {t('analytics.refresh')}
                    </button>
                    <button className="btn btn-primary btn-sm" onClick={handleExport} disabled={exporting}>
                        <Download size={14} /> {exporting ? t('analytics.exporting') : t('analytics.exportCsv')}
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-icon cyan"><ShoppingBag size={18} /></div>
                    <div className="metric-content">
                        <div className="metric-value">{summary.total_records.toLocaleString()}</div>
                        <div className="metric-label">{t('analytics.totalRecords')}</div>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon green"><TrendingUp size={18} /></div>
                    <div className="metric-content">
                        <div className="metric-value">${summary.total_revenue.toLocaleString()}</div>
                        <div className="metric-label">{t('analytics.totalRevenue')}</div>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon purple"><Store size={18} /></div>
                    <div className="metric-content">
                        <div className="metric-value">{summary.unique_stores}</div>
                        <div className="metric-label">{t('analytics.uniqueStores')}</div>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon amber"><BarChart3 size={18} /></div>
                    <div className="metric-content">
                        <div className="metric-value">{summary.unique_products}</div>
                        <div className="metric-label">{t('analytics.uniqueProducts')}</div>
                    </div>
                </div>
            </div>

            {/* Revenue Trend Over Time */}
            {over_time.length > 0 && (
                <div className="card" style={{ marginBottom: 20 }}>
                    <div className="card-title">
                        <TrendingUp size={16} /> {t('analytics.salesTrend')}
                        <span className="card-subtitle" style={{ marginLeft: 'auto' }}>
                            {over_time.length} {t('analytics.dataPoints')}
                        </span>
                    </div>
                    <ResponsiveContainer width="100%" height={280}>
                        <LineChart data={over_time} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis
                                dataKey="date" stroke="#6b7a8d" fontSize={11}
                                tickFormatter={(v) => v?.slice(5) || v}
                            />
                            <YAxis stroke="#6b7a8d" fontSize={11} />
                            <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#e4e8ee' }} itemStyle={{ color: '#a0aec0' }} />
                            <Line
                                type="monotone" dataKey="revenue" name={t('analytics.revenue')}
                                stroke="#31cab0" strokeWidth={2} dot={false}
                                activeDot={{ r: 4, fill: '#31cab0' }}
                            />
                            <Line
                                type="monotone" dataKey="qty" name={t('analytics.quantity')}
                                stroke="#a78bfa" strokeWidth={2} dot={false}
                                activeDot={{ r: 4, fill: '#a78bfa' }}
                            />
                            <Legend wrapperStyle={{ fontSize: '0.8rem', color: '#a0aec0' }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            <div className="grid-2">
                {/* Sales by Product */}
                <div className="card">
                    <div className="card-title">
                        <ShoppingBag size={16} /> {t('analytics.topProducts')}
                    </div>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={by_product} margin={{ top: 5, right: 10, left: 10, bottom: 60 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis
                                dataKey="product" stroke="#6b7a8d" fontSize={10}
                                interval={0} angle={-35} textAnchor="end"
                            />
                            <YAxis stroke="#6b7a8d" fontSize={11} />
                            <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#e4e8ee' }} itemStyle={{ color: '#a0aec0' }} cursor={{ stroke: 'rgba(255,255,255,0.1)' }} />
                            <Bar dataKey="revenue" name={t('analytics.revenue')} radius={[4, 4, 0, 0]}>
                                {by_product.map((_, i) => (
                                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Sales by Store */}
                <div className="card">
                    <div className="card-title">
                        <Store size={16} /> {t('analytics.salesByStore')}
                    </div>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={by_store} layout="vertical" margin={{ top: 5, right: 20, left: 40, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis type="number" stroke="#6b7a8d" fontSize={11} />
                            <YAxis
                                type="category" dataKey="store_id" stroke="#6b7a8d"
                                fontSize={11} width={50}
                            />
                            <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#e4e8ee' }} itemStyle={{ color: '#a0aec0' }} />
                            <Bar dataKey="revenue" name={t('analytics.revenue')} radius={[0, 4, 4, 0]}>
                                {by_store.map((_, i) => (
                                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Data Quality */}
            {qualityTotals.valid + qualityTotals.rejected > 0 && (
                <div className="card" style={{ marginTop: 20 }}>
                    <div className="card-title"><PieIcon size={16} /> {t('analytics.dataQuality')}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
                        <ResponsiveContainer width="40%" height={200}>
                            <PieChart>
                                <Pie
                                    data={qualityPie} dataKey="value" nameKey="name"
                                    cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                                    strokeWidth={0}
                                >
                                    {qualityPie.map((entry, i) => (
                                        <Cell key={i} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#e4e8ee' }} itemStyle={{ color: '#a0aec0' }} />
                            </PieChart>
                        </ResponsiveContainer>
                        <div style={{ flex: 1 }}>
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                                    <div style={{ width: 12, height: 12, borderRadius: 3, background: '#31cab0' }}></div>
                                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{t('analytics.validRecords')}</span>
                                    <strong style={{ marginLeft: 'auto', color: 'var(--accent-teal)' }}>
                                        {qualityTotals.valid.toLocaleString()}
                                    </strong>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <div style={{ width: 12, height: 12, borderRadius: 3, background: '#fc5c65' }}></div>
                                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{t('analytics.rejectedRecords')}</span>
                                    <strong style={{ marginLeft: 'auto', color: 'var(--accent-red)' }}>
                                        {qualityTotals.rejected.toLocaleString()}
                                    </strong>
                                </div>
                            </div>
                            <div style={{
                                fontSize: '0.8rem', color: 'var(--text-muted)', padding: '10px 12px',
                                background: 'rgba(255,255,255,0.03)', borderRadius: 6
                            }}>
                                {t('analytics.passRate')}{' '}
                                <strong style={{ color: 'var(--accent-teal)' }}>
                                    {((qualityTotals.valid / (qualityTotals.valid + qualityTotals.rejected)) * 100).toFixed(1)}%
                                </strong>
                                {' '}{quality.length === 1
                                    ? t('analytics.acrossPipelineRuns', { count: quality.length })
                                    : t('analytics.acrossPipelineRunsPlural', { count: quality.length })
                                }
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
