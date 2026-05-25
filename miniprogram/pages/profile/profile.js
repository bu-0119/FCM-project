const api = require('../../utils/api');

Page({
  data: {
    profile: null,
    userId: '',
    myTeams: [],
    notifySettings: {},
    loggedIn: false,
    reminderOptions: ['关闭', '15分钟前', '30分钟前', '60分钟前', '2小时前'],
    summaryTimeOptions: ['关闭', '8:00', '9:00', '10:00', '12:00', '18:00', '20:00'],
  },

  onShow() {
    this.loadProfile();
  },

  async loadProfile() {
    const app = getApp();
    if (!app.globalData.token) {
      this.setData({ loggedIn: false, profile: null, myTeams: [] });
      return;
    }
    try {
      const profile = await api.getProfile();
      const teams = await api.getMyTeams();
      this.setData({
        loggedIn: true,
        profile,
        userId: app.globalData.userId || profile.id || '',
        myTeams: teams,
        notifySettings: profile.notify_settings || {},
      });
    } catch (e) {
      console.error('loadProfile error:', e);
      this.setData({ loggedIn: false, profile: null, myTeams: [] });
    }
  },

  async handleLogin() {
    const app = getApp();
    wx.showLoading({ title: '登录中...' });
    try {
      await app.login('球迷' + Date.now().toString(36), '');
      wx.hideLoading();
      wx.showToast({ title: '登录成功', icon: 'success', duration: 1500 });
      // Reload profile after toast
      setTimeout(() => { this.loadProfile(); }, 500);
    } catch (e) {
      wx.hideLoading();
      console.error('Login error:', e);
      wx.showToast({ title: '登录失败: ' + (e.message || '网络错误'), icon: 'none', duration: 2000 });
    }
  },

  onReminderChange(e) {
    if (!this.data.loggedIn) return;
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
    if (!this.data.loggedIn) return;
    const value = this.data.summaryTimeOptions[parseInt(e.detail.value)];
    const payload = value === '关闭' ? { daily_summary: null } : { daily_summary: value };
    api.updateNotifySettings(payload).then(() => {
      this.setData({ 'notifySettings.daily_summary': value });
      wx.showToast({ title: '已保存', icon: 'success' });
    }).catch(() => {
      wx.showToast({ title: '保存失败', icon: 'none' });
    });
  },
});
