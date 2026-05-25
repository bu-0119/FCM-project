const api = require('../../utils/api');

Page({
  data: {
    profile: {},
    userId: '',
    myTeams: [],
    notifySettings: {},
    reminderOptions: ['关闭', '15分钟前', '30分钟前', '60分钟前', '2小时前'],
    summaryTimeOptions: ['关闭', '8:00', '9:00', '10:00', '12:00', '18:00', '20:00'],
  },

  onShow() {
    this.loadProfile();
  },

  async loadProfile() {
    const app = getApp();
    if (!app.globalData.token) {
      this.setData({ profile: {}, userId: '', myTeams: [] });
      return;
    }
    try {
      const profile = await api.getProfile();
      this.setData({
        profile,
        userId: app.globalData.userId || '',
        notifySettings: profile.notify_settings || {},
      });
      const teams = await api.getMyTeams();
      this.setData({ myTeams: teams });
    } catch (e) {
      console.log('加载用户信息失败', e);
      this.setData({ profile: {}, myTeams: [] });
    }
  },

  async handleLogin() {
    const app = getApp();
    wx.showLoading({ title: '登录中...' });
    try {
      const resp = await app.login('球迷' + Date.now().toString(36), '');
      wx.hideLoading();
      wx.showToast({ title: '登录成功', icon: 'success' });
      this.loadProfile();
    } catch (e) {
      wx.hideLoading();
      wx.showToast({ title: '登录失败', icon: 'error' });
    }
  },

  onReminderChange(e) {
    const values = [0, 15, 30, 60, 120];
    const value = values[parseInt(e.detail.value)];
    api.updateNotifySettings({ match_reminder: value }).then(() => {
      this.setData({ 'notifySettings.match_reminder': value });
      wx.showToast({ title: '已保存', icon: 'success' });
    }).catch(() => {
      wx.showToast({ title: '保存失败', icon: 'none' });
    });
  },

  onSummaryChange(e) {
    const value = this.data.summaryTimeOptions[parseInt(e.detail.value)];
    api.updateNotifySettings({ daily_summary: value === '关闭' ? null : value }).then(() => {
      this.setData({ 'notifySettings.daily_summary': value });
      wx.showToast({ title: '已保存', icon: 'success' });
    }).catch(() => {
      wx.showToast({ title: '保存失败', icon: 'none' });
    });
  },
});
