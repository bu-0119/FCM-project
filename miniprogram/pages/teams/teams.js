const api = require('../../utils/api');

var ut = {
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
    activeLeague: '西甲',
    activeTeams: [],
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

      // Group by league_name
      const leagueMap = {};
      teams.forEach(t => {
        const ln = t.league_name || '其他联赛';
        if (!leagueMap[ln]) leagueMap[ln] = [];
        leagueMap[ln].push(t);
      });

      // Build league list, 西甲 first, then 英超 etc.
      const leagueOrder = ['西甲', '英超', '德甲', '意甲', '法甲', '欧冠'];
      const leagueList = [];
      leagueOrder.forEach(name => {
        if (leagueMap[name] && leagueMap[name].length > 0) {
          leagueList.push({ name: name, teams: leagueMap[name] });
          delete leagueMap[name];
        }
      });
      // Remaining leagues
      Object.keys(leagueMap).forEach(name => {
        leagueList.push({ name: name, teams: leagueMap[name] });
      });

      this.setData({ leagues: leagueList });
      this.setActiveTeams(leagueList);

      // Load already selected teams
      const app = getApp();
      if (app.globalData.token) {
        try {
          const myTeams = await api.getMyTeams();
          const ids = myTeams.map(t => t.id);
          const names = myTeams.map(t => ({ id: t.id, name: t.name, crest: t.crest_url }));
          this.setData({ selectedIds: ids, selectedNames: names });
        } catch (e) {}
      }
    } catch (e) {
      console.error('Load teams failed:', e);
    } finally {
      this.setData({ loading: false });
    }
  },

  setActiveTeams(leagues) {
    const active = this.data.activeLeague || '西甲';
    const league = leagues.find(l => l.name === active);
    this.setData({ activeTeams: league ? league.teams : [] });
  },

  switchLeague(e) {
    const league = e.currentTarget.dataset.league;
    this.setData({ activeLeague: league });
    this.setActiveTeams(this.data.leagues);
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
      if (team) selectedNames.push({ id: team.id, name: team.name, crest: team.crest_url });
    }
    this.setData({ selectedIds: selected, selectedNames: selectedNames });
  },

  async saveTeams() {
    const app = getApp();
    if (!app.globalData.token) {
      wx.showLoading({ title: '请先登录...' });
      try { await app.login(); } catch (e) {}
      wx.hideLoading();
      if (!app.globalData.token) {
        wx.showToast({ title: '请先登录', icon: 'none' });
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
      wx.showToast({ title: '保存失败，请重试', icon: 'none' });
    }
  },
});
