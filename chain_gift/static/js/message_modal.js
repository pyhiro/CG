
(function($) {
	$.fn.layerBoard = function(option) {
		var elements = this;
		elements.each(function(){
			option = $.extend({
				delayTime: 200,		//表示までの待ち時間
				fadeTime : 500,		//表示開始から表示しきるまでの時間
				alpha : 0.8,		//背景レイヤーの透明度
				limitMin : 0,		//何分経過後に再度表示するか/分（0で再表示なし）
				easing: 'linear',		//イージング
			}, option);

			// モーダル表示用ボタンの表示処理 --------------------
			$('.image-popup').click(function() {
                var url = $(this).attr('name');
				//Ajaxを開始
				$.ajax({
					url: url,
					type: 'GET',
					dataType: 'json',
					success: function(data) {
					  var datum = data
                        var contents = datum.contents
                        var sender = datum.sender
                        var point = datum.point
                        $("#message").text(contents)
                        $("#sender").text(sender)
                        $("#point").text(point)
                        $("#").text(point)
					},
					error: function(){
						alert('失敗');
					}
				})
				$('#layer_board_area').css('display', 'block');
				$('.layer_board_bg', elements).show().animate({opacity: 0},0).delay(option.delayTime).animate({opacity: option.alpha},option.fadeTime,function(){
					$('.layer_board', elements).fadeIn(option.fadeTime);
					
					//表示した際背景のスクロール禁止
					$('html, body').css('overflow', 'hidden');	
				});
			});

			// .mdl_btn_closeをクリックした時の動作(非表示処理) --------------------
			$('.mdl_btn_close', elements).click(function() {

				$('.layer_board , #layer_board_area', elements).fadeOut(option.fadeTime);
				$('.layer_board_bg', elements).fadeOut(option.fadeTime);
				$('#layer_board_area').css('display', 'none');
				//非表示にした際背景のスクロール許可
				$('html, body').css('overflow', 'auto');
			});

			// 見た目処理(コンテンツが短い場合中央表示) --------------------
			var bg_height = $('.layer_board_bg').outerHeight();
			var layer_bord_height = $('.layer_board').outerHeight();
			if(bg_height + 40 >= layer_bord_height){
				$('.layer_board').addClass('shortLayer');
			}

		});
		return this;	
	};
})( jQuery );
