/* Hàm dùng chung cho trang chủ và trang mục lục. Dữ liệu nằm trong window.MUC_LUC (data/muc-luc.js). */
(function () {
  "use strict";

  function khongDau(s) {
    return (s || "").replace(/đ/g, "d").replace(/Đ/g, "D")
      .normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  // "t2n120", "T02 N 0120", "x60n1118" → dạng chuẩn "t02n0120"
  function chuanHoaMa(s) {
    return s.replace(/\b([tx])\s*0*(\d{1,3})\s*n\s*0*(\d{1,4})([a-z]?)\b/gi, function (_, t, v, n, h) {
      return t.toLowerCase() + ("0" + v).slice(-2) + "n" + ("000" + n).slice(-4) + h.toLowerCase();
    });
  }

  function ngayVN(iso) {
    return iso && iso.length >= 10 ? iso.slice(8, 10) + "/" + iso.slice(5, 7) + "/" + iso.slice(0, 4) : (iso || "");
  }

  function so(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function el(the, lop, noiDung) {
    var e = document.createElement(the);
    if (lop) e.className = lop;
    if (noiDung != null) e.textContent = noiDung;
    return e;
  }

  window.CKCH = { khongDau: khongDau, chuanHoaMa: chuanHoaMa, ngayVN: ngayVN, so: so, el: el };
})();
