const api = require('../../utils/api');

Page({
  data: {
    chatMessages: [],
    inputText: '',
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
    this.setData({ inputText: e.detail.value });
  },

  quickPrompt(e) {
    this.setData({ inputText: e.currentTarget.dataset.text });
    this.sendMessage();
  },

  scrollToBottom() {
    this.setData({ scrollTop: 99999 });
    // Also use scroll-into-view
    const len = this.data.chatMessages.length;
    if (len > 0) {
      this.setData({ lastMsgId: 'msg-' + this.data.chatMessages[len - 1].id });
    }
  },

  async sendMessage() {
    const text = this.data.inputText.trim();
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

    const newMessages = [...this.data.chatMessages, userMsg, botMsg];
    this.setData({
      chatMessages: newMessages,
      inputText: '',
      streaming: true,
      lastMsgId: 'msg-' + botMsg.id,
    });

    try {
      const res = await api.agentChat(text, this.data.sessionId);
      // res is { reply, session_id, intent, entities }
      this.updateBotMsg(msgId + 1, res.reply);
      if (res.session_id) {
        this.setData({ sessionId: res.session_id });
        wx.setStorageSync('sessionId', res.session_id);
      }
    } catch (e) {
      this.updateBotMsg(msgId + 1, '网络错误，请稍后重试\n' + JSON.stringify(e));
    } finally {
      this.setData({ streaming: false });
      this.scrollToBottom();
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
