const api = require('../../utils/api');

Page({
  data: {
    chatMessages: [],
    inputText: '',
    canSend: false,
    sessionId: null,
    streaming: false,
  },

  onLoad() {
    try {
      const sid = wx.getStorageSync('sessionId');
      if (sid) this.setData({ sessionId: sid });
    } catch (e) {}
  },

  onInput(e) {
    const val = e.detail.value;
    this.setData({
      inputText: val,
      canSend: val.trim().length > 0 && !this.data.streaming,
    });
  },

  quickPrompt(e) {
    const text = e.currentTarget.dataset.text;
    this.setData({ inputText: text, canSend: true });
    this.sendMessage();
  },

  async sendMessage() {
    const text = (this.data.inputText || '').trim();
    if (!text || this.data.streaming) return;

    const app = getApp();
    if (!app.globalData.token) {
      wx.showModal({
        title: '请先登录',
        content: '需要登录后才能使用AI助手',
        confirmText: '去登录',
        success: (res) => {
          if (res.confirm) wx.switchTab({ url: '/pages/profile/profile' });
        },
      });
      return;
    }

    const msgId = Date.now();
    const userMsg = { id: msgId, role: 'user', content: text };
    const botMsg = { id: msgId + 1, role: 'bot', content: '', typing: true };

    this.setData({
      chatMessages: [...this.data.chatMessages, userMsg, botMsg],
      inputText: '',
      canSend: false,
      streaming: true,
      lastMsgId: 'msg-' + botMsg.id,
    });

    try {
      const res = await api.agentChat(text, this.data.sessionId);
      this.updateBotMsg(msgId + 1, res.reply || '抱歉，我暂时无法回答这个问题。');
      if (res.session_id) {
        this.setData({ sessionId: res.session_id });
        wx.setStorageSync('sessionId', res.session_id);
      }
    } catch (e) {
      console.error('Agent chat error:', e);
      this.updateBotMsg(msgId + 1, '网络错误，请稍后重试');
    } finally {
      this.setData({ streaming: false, canSend: false });
    }
  },

  updateBotMsg(msgId, content) {
    const msgs = this.data.chatMessages.map(m => {
      if (m.id === msgId) return { ...m, content, typing: false };
      return m;
    });
    this.setData({ chatMessages: msgs, lastMsgId: 'msg-' + msgId });
  },
});
