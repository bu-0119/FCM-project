const api = require('../../utils/api');

Page({
  data: {
    loggedIn: false,
    nickname: '',
    userId: '',
    myTeams: [],
    notifySettings: {},
    reminderOptions: ['关闭', '15分钟前', '30分钟前', '60分钟前', '2小时前'],
    summaryTimeOptions: ['关闭', '8:00', '9:00', '10:00', '12:00', '18:00', '20:00'],
  },

  onShow() {
    this.checkLoginState();
  },

  // 仅检查 token 是否存在，不做网络请求
  checkLoginState() {
    const app = getApp();
    if (app.globalData.token) {
      this.setData({ loggedIn: true, userId: app.globalData.userId || '' });
      this.loadProfile();
    } else {
      this.setData({ loggedIn: false, nickname: '', myTeams: [], notifySettings: {} });
    }
  },

  async loadProfile() {
    try {
      const profile = await api.getProfile();
      this.setData({
        nickname: profile.nickname || '微信用户',
        notifySettings: profile.notify_settings || {},
      });
      const teams = await api.getMyTeams();
      this.setData({ myTeams: teams });
    } catch (e) {
      console.log('loadProfile 失败:', e);
    }
  },

  async handleLogin() {
    const app = getApp();
    wx.showLoading({ title: '登录中...' });
    try {
      await app.login();
      wx.hideLoading();
      this.setData({ loggedIn: true, userId: app.globalData.userId });
      wx.showToast({ title: '登录成功', icon: 'success' });
      this.loadProfile();
    } catch (e) {
      wx.hideLoading();
      console.log('登录失败:', e);
      wx.showToast({ title: '登录失败，请重试', icon: 'none' });
    }
  },

  onReminderChange(e) {
    const values = [0, 15, 30, 60, 120];
    api.updateNotifySettings({ match_reminder: values[parseInt(e.detail.value)] })
      .then(s => this.setData({ notifySettings: s }))
      .catch(() => {});
  },

  onSummaryChange(e) {
    const val = this.data.summaryTimeOptions[parseInt(e.detail.value)];
    api.updateNotifySettings({ daily_summary: val === '关闭' ? null : val })
      .then(s => this.setData({ notifySettings: s }))
      .catch(() => {});
  },
});
