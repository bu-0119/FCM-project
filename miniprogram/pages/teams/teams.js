const api = require('../../utils/api');

// WXS-compatible helper for template
const ut = {
  isPicked: function(arr, id) {
    if (!arr) return false;
    for (var i = 0; i < arr.length; i++) {
      if (arr[i] === id) return true;
    }
    return false;
  }
};

Page({
  data: {
    leagues: [],
    selectedIds: [],
    selectedNames: [],
    allTeams: [],
    loading: false,
    utils: ut,
  },

  onLoad() {
    this.loadTeams();
  },

  async loadTeams() {
    this.setData({ loading: true });
    try {
      const teams = await api.getTeams();
      this.setData({ allTeams: teams });
      const leagueMap = {};
      teams.forEach(t => {
        const key = 'league_' + (t.league_id || 0);
        if (!leagueMap[key]) leagueMap[key] = { id: t.league_id, name: '联赛', name_en: '', teams: [] };
        leagueMap[key].teams.push(t);
      });
      this.setData({ leagues: Object.values(leagueMap) });

      const app = getApp();
      if (app.globalData.token) {
        try {
          const myTeams = await api.getMyTeams();
          const ids = myTeams.map(t => t.id);
          const names = myTeams.map(t => ({ id: t.id, name: t.name }));
          this.setData({ selectedIds: ids, selectedNames: names });
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
    let selectedNames = [...this.data.selectedNames];
    const idx = selected.indexOf(id);

    if (idx >= 0) {
      selected.splice(idx, 1);
      selectedNames.splice(idx, 1);
    } else if (selected.length >= 3) {
      wx.showToast({ title: '最多选择3支球队', icon: 'none' });
      return;
    } else {
      selected.push(id);
      const team = this.data.allTeams.find(t => t.id === id);
      if (team) selectedNames.push({ id: team.id, name: team.name });
    }
    this.setData({ selectedIds: selected, selectedNames: selectedNames });
  },

  async saveTeams() {
    const app = getApp();

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
      wx.showToast({ title: '保存失败，请重试', icon: 'none', duration: 2000 });
    }
  },
});
