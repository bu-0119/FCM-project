const api = require('../../utils/api');

Page({
  data: { team: {}, feed: [] },

  onLoad(options) {
    if (options.id) {
      api.getTeam(options.id).then(team => this.setData({ team }));
      api.getFeed({ team_id: options.id, size: 10 }).then(res => this.setData({ feed: res.items }));
    }
  },
});
