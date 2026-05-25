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
    console.log('loadProfile: token=', !!app.globalData.token);
    if (!app.globalData.token) {
      this.setData({ loggedIn: false, profile: null, myTeams: [] });
      return;
    }
    try {
      const profile = await api.getProfile();
      console.log('getProfile success:', profile);
      const teams = await api.getMyTeams();
      console.log('getMyTeams success:', teams);
      this.setData({
        loggedIn: true,
        profile,
        userId: app.globalData.userId || profile.id || '',
        myTeams: teams,
        notifySettings: profile.notify_settings || {},
      });
    } catch (e) {
      console.error('loadProfile failed:', JSON.stringify(e));
      wx.removeStorageSync('token');
      getApp().globalData.token = null;
      this.setData({ loggedIn: false, profile: null, myTeams: [] });
    }
  },

  async handleLogin() {
    const app = getApp();
    wx.showLoading({ title: '微信登录中...' });
    try {
      const resp = await app.login();
      console.log('login resp:', JSON.stringify(resp));
      console.log('token now:', !!app.globalData.token);
      wx.hideLoading();
      wx.showToast({ title: '登录成功', icon: 'success', duration: 1000 });
      // 直接刷新，不用 setTimeout
      await this.loadProfile();
    } catch (e) {
      wx.hideLoading();
      console.error('Login error:', JSON.stringify(e));
      wx.showToast({ title: '登录失败，请重试', icon: 'none' });
    }
  },

  onReminderChange(e) {
    if (!this.data.loggedIn) return;
    const values = [0, 15, 30, 60, 120];
    const value = values[parseInt(e.detail.value)];
    api.updateNotifySettings({ match_reminder: value }).then(() => {
      this.setData({ 'notifySettings.match_reminder': value });
    }).catch(() => {});
  },

  onSummaryChange(e) {
    if (!this.data.loggedIn) return;
    const value = this.data.summaryTimeOptions[parseInt(e.detail.value)];
    const payload = value === '关闭' ? { daily_summary: null } : { daily_summary: value };
    api.updateNotifySettings(payload).then(() => {
      this.setData({ 'notifySettings.daily_summary': value });
    }).catch(() => {});
  },
});
