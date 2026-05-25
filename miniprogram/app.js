App({
  globalData: {
    userInfo: null,
    token: null,
    baseURL: 'http://localhost:8000/api/v1', // 本地开发
  },

  onLaunch() {
    this.checkLogin();
  },

  checkLogin() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
    }
  },

  async login() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: async (res) => {
          try {
            const resp = await this.request('/auth/wechat-login', 'POST', {
              code: res.code,
              nickname: '',
              avatar_url: '',
            });
            this.globalData.token = resp.access_token;
            wx.setStorageSync('token', resp.access_token);
            wx.setStorageSync('userId', resp.user_id);
            resolve(resp);
          } catch (e) {
            reject(e);
          }
        },
        fail: reject,
      });
    });
  },

  request(path, method = 'GET', data = null) {
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
          } else if (res.statusCode === 401) {
            wx.removeStorageSync('token');
            this.globalData.token = null;
            this.login().then(() => resolve(this.request(path, method, data)));
          } else {
            reject(res.data);
          }
        },
        fail: reject,
      });
    });
  },
});
