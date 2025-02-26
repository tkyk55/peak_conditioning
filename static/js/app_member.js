function cancelCheck() {
// 予約キャンセル時のチェックなし確認
 　　    // 選択されているチェックボックスの値を取得する
        let allUnchecked = 0;
        $('input[type="checkbox"][name="delete"]').each(function(){
            if ($(this).is(':checked')) {
                allUnchecked += 1;
                return false; // ループを終了する
            }
        });
        if (allUnchecked > 0) {
            return true;
        } else {
            alert("選択してください");
            return false;
        }
}
function exBookingCheck() {
    // 体験予約時の確認

    const id_first_name = $("#id_first_name").val().trim(); // 入力値を取得し、空白を削除
    if (id_first_name === "") {
        alert("姓を入力してください。");
        return false; // 送信を中止
    }

    const id_last_name = $("#id_last_name").val().trim(); // 入力値を取得し、空白を削除
    if (id_last_name === "") {
        alert("名を入力してください。");
        return false; // 送信を中止
    }

    // 性別が選択されているか？
    if (!$('input[type="radio"][name="sex"]').is(':checked')){
        alert("性別を選択してください");
        return false;
    }

    // 人数が選択されているか？
    if (!$('input[type="radio"][name="people"]').is(':checked')){
        alert("人数を選択してください");
        return false;
    }

    const id_email = $("#id_email").val().trim(); // 入力値を取得し、空白を削除
    if (id_email === "") {
        alert("Emailを入力してください。");
        return false; // 送信を中止
    }

    return true;
}

function exemailResendConf(){
    let checked = confirm("お送りした認証メールは無効になります。よろしいですか？");
    return checked === true;
}

function exBookingDel(){
    let checked = confirm("体験予約を取り消します。よろしいですか？");
    return checked === true;
}

function profileCheck(){
    let telNumber = $('#id_tel_number').val();

    // 電話番号の正規表現（2桁, 3桁, 4桁の市外局番対応）
    let telRegex = /^(0\d{1,4})-?(\d{1,4})-?(\d{4})$/;

    if (!telRegex.test(telNumber)) {
        alert('電話番号の形式が正しくありません。例: 03-1234-5678、045-123-4567、0120-123-456');
        return false; // 検証失敗時、イベントを中断
    }

    // 検証成功時の動作
    return true; // 検証成功時、イベントを続行
}


