const app = getApp();

const api = {
  // Auth
  login(code, nickname, avatarUrl) {
    return app.request('/auth/wechat-login', 'POST', {
      code, nickname, avatar_url: avatarUrl,
    });
  },

  // Teams
  getTeams() {
    return app.request('/teams');
  },

  getTeam(id) {
    return app.request(`/teams/${id}`);
  },

  // User
  getProfile() {
    return app.request('/users/me');
  },

  updateProfile(data) {
    return app.request('/users/me', 'PUT', data);
  },

  getMyTeams() {
    return app.request('/users/me/teams');
  },

  updateMyTeams(teamIds) {
    return app.request('/users/me/teams', 'PUT', { team_ids: teamIds });
  },

  // Content
  getFeed(params = {}) {
    const query = Object.entries(params)
      .filter(([_, v]) => v != null)
      .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
      .join('&');
    return app.request(`/content/feed?${query}`);
  },

  searchContent(q, teamId) {
    return app.request(`/content/search?q=${encodeURIComponent(q)}&team_id=${teamId}`);
  },

  // Social
  getPosts(params = {}) {
    const query = Object.entries(params)
      .filter(([_, v]) => v != null)
      .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
      .join('&');
    return app.request(`/posts?${query}`);
  },

  createPost(data) {
    return app.request('/posts', 'POST', data);
  },

  deletePost(id) {
    return app.request(`/posts/${id}`, 'DELETE');
  },

  likePost(id) {
    return app.request(`/posts/${id}/like`, 'POST');
  },

  getComments(postId) {
    return app.request(`/posts/${postId}/comments`);
  },

  createComment(postId, content) {
    return app.request(`/comments?post_id=${postId}`, 'POST', { content });
  },

  // Agent
  agentChat(message, sessionId) {
    return app.request('/agent/chat', 'POST', { message, session_id: sessionId });
  },

  // Notifications
  getNotifications(page = 1) {
    return app.request(`/notifications?page=${page}`);
  },

  updateNotifySettings(settings) {
    return app.request('/notifications/settings', 'PUT', settings);
  },

  getNotifySettings() {
    return app.request('/notifications/settings');
  },
};

module.exports = api;
