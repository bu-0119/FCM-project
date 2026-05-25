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
    try {
      const profile = await api.getProfile();
      this.setData({
        profile,
        notifySettings: profile.notify_settings || {},
      });
      const teams = await api.getMyTeams();
      this.setData({ myTeams: teams });
    } catch (e) {
      // Fallback: try login
      try {
        const app = getApp();
        await app.login();
        const profile = await api.getProfile();
        this.setData({
          profile,
          userId: wx.getStorageSync('userId') || '',
          notifySettings: profile.notify_settings || {},
        });
        const teams = await api.getMyTeams();
        this.setData({ myTeams: teams });
      } catch (e2) {
        console.log('Not logged in');
      }
    }
  },

  async handleLogin() {
    const app = getApp();
    try {
      await app.login();
      wx.showToast({ title: '登录成功', icon: 'success' });
      this.loadProfile();
    } catch (e) {
      wx.showToast({ title: '登录失败', icon: 'error' });
    }
  },

  onReminderChange(e) {
    const values = [0, 15, 30, 60, 120];
    const value = values[parseInt(e.detail.value)];
    api.updateNotifySettings({ match_reminder: value }).then(() => {
      this.setData({ 'notifySettings.match_reminder': value });
      wx.showToast({ title: '已保存', icon: 'success' });
    });
  },

  onSummaryChange(e) {
    const value = this.data.summaryTimeOptions[parseInt(e.detail.value)];
    api.updateNotifySettings({ daily_summary: value === '关闭' ? null : value }).then(() => {
      this.setData({ 'notifySettings.daily_summary': value });
      wx.showToast({ title: '已保存', icon: 'success' });
    });
  },
});
