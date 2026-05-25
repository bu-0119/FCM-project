const api = require('../../utils/api');

Page({
  data: {
    posts: [],
    postText: '',
    teamList: [],
    selectedTeam: null,
    selectedTeamIdx: -1,
    loading: false,
  },

  onShow() {
    this.loadPosts();
    this.loadTeams();
  },

  async loadPosts() {
    this.setData({ loading: true });
    try {
      const res = await api.getPosts({ sort: 'latest', page: 1, size: 20 });
      this.setData({ posts: res.items });
    } catch (e) {
      console.error('Load posts failed', e);
    } finally {
      this.setData({ loading: false });
    }
  },

  async loadTeams() {
    try {
      const teams = await api.getTeams();
      this.setData({ teamList: teams });
    } catch (e) {
      // teams not critical
    }
  },

  onTextInput(e) {
    this.setData({ postText: e.detail.value });
  },

  onTeamChange(e) {
    const idx = parseInt(e.detail.value);
    this.setData({
      selectedTeam: this.data.teamList[idx],
      selectedTeamIdx: idx,
    });
  },

  async publishPost() {
    if (!this.data.postText.trim() || !this.data.selectedTeam) return;
    try {
      await api.createPost({
        team_id: this.data.selectedTeam.id,
        content: this.data.postText.trim(),
        images: [],
      });
      wx.showToast({ title: '发布成功', icon: 'success' });
      this.setData({ postText: '' });
      this.loadPosts();
    } catch (e) {
      wx.showToast({ title: '发布失败', icon: 'error' });
    }
  },

  async likePost(e) {
    const postId = e.currentTarget.dataset.id;
    try {
      const res = await api.likePost(postId);
      const posts = this.data.posts.map(p => {
        if (p.id === postId) {
          return { ...p, like_count: res.count };
        }
        return p;
      });
      this.setData({ posts });
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'error' });
    }
  },

  showComments(e) {
    const postId = e.currentTarget.dataset.id;
    wx.showModal({
      title: '评论',
      editable: true,
      placeholderText: '写下你的评论...',
      success: async (res) => {
        if (res.confirm && res.content) {
          try {
            await api.createComment(postId, res.content);
            wx.showToast({ title: '评论成功', icon: 'success' });
          } catch (e) {
            wx.showToast({ title: '评论失败', icon: 'error' });
          }
        }
      },
    });
  },
});
