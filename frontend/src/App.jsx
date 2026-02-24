import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import {
    LayoutDashboard, Database, AlertTriangle,
    History, BarChart3, Zap, Globe
} from 'lucide-react';
import { useTranslation } from './i18n/LanguageContext';
import Dashboard from './pages/Dashboard';
import DataExplorer from './pages/DataExplorer';
import Quarantine from './pages/Quarantine';
import HistoryPage from './pages/History';
import Analytics from './pages/Analytics';

function App() {
    const location = useLocation();
    const { t, lang, setLang } = useTranslation();

    const navItems = [
        { path: '/', labelKey: 'sidebar.dashboard', icon: LayoutDashboard, section: 'main' },
        { path: '/data', labelKey: 'sidebar.dataExplorer', icon: Database, section: 'main' },
        { path: '/quarantine', labelKey: 'sidebar.quarantine', icon: AlertTriangle, section: 'monitor' },
        { path: '/history', labelKey: 'sidebar.runHistory', icon: History, section: 'monitor' },
        { path: '/analytics', labelKey: 'sidebar.analytics', icon: BarChart3, section: 'insights' },
    ];

    const sections = {
        main: t('sidebar.pipeline'),
        monitor: t('sidebar.monitoring'),
        insights: t('sidebar.insights'),
    };

    const groupedItems = {};
    navItems.forEach(item => {
        if (!groupedItems[item.section]) groupedItems[item.section] = [];
        groupedItems[item.section].push(item);
    });

    return (
        <div className="app-layout">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-logo">
                    <div className="logo-icon">
                        <Zap size={20} />
                    </div>
                    <div>
                        <h1>Datrix</h1>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    {Object.entries(groupedItems).map(([section, items]) => (
                        <div key={section}>
                            <div className="sidebar-section-label">{sections[section]}</div>
                            {items.map(item => (
                                <NavLink
                                    key={item.path}
                                    to={item.path}
                                    end={item.path === '/'}
                                    className={({ isActive }) =>
                                        `nav-link ${isActive ? 'active' : ''}`
                                    }
                                >
                                    <item.icon className="nav-icon" size={20} />
                                    {t(item.labelKey)}
                                </NavLink>
                            ))}
                        </div>
                    ))}
                </nav>

                <div className="sidebar-footer">
                    <div
                        className="lang-toggle"
                        onClick={() => setLang(lang === 'en' ? 'es' : 'en')}
                        title="Switch language"
                    >
                        <Globe size={14} />
                        <span className={`lang-option ${lang === 'en' ? 'active' : ''}`}>EN</span>
                        <span className="lang-divider">/</span>
                        <span className={`lang-option ${lang === 'es' ? 'active' : ''}`}>ES</span>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                <div className="animate-in" key={location.pathname}>
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/data" element={<DataExplorer />} />
                        <Route path="/quarantine" element={<Quarantine />} />
                        <Route path="/history" element={<HistoryPage />} />
                        <Route path="/analytics" element={<Analytics />} />
                    </Routes>
                </div>
            </main>
        </div>
    );
}

export default App;
