function delCheck(){
    var checked = confirm("削除します");
    if (checked == true) {
        return true;
    } else {
        return false;
    }
}

function updateynCheck(){
    var checked = confirm("更新します");
    if (checked == true) {
        return true;
    } else {
        return false;
    }
}

function editCheck() {
    // 選択されているラジオボタンの値を取得する
    var selectedRadio = document.querySelector("input[name='select_staff']:checked");

    // 選択されているラジオボタンがない場合
    if (!selectedRadio) {
        // エラーメッセージを表示する
        alert("選択してください");
        return false;
    }
}

function entCheck() {
    var startValueByName = $("input[name='start']").val();
    var minutesPart = startValueByName.split(":")[1];
    if (minutesPart === "00" || minutesPart === "15" || minutesPart === "30" || minutesPart === "45") {
        return true;
    } else {
        alert("00分,15分,30分,45分を選択してください");
        return false;
    }
}

function daytimeInputCheck() {
    var startValueByName = $("input[name='start']").val();
    var endValueByName = $("input[name='end']").val();
    var targetDateValueByName = $("input[name='target_date']").val();

    // 分を抜き出す
    var startMinutesPart = startValueByName.split(":")[1];
    var endMinutesPart = endValueByName.split(":")[1];

    // Dateオブジェクトを作成
    var startDate = new Date(startValueByName);
    var endDate = new Date(endValueByName);
    var targetDate = new Date(targetDateValueByName);

    // 時間を比較
    if(startDate >= endDate) {
        alert("開始時刻が終了時刻より大きい、または同じです。確認してください");
        return false;
    }

    // 分が "00", "15", "30", "45" でないかチェック
    var validMinutes = ["00", "15", "30", "45"];
    if(!validMinutes.includes(startMinutesPart)) {
        alert("エラー: 開始の分は00分, 15分, 30分, 45分のいずれかを選択してください");
        return false;
    }
    if(!validMinutes.includes(endMinutesPart)) {
        alert("エラー: 終了の分は00分, 15分, 30分, 45分のいずれかを選択してください");
        return false;
    }

    // 年、月、日を取り出す
    var startYear = startDate.getFullYear();
    var startMonth = startDate.getMonth();
    var startDay = startDate.getDate();
    var startHours = startDate.getHours();

    var endYear = endDate.getFullYear();
    var endMonth = endDate.getMonth();
    var endDay = endDate.getDate();
    var endHours = endDate.getHours();
    var endMinutes = endDate.getMinutes();

    var targetYear = targetDate.getFullYear();
    var targetMonth = targetDate.getMonth();
    var targetDay = targetDate.getDate();

    consolelog(targetYear);
    consolelog(targetMonth);
    consolelog(targetDay);


    // 年、月、日を比較
    if(startYear === targetYear && startMonth === targetMonth && startDay === targetDay && endYear === targetYear && endMonth === targetMonth && endDay === targetDay) {
    } else {
        alert("エラー: 日付を変更しないでください");
        return false;
    }

    if(startHours < 9 ){
        alert("エラー: 開始は9時より前にしないでください");
        return false;
    }

    if(startHours > 19 ){
        alert("エラー: 開始は19時より後にしないでください");
        return false;
    }

    if(endHours < 9 ){
        alert("エラー: 終了は9時より前にしないでください");
        return false;
    }

    if(endHours === 20 && endMinutes > 0){
        alert("エラー: 終了は20時より後にしないでください");
        return false;
    }

    if(endHours > 20){
        alert("エラー: 終了は20時より後にしないでください");
        return false;
    }

    return true;
}

