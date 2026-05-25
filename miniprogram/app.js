App({
  globalData: {
    token: null,
    userId: null,
    baseURL: 'http://localhost:8000/api/v1',
  },

  onLaunch() {
    const token = wx.getStorageSync('token');
    const userId = wx.getStorageSync('userId');
    if (token) {
      this.globalData.token = token;
      this.globalData.userId = userId;
    }
  },

  // Step 1: 调用 wx.login 获取临时 code
  wxLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (res.code) {
            resolve(res.code);
          } else {
            reject(new Error('wx.login 失败'));
          }
        },
        fail: reject,
      });
    });
  },

  // Step 2: 获取微信用户信息（昵称+头像）
  getUserInfo() {
    return new Promise((resolve, reject) => {
      wx.getUserInfo({
        success: (res) => {
          resolve({
            nickname: res.userInfo.nickName,
            avatarUrl: res.userInfo.avatarUrl,
          });
        },
        fail: (err) => {
          // 用户拒绝授权, 使用默认值
          resolve({ nickname: '球迷' + Date.now().toString(36), avatarUrl: '' });
        },
      });
    });
  },

  // 完整登录流程: wx.login → getUserInfo → 后端注册/登录
  async login() {
    const code = await this.wxLogin();
    const userInfo = await this.getUserInfo();

    const resp = await this.request('/auth/wechat-login', 'POST', {
      code: code,
      nickname: userInfo.nickname,
      avatar_url: userInfo.avatarUrl,
    }, true);

    this.globalData.token = resp.access_token;
    this.globalData.userId = resp.user_id;
    wx.setStorageSync('token', resp.access_token);
    wx.setStorageSync('userId', resp.user_id);
    return resp;
  },

  request(path, method = 'GET', data = null, skipAuth = false) {
    return new Promise((resolve, reject) => {
      const header = { 'Content-Type': 'application/json' };
      if (this.globalData.token) {
        header['Authorization'] = `Bearer ${this.globalData.token}`;
      }
      wx.request({
        url: this.globalData.baseURL + path,
        method,
        data,
        header,
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data);
          } else if (res.statusCode === 401 && !skipAuth) {
            wx.removeStorageSync('token');
            this.globalData.token = null;
            reject({ code: 401, message: '请先登录' });
          } else {
            reject(res.data || { message: '请求失败' });
          }
        },
        fail: (err) => {
          reject({ message: '网络错误: ' + (err.errMsg || '') });
        },
      });
    });
  },
});
