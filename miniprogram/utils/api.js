// 不能在这里 getApp() —— 模块加载时 App 还没初始化
// 每个方法内用 getApp_() 懒加载
function getApp_() {
  return getApp();
}

const api = {
  // Auth
  login(code, nickname, avatarUrl) {
    return getApp_().request('/auth/wechat-login', 'POST', {
      code, nickname, avatar_url: avatarUrl,
    });
  },

  // Teams
  getTeams() {
    return getApp_().request('/teams');
  },

  getTeam(id) {
    return getApp_().request('/teams/' + id);
  },

  // User
  getProfile() {
    return getApp_().request('/users/me');
  },

  updateProfile(data) {
    return getApp_().request('/users/me', 'PUT', data);
  },

  getMyTeams() {
    return getApp_().request('/users/me/teams');
  },

  updateMyTeams(teamIds) {
    return getApp_().request('/users/me/teams', 'PUT', { team_ids: teamIds });
  },

  // Content
  getFeed(params) {
    params = params || {};
    var parts = [];
    if (params.type) parts.push('type=' + params.type);
    if (params.team_id) parts.push('team_id=' + params.team_id);
    parts.push('page=' + (params.page || 1));
    parts.push('size=' + (params.size || 20));
    return getApp_().request('/content/feed?' + parts.join('&'));
  },

  searchContent(q, teamId) {
    return getApp_().request('/content/search?q=' + encodeURIComponent(q) + '&team_id=' + teamId);
  },

  // Social
  getPosts(params) {
    params = params || {};
    return getApp_().request('/posts?sort=' + (params.sort || 'latest') + '&page=' + (params.page || 1) + '&size=20');
  },

  createPost(data) {
    return getApp_().request('/posts', 'POST', data);
  },

  deletePost(id) {
    return getApp_().request('/posts/' + id, 'DELETE');
  },

  likePost(id) {
    return getApp_().request('/posts/' + id + '/like', 'POST');
  },

  getComments(postId) {
    return getApp_().request('/posts/' + postId + '/comments');
  },

  createComment(postId, content) {
    return getApp_().request('/comments?post_id=' + postId, 'POST', { content });
  },

  // Agent
  agentChat(message, sessionId) {
    return getApp_().request('/agent/chat', 'POST', { message: message, session_id: sessionId || null });
  },

  // Notifications
  getNotifications(page) {
    return getApp_().request('/notifications?page=' + (page || 1));
  },

  updateNotifySettings(settings) {
    return getApp_().request('/notifications/settings', 'PUT', settings);
  },

  getNotifySettings() {
    return getApp_().request('/notifications/settings');
  },
};

module.exports = api;
