import { createContext, useContext, useState, useCallback } from 'react';
import en from './en.json';
import es from './es.json';

const translations = { en, es };
const STORAGE_KEY = 'datrix-lang';

const LanguageContext = createContext();

function getNestedValue(obj, path) {
    return path.split('.').reduce((acc, key) => acc?.[key], obj);
}

export function LanguageProvider({ children }) {
    const [lang, setLangState] = useState(() => {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            return saved === 'es' ? 'es' : 'en';
        } catch {
            return 'en';
        }
    });

    const setLang = useCallback((newLang) => {
        const l = newLang === 'es' ? 'es' : 'en';
        setLangState(l);
        try { localStorage.setItem(STORAGE_KEY, l); } catch { /* ignore */ }
    }, []);

    const t = useCallback((key, replacements) => {
        let value = getNestedValue(translations[lang], key) ?? key;
        if (replacements && typeof value === 'string') {
            Object.entries(replacements).forEach(([k, v]) => {
                value = value.replace(`{${k}}`, v);
            });
        }
        return value;
    }, [lang]);

    return (
        <LanguageContext.Provider value={{ lang, setLang, t }}>
            {children}
        </LanguageContext.Provider>
    );
}

export function useTranslation() {
    const ctx = useContext(LanguageContext);
    if (!ctx) throw new Error('useTranslation must be used within LanguageProvider');
    return ctx;
}
