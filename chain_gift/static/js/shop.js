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
      // カテゴリーの選択値　(0:全商品、1:スタンプ、2:参考書、3:文房具)
      category: 'すべての商品',
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
        this.products =  data.goods;
      }.bind(this))
      .fail(function(jqXHR, textStatus, errorThrown) {
        this.isError = true;
        this.message = '商品リストの読み込みに失敗しました。';
        alert('接続失敗')
      }.bind(this));
  },
  methods: {
    allList: function() {
      this.category = 'すべての商品';

    },
    stampList: function() {
      this.category = 'スタンプ';
    },
    bookList: function() {
      this.category = '参考書';
    },
    stationeryList: function() {
      this.category = '文房具';
    },
    sortList: function() {
      //絞り混み後のリストを格納する配列
      var newList = [];
      for (var i=0; i < this.products.length; i++){
        //表示対象かどうかの判定フラグ
        var isShow = false;
        //スタンプだけの場合
        if(this.category == 'スタンプ' && this.products[i].goods_category == 'stamp'){
          isShow = true;
          //参考書だけの場合
        }else if(this.category == "参考書"　&& this.products[i].goods_category == 'book'){
          isShow = true;
          //文房具だけの場合
        }else if(this.category == '文房具' && this.products[i].goods_category == 'stationery'){
          isShow = true;
          //全商品の場合
        }else if (this.category == 'すべての商品'){
          isShow = true;
        }else{
          isShow = false;
        }
        //対象の商品だけを新しい配列に追加する
        if (isShow) {
          newList.push(this.products[i]);
        }
      }
      // 新しい配列を並び変える
      if (this.sortOrder == 1) {
        //元の順番に並び替え済み
      }
      else if(this.sortOrder == 2) {
        //ポイントが低い順に並び変える
        newList.sort(function(a,b){
          return a.goods_value - b.goods_value;
        });
      }
      //絞り込み後の商品リストを返す
      return newList;
    }
  }
});
