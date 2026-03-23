import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import Landing from './Landing';
import './index.css';

function Root() {
  const [page, setPage] = useState(() => {
    return window.location.hash === '#dashboard' ? 'dashboard' : 'landing';
  });

  useEffect(() => {
    const onHash = () => setPage(window.location.hash === '#dashboard' ? 'dashboard' : 'landing');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const goToDashboard = () => {
    window.location.hash = '#dashboard';
    setPage('dashboard');
  };

  const goToLanding = () => {
    window.location.hash = '';
    setPage('landing');
  };

  if (page === 'dashboard') return <App onBack={goToLanding} />;
  return <Landing onEnter={goToDashboard} />;
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
