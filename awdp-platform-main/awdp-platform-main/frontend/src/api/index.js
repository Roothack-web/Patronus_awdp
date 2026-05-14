const BASE = '/api';

async function request(path, options = {}) {
  const headers = { ...options.headers };
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers,
    ...options,
    body: options.body,
  });

  // Handle file downloads
  if (options.raw) return res;

  const data = await res.json();
  if (!data.ok) {
    const err = new Error(data.error || '请求失败');
    err.status = res.status;
    throw err;
  }
  return data.data;
}

export const api = {
  // Auth
  login: (username, password, remember) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password, remember }),
    }),
  logout: () =>
    request('/auth/logout', { method: 'POST' }),
  register: (name, password) =>
    request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, password }),
    }),
  me: () => request('/auth/me'),

  // Challenges
  challenges: () => request('/challenges'),
  challengeDetail: (id) => request(`/challenges/${id}`),
  submitFlag: (challengeId, flag) =>
    request(`/challenges/${challengeId}/flag`, {
      method: 'POST',
      body: JSON.stringify({ flag }),
    }),
  downloadSource: (challengeId) =>
    request(`/challenges/${challengeId}/source`, { raw: true }),

  // Containers
  startContainer: (challengeId) =>
    request(`/containers/${challengeId}/start`, { method: 'POST' }),
  stopContainer: (challengeId) =>
    request(`/containers/${challengeId}/stop`, { method: 'POST' }),
  resetContainer: (challengeId) =>
    request(`/containers/${challengeId}/reset`, { method: 'POST' }),
  refreshFlag: (challengeId) =>
    request(`/containers/${challengeId}/refresh-flag`, { method: 'POST' }),

  // Defenses
  getDefenseUpload: (challengeId) => request(`/defenses/${challengeId}/upload`),
  uploadDefense: (challengeId, formData) =>
    request(`/defenses/${challengeId}/upload`, {
      method: 'POST',
      body: formData,
    }),

  // Contests
  contests: () => request('/contests'),
  contestDetail: (id) => request(`/contests/${id}`),

  // Leaderboard
  leaderboard: (contestId) =>
    request(`/leaderboard${contestId ? `?contest_id=${contestId}` : ''}`),
};
