const BASE = '/api';

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  return res.json();
}

export const api = {
  health:          ()          => req('/health'),
  chat:            (message)   => req('/chat', { method: 'POST', body: JSON.stringify({ message }) }),

  getContributors: ()          => req('/contributors'),
  addContributor:  (data)      => req('/contributors', { method: 'POST', body: JSON.stringify(data) }),

  getStreams:      ()          => req('/streams'),
  createStream:    (data)      => req('/streams', { method: 'POST', body: JSON.stringify(data) }),
  cancelStream:    (id)        => req(`/streams/${id}/cancel`, { method: 'POST' }),

  getPolicy:       ()          => req('/policy'),
  updatePolicy:    (data)      => req('/policy', { method: 'PUT', body: JSON.stringify(data) }),
  pause:           ()          => req('/policy/pause', { method: 'POST' }),
  resume:          ()          => req('/policy/resume', { method: 'POST' }),

  getAudit:        (limit=40)  => req(`/audit?limit=${limit}`),
  getAuditSummary: ()          => req('/audit/summary'),

  // Autonomous loop
  getAutonomous:   ()          => req('/autonomous/status'),
  enableAuto:      ()          => req('/autonomous/enable', { method: 'POST' }),
  disableAuto:     ()          => req('/autonomous/disable', { method: 'POST' }),
  triggerTick:     ()          => req('/autonomous/trigger', { method: 'POST' }),
};
