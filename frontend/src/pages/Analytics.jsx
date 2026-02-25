import { useState, useEffect } from 'react';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
    BarChart3, Download, TrendingUp, Hash,
    Layers, PieChart as PieIcon, RefreshCw
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

    const { charts, summary, quality } = data;
    const numericCols = summary.numeric_columns || [];
    const textCols = summary.text_columns || [];

    // Data quality pie chart data
    const qualityTotals = (quality || []).reduce(
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

    // Icons for summary cards
    const ICONS = [TrendingUp, Hash, Layers, BarChart3];

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

            {/* Summary Cards - Dynamic */}
            <div className="metrics-grid">
                {/* Total Records */}
                <div className="metric-card">
                    <div className="metric-icon cyan"><BarChart3 size={18} /></div>
                    <div className="metric-content">
                        <div className="metric-value">{summary.total_records.toLocaleString()}</div>
                        <div className="metric-label">{t('analytics.totalRecords')}</div>
                    </div>
                </div>
                {/* Columns Count */}
                <div className="metric-card">
                    <div className="metric-icon purple"><Layers size={18} /></div>
                    <div className="metric-content">
                        <div className="metric-value">{summary.columns}</div>
                        <div className="metric-label">{t('analytics.columns')}</div>
                    </div>
                </div>
                {/* First two numeric column summaries */}
                {numericCols.slice(0, 2).map((nc, i) => {
                    const Icon = ICONS[i % ICONS.length];
                    return (
                        <div className="metric-card" key={nc.column}>
                            <div className={`metric-icon ${i === 0 ? 'green' : 'amber'}`}><Icon size={18} /></div>
                            <div className="metric-content">
                                <div className="metric-value">{nc.sum.toLocaleString()}</div>
                                <div className="metric-label">{t('analytics.sum')}: {nc.original_name}</div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Dynamic numeric stats table */}
            {numericCols.length > 0 && (
                <div className="card" style={{ marginBottom: 20 }}>
                    <div className="card-title">
                        <Hash size={16} /> Numeric Column Statistics
                    </div>
                    <div className="data-table-wrapper">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Column</th>
                                    <th>{t('analytics.sum')}</th>
                                    <th>{t('analytics.avg')}</th>
                                    <th>Min</th>
                                    <th>Max</th>
                                </tr>
                            </thead>
                            <tbody>
                                {numericCols.map((nc) => (
                                    <tr key={nc.column}>
                                        <td style={{ fontWeight: 600 }}>{nc.original_name}</td>
                                        <td style={{ color: 'var(--accent-green)' }}>{nc.sum.toLocaleString()}</td>
                                        <td>{nc.avg.toLocaleString()}</td>
                                        <td>{nc.min.toLocaleString()}</td>
                                        <td>{nc.max.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Text column unique values */}
            {textCols.length > 0 && (
                <div className="card" style={{ marginBottom: 20 }}>
                    <div className="card-title">
                        <Layers size={16} /> Categorical Columns
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                        {textCols.map((tc) => (
                            <div key={tc.column} style={{
                                padding: '10px 16px', borderRadius: 8,
                                background: 'rgba(255,255,255,0.03)',
                                border: '1px solid var(--border-subtle)',
                                minWidth: 120,
                            }}>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4 }}>
                                    {tc.original_name}
                                </div>
                                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>
                                    {tc.unique_values} <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 400 }}>{t('analytics.uniqueValues')}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Dynamic Charts from Backend */}
            {charts.length > 0 && (
                <div className="grid-2">
                    {charts.map((chart, ci) => (
                        <div className="card" key={ci}>
                            <div className="card-title">
                                {chart.type === 'line' ? <TrendingUp size={16} /> : <BarChart3 size={16} />}
                                {' '}{chart.title}
                                <span className="card-subtitle" style={{ marginLeft: 'auto' }}>
                                    {chart.data.length} {t('analytics.dataPoints')}
                                </span>
                            </div>
                            <ResponsiveContainer width="100%" height={280}>
                                {chart.type === 'line' ? (
                                    <LineChart data={chart.data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                        <XAxis
                                            dataKey={chart.x_key} stroke="#6b7a8d" fontSize={11}
                                            tickFormatter={(v) => v?.slice(5) || v}
                                        />
                                        <YAxis stroke="#6b7a8d" fontSize={11} />
                                        <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#e4e8ee' }} itemStyle={{ color: '#a0aec0' }} />
                                        <Line
                                            type="monotone" dataKey={chart.y_key}
                                            name={chart.title}
                                            stroke="#31cab0" strokeWidth={2} dot={false}
                                            activeDot={{ r: 4, fill: '#31cab0' }}
                                        />
                                        <Legend wrapperStyle={{ fontSize: '0.8rem', color: '#a0aec0' }} />
                                    </LineChart>
                                ) : (
                                    <BarChart data={chart.data} margin={{ top: 5, right: 10, left: 10, bottom: 60 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                        <XAxis
                                            dataKey={chart.category_key} stroke="#6b7a8d" fontSize={10}
                                            interval={0} angle={-35} textAnchor="end"
                                        />
                                        <YAxis stroke="#6b7a8d" fontSize={11} />
                                        <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#e4e8ee' }} itemStyle={{ color: '#a0aec0' }} cursor={{ stroke: 'rgba(255,255,255,0.1)' }} />
                                        <Bar dataKey={chart.value_key} name={chart.title} radius={[4, 4, 0, 0]}>
                                            {chart.data.map((_, i) => (
                                                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                )}
                            </ResponsiveContainer>
                        </div>
                    ))}
                </div>
            )}

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
                                {' '}{(quality || []).length === 1
                                    ? t('analytics.acrossPipelineRuns', { count: (quality || []).length })
                                    : t('analytics.acrossPipelineRunsPlural', { count: (quality || []).length })
                                }
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
