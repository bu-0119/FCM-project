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

  login() {
    const app = this;
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (!res.code) { reject(new Error('wx.login fail')); return; }
          wx.request({
            url: app.globalData.baseURL + '/auth/wechat-login',
            method: 'POST',
            data: { code: res.code, nickname: '', avatar_url: '' },
            header: { 'Content-Type': 'application/json' },
            success: (resp) => {
              if (resp.statusCode === 200) {
                app.globalData.token = resp.data.access_token;
                app.globalData.userId = resp.data.user_id;
                wx.setStorageSync('token', resp.data.access_token);
                wx.setStorageSync('userId', resp.data.user_id);
                resolve(resp.data);
              } else {
                reject(resp.data);
              }
            },
            fail: reject,
          });
        },
        fail: reject,
      });
    });
  },

  request(path, method = 'GET', data = null) {
    const that = this;
    return new Promise((resolve, reject) => {
      const header = { 'Content-Type': 'application/json' };
      if (that.globalData.token) {
        header['Authorization'] = `Bearer ${that.globalData.token}`;
      }
      wx.request({
        url: that.globalData.baseURL + path,
        method,
        data,
        header,
        success: (res) => {
          if (res.statusCode === 200 || res.statusCode === 201) {
            resolve(res.data);
          } else if (res.statusCode === 401) {
            wx.removeStorageSync('token');
            that.globalData.token = null;
            reject({ code: 401, detail: '未登录' });
          } else {
            reject(res.data || { detail: '请求失败' });
          }
        },
        fail: reject,
      });
    });
  },
});
