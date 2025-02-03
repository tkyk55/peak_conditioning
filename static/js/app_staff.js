function delCheck(){
    let checked = confirm("削除します");
    if (checked === true) {
        return true;
    } else {
        return false;
    }
}

function updateynCheck(){
    let checked = confirm("更新します");
    return checked === true;
}

function editCheck() {
    // 選択されているラジオボタンの値を取得する
    let selectedRadio = document.querySelector("input[name='select_staff']:checked");

    // 選択されているラジオボタンがない場合
    if (!selectedRadio) {
        // エラーメッセージを表示する
        alert("選択してください");
        return false;
    }
}

function daytimeInputCheck() {
    let startTime = $('#id_start option:selected').val();
    let endTime = $('#id_end option:selected').val();

    // 時間を Date オブジェクトに変換
    let startDate = new Date('1970-01-01T' + startTime + ':00');
    let endDate = new Date('1970-01-01T' + endTime + ':00');

    // 時間を比較
    if(startDate >= endDate) {
        alert("開始時刻が終了時刻より大きい、または同じです。確認してください");
        return false;
    }

    return true;
}

function StaffBookingInputCheck() {
    let startTime = $('#id_start option:selected').val();
    let endTime = $('#id_end option:selected').val();

    // 時間を Date オブジェクトに変換
    let startDate = new Date('1970-01-01T' + startTime + ':00');
    let endDate = new Date('1970-01-01T' + endTime + ':00');

    // console.log(startDate);
    // console.log(endDate);

    // 時間を比較
    if(startDate >= endDate) {
        alert("開始時刻が終了時刻より大きい、または同じです。確認してください");
        return false;
    }

    let registration_hour = $('#id_registration_hour').val();
    let userConfirmed = false; // userConfirmed を関数スコープで定義


    if (startTime !== registration_hour) {
        if (registration_hour) {
            let userConfirmed = confirm("時間が変更されています。時間変更のメールを送信しますか？");
            if (userConfirmed === true) {
                // アクションタイプをメール送信に変更
                $('#id_action_type').val('send_mail_submit');
                return true;
            } else {
                return true;
            }
        } else {
            let userConfirmed = confirm("予約を入力した旨のメールを送信しますか？");
            if (userConfirmed === true) {
                // アクションタイプをメール送信に変更
                $('#id_action_type').val('send_mail_submit');
                return true;
            } else {
                return true;
            }
        }
    }

    return true;
}

function StaffExBookingCheck() {
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

    // 年齢が選択されているか？
    if (!$('input[type="radio"][name="age"]').is(':checked')){
        alert("年齢を選択してください");
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

    let userConfirmed = confirm("予約を入力した旨のメールを送信しますか？");
    if (userConfirmed === true) {
        // アクションタイプをメール送信に変更
        $('#id_action_type').val('send_mail_submit');
        return true;
    } else {
        return true;
    }

}

function StaffExBookingDelCheck() {
    let checked = confirm("削除します");
    if (checked === true) {
        let checked = confirm("予約を削除した旨のメールを送信しますか？");
        if (checked === true) {
            $('#id_action_type').val('send_mail_submit');
            return true;
        } else {
            return true;
        }
    } else {
        return false;
    }
}