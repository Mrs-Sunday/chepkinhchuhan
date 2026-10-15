/* Google Analytics 4 cho website dự phòng Chép Kinh Chữ Hán.
   Chỉ cần sửa MỘT dòng bên dưới: dán Measurement ID (dạng G-XXXXXXXXXX) vào giữa hai dấu ngoặc kép.
   Để trống hoặc giữ nguyên "G-XXXXXXXXXX" thì website không đo gì cả. */
(function () {
  "use strict";
  var MA_GA4 = "G-TVG69P94JK";

  if (!/^G-[A-Z0-9]{6,}$/.test(MA_GA4) || MA_GA4 === "G-XXXXXXXXXX") return;
  if (location.protocol === "file:") return; // không đo khi mở bản offline trên máy

  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + MA_GA4;
  document.head.appendChild(s);

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag("js", new Date());
  gtag("config", MA_GA4);
})();
