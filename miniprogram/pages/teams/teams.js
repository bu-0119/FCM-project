const api = require('../../utils/api');

Page({
  data: {
    leagues: [],
    selectedIds: [],
    allTeams: [],
  },

  onLoad() {
    this.loadTeams();
  },

  async loadTeams() {
    try {
      const teams = await api.getTeams();
      this.setData({ allTeams: teams });
      // Group by league
      const leagueMap = {};
      teams.forEach(t => {
        const leagueName = `联赛 ${t.league_id || '其他'}`;
        if (!leagueMap[leagueName]) {
          leagueMap[leagueName] = { name: leagueName, name_en: '', id: t.league_id, teams: [] };
        }
        leagueMap[leagueName].teams.push(t);
      });
      this.setData({ leagues: Object.values(leagueMap) });

      // Load existing selections
      try {
        const myTeams = await api.getMyTeams();
        this.setData({ selectedIds: myTeams.map(t => t.id) });
      } catch (e) {
        // Not logged in
      }
    } catch (e) {
      console.error('Load teams failed', e);
    }
  },

  toggleTeam(e) {
    const id = e.currentTarget.dataset.id;
    let selected = [...this.data.selectedIds];
    const idx = selected.indexOf(id);
    if (idx >= 0) {
      selected.splice(idx, 1);
    } else if (selected.length < 3) {
      selected.push(id);
    } else {
      wx.showToast({ title: '最多选择3支球队', icon: 'none' });
      return;
    }
    this.setData({ selectedIds: selected });
  },

  async saveTeams() {
    try {
      await api.updateMyTeams(this.data.selectedIds);
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 1500);
    } catch (e) {
      // Try login then retry
      const app = getApp();
      await app.login();
      await api.updateMyTeams(this.data.selectedIds);
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 1500);
    }
  },

  utils: {
    isSelected(selectedIds, id) {
      return selectedIds.includes(id);
    },
  },
});
