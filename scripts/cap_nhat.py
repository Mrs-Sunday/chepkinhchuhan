#!/usr/bin/env python3
"""Cập nhật website dự phòng Chép Kinh Chữ Hán.

Việc script làm, mỗi lần chạy:
  1. Kéo toàn bộ bài viết và trang tĩnh từ Blogger feed của blog gốc.
  2. Tách mã tạng, tên Hán, tên Hán Việt, số quyển, DOI, link tải từ mỗi bài.
  3. Tra Zenodo theo DOI để lấy danh sách file (chỉ tra những DOI chưa có trong bộ nhớ đệm).
  4. Sinh trang lưu trữ cho từng bài (bai/*.html), tải ảnh về thư mục anh/.
  5. Ghi data/muc-luc.js (dùng cho trang Mục lục, mở được cả khi xem offline).

Chỉ dùng thư viện chuẩn của Python, không cần cài thêm gì.

Chạy:  python scripts/cap_nhat.py
Thử với dữ liệu mẫu (không cần mạng):  python scripts/cap_nhat.py --mau scripts/mau
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------- cấu hình
BLOG = "https://hoadaochepkinhchuhan.blogspot.com"
ZENODO_API = "https://zenodo.org/api/records/"
TAI_ANH = os.environ.get("TAI_ANH", "1") != "0"      # đặt TAI_ANH=0 để không tải ảnh
CO_ANH = 1000                                         # cạnh dài ảnh khi tải về (px)
ANH_TOI_DA = 4 * 1024 * 1024                          # bỏ qua ảnh lớn hơn 4 MB
NGHI_ZENODO = 1.1                                     # giây nghỉ giữa hai lần gọi Zenodo
UA = "ChepKinhChuHan-backup/1.0 (+https://github.com)"

GOC = Path(__file__).resolve().parent.parent
THU_MUC_BAI = GOC / "bai"
THU_MUC_ANH = GOC / "anh"
THU_MUC_DATA = GOC / "data"
DEM_ZENODO = THU_MUC_DATA / "zenodo-dem.json"
GIO_VN = timezone(timedelta(hours=7))


# ---------------------------------------------------------------- mạng
def tai(url: str, nhi_phan: bool = False, thu_lai: int = 3):
    loi = None
    for lan in range(thu_lai):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                du_lieu = r.read()
                return du_lieu if nhi_phan else du_lieu.decode("utf-8")
        except urllib.error.HTTPError as e:
            loi = e
            if e.code in (404, 410):
                break
            if e.code == 429:
                time.sleep(30)
        except Exception as e:  # mạng chập chờn
            loi = e
        time.sleep(2 * (lan + 1))
    raise RuntimeError(f"Không tải được {url}: {loi}")


class Nguon:
    """Nguồn dữ liệu thật (mạng) hoặc dữ liệu mẫu trong thư mục."""

    def __init__(self, thu_muc_mau: Path | None):
        self.mau = thu_muc_mau

    def feed(self, loai: str, bat_dau: int, so_luong: int) -> dict:
        if self.mau:
            f = self.mau / f"{loai}-{bat_dau}.json"
            return json.loads(f.read_text("utf-8")) if f.exists() else {"feed": {}}
        url = (f"{BLOG}/feeds/{loai}/default?alt=json&max-results={so_luong}"
               f"&start-index={bat_dau}")
        return json.loads(tai(url))

    def zenodo(self, so: str) -> dict | None:
        if self.mau:
            f = self.mau / f"zenodo-{so}.json"
            return json.loads(f.read_text("utf-8")) if f.exists() else None
        try:
            return json.loads(tai(ZENODO_API + so))
        finally:
            time.sleep(NGHI_ZENODO)

    def anh(self, url: str) -> bytes | None:
        if self.mau:
            return None
        return tai(url, nhi_phan=True)


def keo_feed(nguon: Nguon, loai: str) -> list[dict]:
    tat_ca, bat_dau, buoc = [], 1, 150
    while True:
        trang = nguon.feed(loai, bat_dau, buoc).get("feed", {})
        muc = trang.get("entry", [])
        if not muc:
            break
        tat_ca.extend(muc)
        bat_dau += len(muc)
        if len(muc) < buoc and not nguon.mau:
            break
    return tat_ca


# ---------------------------------------------------------------- tách thông tin
RE_MA = re.compile(r"^\s*([TX])(\d{1,3})[Nn](\d{1,4})([A-Za-z]?)\b")
RE_HAN = re.compile(r"[㐀-鿿豈-﫿\U00020000-\U0003134f"
                    r"　-〿（）·・]+")
RE_QUYEN = re.compile(r"\((\d+)\s*quyển\)\s*$", re.I)
RE_DOI = re.compile(r"10\.5281/zenodo\.(\d+)")
RE_TAI_VE = re.compile(r"drive\.google|docs\.google|onedrive|1drv\.ms|mediafire|"
                       r"dropbox|mega\.nz|zenodo\.org/records/\d+/files", re.I)


def tach_tieu_de(tieu_de: str) -> dict:
    kq = {"ma": None, "han": None, "hv": None, "quyen": None}
    t = tieu_de.strip()
    m = RE_QUYEN.search(t)
    if m:
        kq["quyen"] = int(m.group(1))
        t = t[: m.start()].rstrip()
    m = RE_MA.match(t)
    if m:
        kq["ma"] = f"{m.group(1)}{int(m.group(2)):02d}n{m.group(3).zfill(4)}{m.group(4).lower()}"
        t = t[m.end():].strip()
        h = RE_HAN.match(t)
        if h:
            kq["han"] = h.group(0).strip()
            t = t[h.end():].strip()
        kq["hv"] = t or None
    return kq


def khoa_sap_xep(ma: str | None, tieu_de: str):
    if not ma:
        return (2, 0, 0, "", tieu_de)
    m = re.match(r"([TX])(\d+)n(\d+)([a-z]?)", ma)
    tang = 0 if m.group(1) == "T" else 1
    return (tang, int(m.group(2)), int(m.group(3)), m.group(4), tieu_de)


def khong_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


# ---------------------------------------------------------------- làm sạch HTML
THE_GIU = {
    "p", "br", "a", "img", "b", "strong", "i", "em", "u", "s", "span", "div",
    "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "table", "thead",
    "tbody", "tfoot", "tr", "td", "th", "caption", "blockquote", "ruby", "rt",
    "rp", "rb", "sup", "sub", "hr", "pre", "code", "figure", "figcaption",
    "small", "mark", "center",
}
THE_BO_CA_NOI_DUNG = {"script", "style", "noscript", "iframe", "object", "embed",
                      "form", "button", "input", "select", "textarea", "svg",
                      "canvas", "template", "head", "title", "meta", "link"}
THUOC_TINH_GIU = {"href", "src", "alt", "title", "colspan", "rowspan", "lang"}
THE_RONG = {"br", "img", "hr"}


class LamSach(HTMLParser):
    def __init__(self, doi_anh, ban_do_noi_bo=None):
        super().__init__(convert_charrefs=True)
        self.ban_do = ban_do_noi_bo or {}
        self.ra: list[str] = []
        self.bo = 0
        self.doi_anh = doi_anh
        self.links: list[tuple[str, str]] = []
        self._a_hien_tai: list | None = None

    def handle_starttag(self, tag, attrs):
        if tag in THE_BO_CA_NOI_DUNG:
            self.bo += 1
            return
        if self.bo or tag not in THE_GIU:
            return
        giu = []
        for k, v in attrs:
            if k not in THUOC_TINH_GIU or v is None:
                continue
            if k in ("href", "src"):
                v = v.strip()
                if v.lower().startswith(("javascript:", "data:", "vbscript:")):
                    continue
                if v.startswith("//"):
                    v = "https:" + v
                if k == "src" and tag == "img":
                    v = self.doi_anh(v)
                if k == "href" and tag == "a":
                    v = self.ban_do.get(chuan_hoa_link(v), v)
            giu.append((k, v))
        if tag == "a":
            href = dict(giu).get("href", "")
            self._a_hien_tai = [href, ""]
            if href.startswith("http"):
                giu.append(("rel", "noopener"))
        if tag == "img":
            giu.append(("loading", "lazy"))
        thuoc_tinh = "".join(f' {k}="{html.escape(v, quote=True)}"' for k, v in giu)
        self.ra.append(f"<{tag}{thuoc_tinh}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in THE_BO_CA_NOI_DUNG:
            self.bo = max(0, self.bo - 1)
            return
        if self.bo or tag not in THE_GIU or tag in THE_RONG:
            return
        if tag == "a" and self._a_hien_tai:
            self.links.append(tuple(self._a_hien_tai))
            self._a_hien_tai = None
        self.ra.append(f"</{tag}>")

    def handle_data(self, data):
        if self.bo:
            return
        if self._a_hien_tai is not None:
            self._a_hien_tai[1] += data
        self.ra.append(html.escape(data, quote=False))

    def ket_qua(self) -> str:
        s = "".join(self.ra)
        # bỏ các span/div rỗng do hiệu ứng trang trí để lại
        truoc = None
        while truoc != s:
            truoc = s
            s = re.sub(r"<(span|div|b|i|strong|em|u|font)>\s*</\1>", "", s)
        s = re.sub(r"(<br>\s*){3,}", "<br><br>", s)
        return s.strip()


# ---------------------------------------------------------------- ảnh
RE_CO_ANH_DUONG_DAN = re.compile(r"/(?:s|w|h)\d+(?:-[a-z0-9-]+)?/(?=[^/]+$)")
RE_CO_ANH_DUOI = re.compile(r"=(?:s|w|h)\d+[a-z0-9-]*$")


def doi_co_anh(url: str) -> str:
    if "googleusercontent.com" not in url and "bp.blogspot.com" not in url:
        return url
    if RE_CO_ANH_DUONG_DAN.search(url):
        return RE_CO_ANH_DUONG_DAN.sub(f"/s{CO_ANH}/", url)
    if RE_CO_ANH_DUOI.search(url):
        return RE_CO_ANH_DUOI.sub(f"=s{CO_ANH}", url)
    return url


def lam_doi_anh(nguon: Nguon, thong_ke: dict):
    def doi(url: str) -> str:
        if not TAI_ANH or not url.startswith("http"):
            return url
        duoi = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
        if duoi not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            duoi = ".jpg"
        ten = hashlib.sha1(url.encode()).hexdigest()[:16] + duoi
        dich = THU_MUC_ANH / ten
        if dich.exists():
            return f"../anh/{ten}"
        try:
            du_lieu = nguon.anh(doi_co_anh(url))
            if du_lieu is None:
                return url
            if len(du_lieu) > ANH_TOI_DA:
                thong_ke["anh_bo_qua"] += 1
                return url
            THU_MUC_ANH.mkdir(exist_ok=True)
            dich.write_bytes(du_lieu)
            thong_ke["anh_moi"] += 1
            return f"../anh/{ten}"
        except Exception as e:
            print(f"  ! ảnh: {e}", file=sys.stderr)
            return url
    return doi


# ---------------------------------------------------------------- Zenodo
def tom_tat_zenodo(so: str, rec: dict) -> dict:
    md = rec.get("metadata", {})
    files = rec.get("files") or []
    if isinstance(files, dict):  # định dạng InvenioRDM mới
        files = list((files.get("entries") or {}).values())
    ds = []
    for f in files:
        ten = f.get("key") or f.get("filename")
        if not ten:
            continue
        ds.append({
            "ten": ten,
            "kb": round((f.get("size") or f.get("filesize") or 0) / 1024),
            "url": f"https://zenodo.org/records/{so}/files/{urllib.parse.quote(ten)}?download=1",
        })
    lic = md.get("license")
    if isinstance(lic, dict):
        lic = lic.get("id")
    return {
        "tieu_de": md.get("title"),
        "ngay": md.get("publication_date"),
        "doi_chung": rec.get("conceptdoi"),
        "giay_phep": lic,
        "files": ds,
    }


def tra_zenodo(nguon: Nguon, cac_so: set[str]) -> dict:
    dem = json.loads(DEM_ZENODO.read_text("utf-8")) if DEM_ZENODO.exists() else {}
    can_tra = sorted(s for s in cac_so if s not in dem)
    print(f"Zenodo: {len(dem)} bản ghi đã có, cần tra thêm {len(can_tra)}")
    for i, so in enumerate(can_tra, 1):
        try:
            rec = nguon.zenodo(so)
            if rec:
                dem[so] = tom_tat_zenodo(so, rec)
        except Exception as e:
            print(f"  ! zenodo {so}: {e}", file=sys.stderr)
        if i % 25 == 0:
            print(f"  … {i}/{len(can_tra)}")
            DEM_ZENODO.write_text(json.dumps(dem, ensure_ascii=False, indent=0), "utf-8")
    DEM_ZENODO.write_text(json.dumps(dem, ensure_ascii=False, indent=0), "utf-8")
    return dem


# ---------------------------------------------------------------- trang bài
MAU_BAI = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{tieu_de_the} · Chép Kinh Chữ Hán</title>
<link rel="canonical" href="{goc}">
<link rel="stylesheet" href="../assets/kieu.css">
</head>
<body class="trang-bai">
<header class="dau-trang">
  <a class="ten-site" href="../index.html"><span lang="zh-Hant">冩漢字佛經</span> Chép Kinh Chữ Hán</a>
  <nav><a href="../muc-luc.html">Mục lục</a></nav>
</header>
<main class="bai">
  <p class="duong-dan"><a href="../muc-luc.html">Mục lục</a>{bo_html}</p>
  <h1>{tieu_de_html}</h1>
  <p class="thong-tin">Đăng ngày {ngay} · <a href="{goc}" rel="noopener">Xem bài trên blog gốc</a></p>
  {hop_tai}
  <article class="noi-dung">
{noi_dung}
  </article>
</main>
<footer class="chan-trang">
  <p>Bản lưu dự phòng của blog Chép Kinh Chữ Hán, cập nhật {cap_nhat}. Tài liệu đính âm phát hành theo giấy phép
  <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.vi" rel="noopener">CC BY-NC-SA 4.0</a>; chánh văn lấy từ CBETA.</p>
</footer>
</body>
</html>
"""


def hop_tai_ve(muc: dict, z: dict | None) -> str:
    if not muc.get("doi") and not muc.get("tai_ve"):
        return ""
    dong = []
    if muc.get("doi"):
        d = muc["doi"]
        dong.append(f'<p class="doi">DOI <a href="https://doi.org/{d}" rel="noopener">{d}</a></p>')
    if z and z.get("files"):
        li = "".join(
            f'<li><a href="{html.escape(f["url"])}" rel="noopener">{html.escape(f["ten"])}</a>'
            f'<span class="co">{f"{f["kb"]:,}".replace(",", ".")} KB</span></li>'
            for f in z["files"])
        dong.append(f'<ul class="ds-file">{li}</ul>')
    elif muc.get("tai_ve"):
        dong.append(f'<p><a href="{html.escape(muc["tai_ve"])}" rel="noopener">Tải file</a></p>')
    return '<section class="hop-tai" aria-label="Tải tài liệu">' + "".join(dong) + "</section>"


def chuan_hoa_link(url: str) -> str:
    """Đưa link nội bộ của blog về một dạng chung để so khớp."""
    u = urllib.parse.urlparse(url.strip())
    if not u.netloc.endswith("blogspot.com"):
        return url
    return "https://" + u.netloc.lower() + u.path


def ngay_vn(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}" if len(iso) >= 10 else iso


def ten_tep_bai(link: str, id_du_phong: str) -> str:
    duong = urllib.parse.urlparse(link).path.strip("/")
    duong = re.sub(r"\.html?$", "", duong)
    ten = re.sub(r"[^a-z0-9-]+", "-", duong.lower()).strip("-")
    return (ten or id_du_phong)[:120] + ".html"


# ---------------------------------------------------------------- chính
def xu_ly(nguon: Nguon):
    THU_MUC_BAI.mkdir(exist_ok=True)
    THU_MUC_DATA.mkdir(exist_ok=True)
    thong_ke = {"anh_moi": 0, "anh_bo_qua": 0}
    doi_anh = lam_doi_anh(nguon, thong_ke)
    bay_gio = datetime.now(GIO_VN)

    bai = [("bai", e) for e in keo_feed(nguon, "posts")]
    bai += [("trang", e) for e in keo_feed(nguon, "pages")]
    print(f"Blogger: {sum(1 for l, _ in bai if l == 'bai')} bài, "
          f"{sum(1 for l, _ in bai if l == 'trang')} trang tĩnh")
    if not bai:
        sys.exit("Không lấy được bài nào từ blog — dừng lại để không ghi đè dữ liệu cũ.")

    danh_sach, cac_doi = [], set()
    tho = []
    for loai, e in bai:
        tieu_de = html.unescape(e.get("title", {}).get("$t", "")).strip() or "(không tiêu đề)"
        goc = next((l["href"] for l in e.get("link", []) if l.get("rel") == "alternate"), "")
        noi_dung_tho = e.get("content", {}).get("$t") or e.get("summary", {}).get("$t", "")
        nhan = [c["term"] for c in e.get("category", [])]
        id_ = e.get("id", {}).get("$t", "").rsplit("-", 1)[-1]
        tho.append((loai, tieu_de, goc, noi_dung_tho, nhan, id_, e))
        for m in RE_DOI.finditer(noi_dung_tho):
            cac_doi.add(m.group(1))

    dem = tra_zenodo(nguon, cac_doi)
    # link giữa các bài trên blog → trỏ sang trang lưu tương ứng trên site này
    ban_do = {chuan_hoa_link(g): ten_tep_bai(g, i) for _, _, g, _, _, i, _ in tho if g}

    for loai, tieu_de, goc, noi_dung_tho, nhan, id_, e in tho:
        p = LamSach(doi_anh, ban_do)
        p.feed(noi_dung_tho)
        p.close()
        noi_dung = p.ket_qua()
        m = RE_DOI.search(noi_dung_tho)
        doi = f"10.5281/zenodo.{m.group(1)}" if m else None
        tai_ve = next((h for h, _ in p.links if RE_TAI_VE.search(h or "")), None)
        tt = tach_tieu_de(tieu_de)
        tep = ten_tep_bai(goc, id_)
        ngay = (e.get("published", {}).get("$t") or "")[:10]
        z = dem.get(m.group(1)) if m else None

        muc = {
            "loai": loai, "tieu_de": tieu_de, **tt, "bo": nhan, "ngay": ngay,
            "doi": doi, "tai_ve": tai_ve, "goc": goc, "tep": f"bai/{tep}",
        }
        if z and z.get("files"):
            muc["files"] = len(z["files"])
        muc["tim"] = khong_dau(" ".join(filter(None, [tieu_de, " ".join(nhan)])))
        danh_sach.append(muc)

        bo_html = "".join(
            f' / <a href="../muc-luc.html?bo={urllib.parse.quote(b)}">{html.escape(b)}</a>'
            for b in nhan)
        if tt["ma"]:
            tieu_de_html = (f'<span class="ma">{html.escape(tt["ma"])}</span> '
                            f'<span class="han" lang="zh-Hant">{html.escape(tt["han"] or "")}</span> '
                            f'<span class="hv">{html.escape(tt["hv"] or "")}</span>')
        else:
            tieu_de_html = html.escape(tieu_de)
        (THU_MUC_BAI / tep).write_text(MAU_BAI.format(
            tieu_de_the=html.escape(tieu_de), goc=html.escape(goc), bo_html=bo_html,
            tieu_de_html=tieu_de_html, ngay=ngay_vn(ngay), hop_tai=hop_tai_ve(muc, z),
            noi_dung=noi_dung, cap_nhat=bay_gio.strftime("%d/%m/%Y"),
        ), "utf-8")

    # Giữ lại các mục đã có trong bản lưu nhưng nay không còn trên blog
    # (bài bị gỡ, blog lỗi một phần...). Đây là bản dự phòng nên không xóa gì.
    cu = THU_MUC_DATA / "muc-luc.json"
    if cu.exists():
        da_co = {d["tep"] for d in danh_sach}
        for d in json.loads(cu.read_text("utf-8")).get("muc", []):
            if d["tep"] not in da_co and (GOC / d["tep"]).exists():
                d["khong_con_tren_blog"] = True
                danh_sach.append(d)

    danh_sach.sort(key=lambda d: khoa_sap_xep(d["ma"], d["tieu_de"]))
    tong = {
        "cap_nhat": bay_gio.isoformat(timespec="minutes"),
        "so_bai": sum(1 for d in danh_sach if d["loai"] == "bai"),
        "so_kinh": sum(1 for d in danh_sach if d["ma"]),
        "so_quyen": sum(d["quyen"] or 0 for d in danh_sach if d["ma"]),
        "so_doi": sum(1 for d in danh_sach if d["doi"]),
    }
    goi = {"tong": tong, "muc": danh_sach}
    (THU_MUC_DATA / "muc-luc.json").write_text(
        json.dumps(goi, ensure_ascii=False, indent=1), "utf-8")
    (THU_MUC_DATA / "muc-luc.js").write_text(
        "window.MUC_LUC=" + json.dumps(goi, ensure_ascii=False, separators=(",", ":")) + ";\n",
        "utf-8")

    print(f"Xong: {tong['so_kinh']} bộ kinh ({tong['so_quyen']} quyển), "
          f"{tong['so_doi']} mục có DOI, ảnh mới {thong_ke['anh_moi']}, "
          f"ảnh bỏ qua vì quá lớn {thong_ke['anh_bo_qua']}.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mau", type=Path, help="thư mục dữ liệu mẫu, không dùng mạng")
    a = ap.parse_args()
    xu_ly(Nguon(a.mau))
