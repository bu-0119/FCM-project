const api = require('../../utils/api');

Page({
  data: {
    leagues: [],
    selectedIds: [],
    loading: false,
  },

  onLoad() {
    this.loadTeams();
  },

  async loadTeams() {
    this.setData({ loading: true });
    try {
      const teams = await api.getTeams();
      const leagueMap = {};
      teams.forEach(t => {
        const key = 'league_' + (t.league_id || 0);
        if (!leagueMap[key]) leagueMap[key] = { id: t.league_id, teams: [] };
        leagueMap[key].teams.push(t);
      });
      this.setData({ leagues: Object.values(leagueMap) });

      // 读取已选主队
      const app = getApp();
      if (app.globalData.token) {
        try {
          const myTeams = await api.getMyTeams();
          this.setData({ selectedIds: myTeams.map(t => t.id) });
        } catch (e) {}
      }
    } catch (e) {
      console.error('加载球队失败', e);
    } finally {
      this.setData({ loading: false });
    }
  },

  toggleTeam(e) {
    const id = e.currentTarget.dataset.id;
    let selected = [...this.data.selectedIds];
    const idx = selected.indexOf(id);
    if (idx >= 0) {
      selected.splice(idx, 1);
    } else if (selected.length >= 3) {
      wx.showToast({ title: '最多选择3支球队', icon: 'none' });
      return;
    } else {
      selected.push(id);
    }
    this.setData({ selectedIds: selected });
  },

  async saveTeams() {
    const app = getApp();

    // 未登录先登录
    if (!app.globalData.token) {
      wx.showLoading({ title: '请先登录...' });
      try {
        await app.login();
        wx.hideLoading();
      } catch (e) {
        wx.hideLoading();
        wx.showToast({ title: '登录失败，请先在「我的」页面登录', icon: 'none' });
        return;
      }
    }

    wx.showLoading({ title: '保存中...' });
    try {
      await api.updateMyTeams(this.data.selectedIds);
      wx.hideLoading();
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 1200);
    } catch (e) {
      wx.hideLoading();
      console.log('保存失败:', e);
      wx.showToast({ title: '保存失败: ' + (e.detail || '网络错误'), icon: 'none', duration: 2500 });
    }
  },
});
