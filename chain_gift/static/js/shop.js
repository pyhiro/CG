// 数値を通貨書式「#,###,###」に変換するフィルター
Vue.filter('number_format', function(val) {
    return val.toLocaleString();
  });
var app = new Vue({
    delimiters: ['[[',']]'],
    el: '#app',
    data: {
        //「並び替え」の選択値（1：標準、2：ポイントが低い順)
        sortOrder: 1,
        // 商品リスト
        products: [],
        // エラーの有無
        isError: false,
        // メッセージ
        message: '',
    },
    created: function() {
        // JSONPのURL（サーバーに配置する）
        var url = '/goods_db';
        // 非同期通信でJSONPを読み込む
        $.ajax({
          url : url,                // 通信先URL
          type: 'GET',              // 使用するHTTPメソッド
          dataType: 'json',        // レスポンスのデータタイプ
        })
        .done(function(data, textStatus, jqXHR) {
          this.products = data;
          alert('接続しました');
        }.bind(this))
        .fail(function(jqXHR, textStatus, errorThrown) {
          this.isError = true;
          this.message = '商品リストの読み込みに失敗しました。';
          alert('接続失敗')
        }.bind(this));
    },
    methods: {
      allList: function() {
        return this.products;
      },
      stampList: function() {
        var newList = [];
        for (var i=0; i < this.products.length; i++) {
          var isShow = true;
          //カテゴリーがスタンプかどうかの判定
          if (this.products[i].goods_category !== 'stamp'){
            this.products[i].goods_show = true;//この商品を表示させない
            isShow = false;
          }
          //表示対象の商品だけを新しい配列に追加する
          if(isShow) {
            newList.push(this.products[i]);
          }
        }
        //絞り込み後の商品リストを返す
        return newList;
      },
      bookList: function() {

      },
      stationeryList: function() {

      },
      Shoplist: function() {

      }
    }
});
