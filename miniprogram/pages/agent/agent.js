const api = require('../../utils/api');

Page({
  data: {
    chatMessages: [],
    inputText: '',
    sessionId: null,
    streaming: false,
    sceneLabel: '',
  },

  onLoad() {
    wx.getStorage({ key: 'sessionId', success: (r) => this.setData({ sessionId: r.data }) });
    this.checkScene();
  },

  checkScene() {
    const now = new Date();
    const month = now.getMonth() + 1;
    if (month >= 6 && month <= 8) {
      this.setData({ sceneLabel: '🔥 转会窗口期' });
    } else if (month === 1) {
      this.setData({ sceneLabel: '🔥 冬季转会窗' });
    }
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value });
  },

  quickPrompt(e) {
    this.setData({ inputText: e.currentTarget.dataset.text });
    this.sendMessage();
  },

  async sendMessage() {
    const text = this.data.inputText.trim();
    if (!text || this.data.streaming) return;

    const msgId = Date.now();
    const userMsg = { id: msgId, role: 'user', content: text };
    const botMsg = { id: msgId + 1, role: 'bot', content: '', typing: true };

    this.setData({
      chatMessages: [...this.data.chatMessages, userMsg, botMsg],
      inputText: '',
      streaming: true,
    });

    try {
      const res = await api.agentChat(text, this.data.sessionId);
      // Process SSE-like response
      let fullText = '';
      const botMsgId = msgId + 1;

      // The backend returns JSON, not true SSE in wx.request. Parse accordingly.
      if (typeof res === 'string') {
        fullText = res;
      } else if (res && res.data) {
        fullText = res.data;
      } else if (res && res.type === 'text') {
        fullText = res.data || '';
      }

      // For now, handle the response as-is
      if (res) {
        this.updateBotMsg(botMsgId, fullText || '抱歉，我现在无法回答这个问题。');
        if (res.session_id || (res.data && res.data.session_id)) {
          const sid = res.session_id || res.data.session_id;
          this.setData({ sessionId: sid });
          wx.setStorage({ key: 'sessionId', data: sid });
        }
      }
    } catch (e) {
      this.updateBotMsg(msgId + 1, '网络错误，请稍后重试');
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
    this.setData({ chatMessages: msgs });
  },

  scrollToBottom() {
    this.setData({ scrollTop: 99999 });
  },
});
