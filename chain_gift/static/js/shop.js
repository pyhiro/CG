// 数値を通貨書式「#,###,###」に変換するフィルター
Vue.filter('number_format', function(val) {
  return val.toLocaleString();
});

Vue.component('open-modal',{
  template : `
    <div id="overlay">
        <div id="content">
          <slot></slot>
            <a href="http:/..." onclick="return false;" class="mdl_btn_close square_btn" v-on:click="clickEvent">close</a>
        </div>
    </div>
    `,
  methods :{
    clickEvent: function(){
      this.$emit('from-child')
    }
  }
})


var app = new Vue({
  
  delimiters: ['[[',']]'],
  el: '#app',
  data: {
      //「並び替え」の選択値（1：標準、2：ポイントが低い順、3:ポイントが高い順、4:新着順)
      sortOrder: 1,
      // 商品リスト
      products: [],
      // エラーの有無
      isError: false,
      // メッセージ
      message: '',
      // カテゴリーの選択値　(0:全商品、1:スタンプ、2:参考書、3:文房具)
      category: 'すべての商品',
      //商品の写真が無い場合の仮写真
      syoki_img: '20201205.png',
      // モーダルの表示フラグ
      showContent: false,
      // モーダル表示用の名前
      inModal_name:'',
      // モーダル表示用の画像
      inModal_Image:'',
      // モーダル表示用のポイント
      inModal_price:0,
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
        //取得した商品データをproductsに格納
        this.products =  data.goods;

        //グッズの商品画像が無い場合の設定
        for (var i=0; i < this.products.length; i++){
          if(!this.products[i].goods_img) {
            this.products[i].goods_img = this.syoki_img
          }
        }
      }.bind(this))
      .fail(function(jqXHR, textStatus, errorThrown) {
        //データが取得出来ない場合の処理
        this.isError = true;
        this.message = '商品の読み込みに失敗しました。しばらく時間を置き再度アクセスしてください。';
      }.bind(this));
  },
  methods: {
    //以下４つカテゴリーの設定
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
          //何かの拍子にすり抜けた場合
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
      //ポイントが低い順に並び変える
      else if(this.sortOrder == 2) {
        newList.sort(function(a,b){
          return a.goods_value - b.goods_value;
        });
      }
      //ポイントが高い順に並び替える
      else if(this.sortOrder == 3) {
        newList.sort(function(a,b){
          return b.goods_value - a.goods_value;
        })
      }
      //新着順に並び替える
      else if(this.sortOrder == 4) {
        newList.sort(function(a,b){
          return b.goods_id - a.goods_id;
        })
      }
      //絞り込み後の商品リストを返す
      return newList;
    },
    //モーダル表示用及びモーダルの情報を挿入
    openModal: function(n,i,p){
      this.showContent = true
      this.inModal_name = n
      this.inModal_Image = i
      this.inModal_price = p
    },
    //モーダル非表示及び情報の初期化
    closeModal: function(){
      this.showContent = false
      this.inModal_name = ''
      this.inModal_Image = ''
      this.inModal_price = 0
    },
  }
});
