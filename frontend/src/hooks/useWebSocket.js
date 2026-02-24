import { useState, useEffect, useRef, useCallback } from 'react';

export function useWebSocket(runId) {
    const [logs, setLogs] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef(null);
    const logsEndRef = useRef(null);

    const connect = useCallback((id) => {
        if (wsRef.current) {
            wsRef.current.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/logs/${id}`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            setLogs(prev => [...prev, { text: '● Connected to pipeline log stream', level: 'SUCCESS' }]);
        };

        ws.onmessage = (event) => {
            const text = event.data;
            let level = 'INFO';
            if (text.includes('ERROR')) level = 'ERROR';
            else if (text.includes('WARNING')) level = 'WARNING';
            else if (text.includes('COMPLETED SUCCESSFULLY')) level = 'SUCCESS';

            setLogs(prev => [...prev, { text, level }]);
        };

        ws.onclose = () => {
            setIsConnected(false);
            setLogs(prev => [...prev, { text: '● Disconnected from log stream', level: 'INFO' }]);
        };

        ws.onerror = () => {
            setIsConnected(false);
        };
    }, []);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, []);

    const clearLogs = useCallback(() => {
        setLogs([]);
    }, []);

    useEffect(() => {
        if (runId) {
            connect(runId);
        }
        return () => disconnect();
    }, [runId, connect, disconnect]);

    return { logs, isConnected, connect, disconnect, clearLogs, logsEndRef };
}
