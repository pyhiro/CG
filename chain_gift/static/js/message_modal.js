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
            
            //スクロールポジションの変数宣言
            var scrollPosition;

			// モーダル表示用ボタンの表示処理 --------------------
			$('#modal1,#modal2,#modal3').click(function() {
                //スクロールポジションを取得
                scrollPosition = $(window).scrollTop();
                //取得したポジションで固定
		        $('body').addClass('fixed').css({'top': -scrollPosition});
                
                var url = $(this).attr('name');

                var i = $(this).attr('id')


                $(this).css('background', 'rgb(230, 230, 230)')

				//Ajaxを開始
				$.ajax({
					url: url,
					type: 'GET',
					dataType: 'json',
					success: function(data) {

                        var datum = data
                        var contents = datum.contents
                        var sender = datum.sender
                        var recipient = datum.recipient
                        var point = datum.point
                        var time = datum.time
                        //日本時間に変換
                        var jp_time =  new Date(time).toLocaleString("ja").slice(0,-3);;;

                        $("#message").text(contents)
                        if(i == 'modal3'){
                            $("#sender_recipient").text(recipient)
                            $("#delete_button").attr("href", datum.sender_delete_url)
                        }else{
                            $("#delete_button").attr("href", datum.recipient_delete_url)
                            $("#sender_recipient").text(sender)
                        }
                        $("#point").text(point+"ポイント")
                        $("#time").text(jp_time)
					},
					error: function(){
					}
                })
				    $('#layer_board_area').css('display', 'block');
				    $('.layer_board_bg', elements).show().animate({opacity: 0},0).delay(option.delayTime).animate({opacity: option.alpha},option.fadeTime,function(){
					$('.layer_board', elements).fadeIn(option.fadeTime);
                    //<a>タグのリンクを無効化　＊これが無いとTOPに飛ぶ＊
                    return false	
                });
			});

			// .mdl_btn_closeをクリックした時の動作(非表示処理) --------------------
			$('.mdl_btn_close', elements).click(function() {

                //上で固定したのを無効化
                $('body').removeClass('fixed').css({'top': 0});
		        window.scrollTo( 0 , scrollPosition );

				$('.layer_board , #layer_board_area', elements).fadeOut(1500);
				$('.layer_board_bg', elements).fadeOut(1500);
				$('#layer_board_area').fadeOut(1500);

                //<a>タグのリンクを無効化　＊これが無いとTOPに飛ぶ
                return false
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

	$.fn.layerBoardDark = function(option) {
		var elements = this;
		elements.each(function(){
			option = $.extend({
				delayTime: 200,		//表示までの待ち時間
				fadeTime : 500,		//表示開始から表示しきるまでの時間
				alpha : 0.8,		//背景レイヤーの透明度
				limitMin : 0,		//何分経過後に再度表示するか/分（0で再表示なし）
				easing: 'linear',		//イージング
            }, option);

            //スクロールポジションの変数宣言
            var scrollPosition;

			// モーダル表示用ボタンの表示処理 --------------------
			$('#modal1,#modal2,#modal3').click(function() {
                //スクロールポジションを取得
                scrollPosition = $(window).scrollTop();
                //取得したポジションで固定
		        $('body').addClass('fixed').css({'top': -scrollPosition});

                var url = $(this).attr('name');

                var i = $(this).attr('id')


                $(this).css('background', 'rgb(0, 0, 0)')

				//Ajaxを開始
				$.ajax({
					url: url,
					type: 'GET',
					dataType: 'json',
					success: function(data) {
                        var datum = data
                        var contents = datum.contents
                        var sender = datum.sender
                        var recipient = datum.recipient
                        var point = datum.point
                        var time = datum.time
                        //日本時間に変換
                        var jp_time =  new Date(time).toLocaleString("ja").slice(0,-3);;;

                        $("#message").text(contents)
                        if(i == 'modal3'){
                            $("#sender_recipient").text(recipient)
                            $("#delete_button").attr("href", datum.sender_delete_url)
                        }else{
                            $("#delete_button").attr("href", datum.recipient_delete_url)
                            $("#sender_recipient").text(sender)
                        }
                        $("#point").text(point+"ポイント")
                        $("#time").text(jp_time)
					},
					error: function(){
					}
                })
				    $('#layer_board_area').css('display', 'block');
				    $('.layer_board_bg', elements).show().animate({opacity: 0},0).delay(option.delayTime).animate({opacity: option.alpha},option.fadeTime,function(){
					$('.layer_board', elements).fadeIn(option.fadeTime);
                    //<a>タグのリンクを無効化　＊これが無いとTOPに飛ぶ＊
                    return false
                });
			});

			// .mdl_btn_closeをクリックした時の動作(非表示処理) --------------------
			$('.mdl_btn_close', elements).click(function() {

                //上で固定したのを無効化
                $('body').removeClass('fixed').css({'top': 0});
		        window.scrollTo( 0 , scrollPosition );

				$('.layer_board , #layer_board_area', elements).fadeOut(1500);
				$('.layer_board_bg', elements).fadeOut(1500);
				$('#layer_board_area').fadeOut(1500);

                //<a>タグのリンクを無効化　＊これが無いとTOPに飛ぶ
                return false
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
