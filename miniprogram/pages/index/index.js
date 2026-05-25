const api = require('../../utils/api');

Page({
  data: {
    items: [],
    myTeams: [],
    activeType: '',
    activeTeamId: '',
    page: 1,
    size: 20,
    total: 0,
    loading: false,
    hasMore: true,
  },

  onLoad() {
    this.loadFeed();
  },

  onShow() {
    this.loadMyTeams();
  },

  onPullDownRefresh() {
    this.setData({ page: 1, items: [], hasMore: true });
    this.loadFeed().then(() => wx.stopPullDownRefresh());
  },

  onReachBottom() {
    this.loadMore();
  },

  async loadFeed() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    try {
      const params = { page: this.data.page, size: this.data.size };
      if (this.data.activeType) params.type = this.data.activeType;
      if (this.data.activeTeamId) params.team_id = this.data.activeTeamId;

      const res = await api.getFeed(params);
      this.setData({
        items: this.data.page === 1 ? res.items : [...this.data.items, ...res.items],
        total: res.total,
        hasMore: this.data.page * this.data.size < res.total,
      });
    } catch (e) {
      console.error('Load feed failed', e);
    } finally {
      this.setData({ loading: false });
    }
  },

  async loadMyTeams() {
    const app = getApp();
    if (!app.globalData.token) return;
    try {
      const teams = await api.getMyTeams();
      this.setData({ myTeams: teams });
    } catch (e) {
      // not logged in
    }
  },

  filterByType(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({ activeType: type, page: 1, items: [] });
    this.loadFeed();
  },

  filterByTeam(e) {
    const id = e.currentTarget.dataset.id;
    this.setData({ activeTeamId: id || '', page: 1, items: [] });
    this.loadFeed();
  },

  loadMore() {
    if (!this.data.hasMore || this.data.loading) return;
    this.setData({ page: this.data.page + 1 });
    this.loadFeed();
  },

  openDetail(e) {
    const item = e.currentTarget.dataset.item;
    if (item.source_url) {
      wx.setClipboardData({ data: item.source_url });
      wx.showToast({ title: '原文链接已复制', icon: 'none' });
    }
  },
});
