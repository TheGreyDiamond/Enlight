function encode_html(rawStr) {
  var encodedStr = rawStr.replace(/[\u00A0-\u9999<>\&]/g, function (i) {
    return "&#" + i.charCodeAt(0) + ";";
  });

  return encodedStr;
}

function does_list_contain(list, needle) {
  if (list.indexOf(needle) >= 0) {
    return true;
  } else {
    return false;
  }
}

function updateTime(k) {
  if (k < 10) {
    return "0" + k;
  } else {
    return k;
  }
}