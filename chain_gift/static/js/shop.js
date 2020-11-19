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
        message: ''
    },
    created: function() {
        // JSONPのURL（サーバーに配置する）
        var url = 'goods_db/';
        // 非同期通信でJSONPを読み込む
        $.ajax({
          url : url,                // 通信先URL
          type: 'GET',              // 使用するHTTPメソッド
          dataType: 'jsonp',        // レスポンスのデータタイプ
          jsonp: 'callback',        // クエリパラメータの名前
          jsonpCallback: 'products' // コールバック関数の名前
        })
        .done(function(data, textStatus, jqXHR) {
          this.products = data;
        }.bind(this))
        .fail(function(jqXHR, textStatus, errorThrown) {
          this.isError = true;
          this.message = '商品リストの読み込みに失敗しました。';
        }.bind(this));
      },
    computed: {
        //絞り込み後の商品リストを返す算出プロパティ
        l_list: function() {
          //絞り込み後の商品リストを格納する新しい配列
          var newList = [];
          for (var i=0; i < this.products.length; i++) {
            //表示するかどうかのフラグ
            var isShow = true;
            //i番目の商品が表示対象かどうかを判定する
            if(this.showSale) {
                
            }
        }

        }
    }
});


/*var obj = JSON.parse(data);

Object.keys(obj).forEach(function(key) {

})*/