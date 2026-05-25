App({
  globalData: {
    userInfo: null,
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

  login(nickname, avatarUrl) {
    return new Promise((resolve, reject) => {
      wx.login({
        success: async (res) => {
          try {
            const resp = await this.request('/auth/wechat-login', 'POST', {
              code: res.code,
              nickname: nickname || '',
              avatar_url: avatarUrl || '',
            }, true);
            this.globalData.token = resp.access_token;
            this.globalData.userId = resp.user_id;
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
