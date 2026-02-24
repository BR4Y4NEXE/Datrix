import { useState, useEffect } from 'react';
import { Bell, Mail, MessageSquare, CheckCircle, XCircle } from 'lucide-react';
import { getNotificationStatus } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';

export default function Notifications() {
    const { t } = useTranslation();
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getNotificationStatus()
            .then(setStatus)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <>
                <div className="page-header">
                    <h2>{t('notifications.title')}</h2>
                    <p>{t('notifications.subtitleLoading')}</p>
                </div>
                <div className="empty-state"><div className="spinner" style={{ margin: '0 auto' }}></div></div>
            </>
        );
    }

    const channels = [
        {
            name: t('notifications.emailSmtp'),
            icon: Mail,
            enabled: status?.email_enabled,
            configured: status?.smtp_configured,
            description: status?.smtp_configured
                ? t('notifications.smtpReady')
                : t('notifications.smtpConfigure'),
        },
        {
            name: t('notifications.slackWebhook'),
            icon: MessageSquare,
            enabled: status?.slack_enabled,
            configured: status?.slack_configured,
            description: status?.slack_configured
                ? t('notifications.slackReady')
                : t('notifications.slackConfigure'),
        },
    ];

    return (
        <>
            <div className="page-header">
                <h2>{t('notifications.title')}</h2>
                <p>{t('notifications.subtitle')}</p>
            </div>

            <div className="notification-grid">
                {channels.map((ch) => (
                    <div key={ch.name} className="notif-card">
                        <div className={`notif-icon ${ch.enabled ? 'enabled' : 'disabled'}`}>
                            <ch.icon size={20} />
                        </div>
                        <div className="notif-info">
                            <h4 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                {ch.name}
                                {ch.enabled ? (
                                    <CheckCircle size={14} style={{ color: 'var(--accent-green)' }} />
                                ) : (
                                    <XCircle size={14} style={{ color: 'var(--text-muted)' }} />
                                )}
                            </h4>
                            <p>{ch.description}</p>
                        </div>
                    </div>
                ))}
            </div>

            <div className="card" style={{ marginTop: 24 }}>
                <div className="card-title"><Bell size={16} /> {t('notifications.configGuide')}</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                    <p style={{ marginBottom: 12 }}>
                        {t('notifications.configDesc')}{' '}
                        <code style={{
                            background: 'var(--bg-input)', padding: '2px 6px',
                            borderRadius: 4, fontFamily: 'var(--font-mono)', fontSize: '0.8rem'
                        }}>{t('notifications.configFile')}</code> {t('notifications.configFileSuffix')}
                    </p>
                    <div className="log-viewer" style={{ maxHeight: 200, marginTop: 8 }}>
                        <div className="log-line INFO"># Enable notifications globally</div>
                        <div className="log-line">ENABLE_NOTIFICATIONS=true</div>
                        <div className="log-line"></div>
                        <div className="log-line INFO"># Email (SMTP)</div>
                        <div className="log-line">SMTP_SERVER=smtp.gmail.com</div>
                        <div className="log-line">SMTP_PORT=587</div>
                        <div className="log-line">SMTP_USER=your_email@gmail.com</div>
                        <div className="log-line">SMTP_PASSWORD=your_app_password</div>
                        <div className="log-line"></div>
                        <div className="log-line INFO"># Slack</div>
                        <div className="log-line">SLACK_WEBHOOK_URL=https://hooks.slack.com/...</div>
                    </div>
                </div>
            </div>
        </>
    );
}
