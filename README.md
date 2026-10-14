# Chép Kinh Chữ Hán — website dự phòng

Bản dự phòng của blog [hoadaochepkinhchuhan.blogspot.com](https://hoadaochepkinhchuhan.blogspot.com/), chạy trên GitHub Pages.

Mỗi sáng thứ Hai, GitHub tự kéo bài mới từ blog, tra file trên Zenodo theo DOI, lưu lại bài viết và ảnh bìa, rồi đăng lại website. Không cần cập nhật tay.

## Website gồm những gì

| Phần | Nội dung | Còn dùng được khi blog gốc sập? |
|---|---|---|
| Trang chủ | Giới thiệu, ô tìm kiếm, bài mới đăng, danh sách theo bộ | Có |
| Mục lục | Tra theo mã tạng (gõ `T2n120` hay `T02N0120` đều được), tên Hán, tên Hán Việt có dấu hay không dấu; lọc theo tạng, theo bộ; nhóm theo tập Đại Chánh Tạng / Vạn Tục Tạng | Có |
| Bài lưu | Bản sao từng bài blog (đã bỏ script trang trí), ảnh bìa tải về kho, link giữa các bài trỏ sang bản lưu | Có |
| Ô tải file | Danh sách file DOCX/PDF trên Zenodo kèm dung lượng, tải thẳng | Có (file nằm trên Zenodo) |
| Link Google Drive trong bài | Giữ nguyên như bài gốc | Tùy Google Drive |

Một vài nguyên tắc của bản dự phòng:

- **Không bao giờ xóa.** Bài nào bị gỡ khỏi blog vẫn được giữ lại, và ghi chú "Không còn trên blog gốc" trong mục lục.
- **Blog lỗi thì đứng yên.** Nếu lần chạy nào không lấy được bài nào từ blog, script dừng lại, giữ nguyên dữ liệu cũ, và GitHub gửi email báo lỗi.
- **File kinh không chép vào đây.** File DOCX/PDF đã nằm trên Zenodo (lưu trữ lâu dài của CERN), website chỉ dẫn tới đó bằng DOI.

---

## Cài đặt lần đầu (khoảng 20 phút, làm trên máy tính)

### 1. Tạo tài khoản GitHub

Vào [github.com/signup](https://github.com/signup). Nên dùng **email bút danh** (email đang dùng cho Zenodo/ORCID) để giữ ẩn danh.

Tên tài khoản sẽ nằm trong địa chỉ website: `https://<tên-tài-khoản>.github.io/chep-kinh-chu-han/`. Chọn tên không lộ tên thật, ví dụ `hoadao-chepkinh`.

### 2. Tạo kho chứa (repository)

1. Bấm dấu **+** góc trên phải → **New repository**.
2. **Repository name**: `chep-kinh-chu-han`
3. Chọn **Public** (GitHub Pages miễn phí chỉ dành cho kho công khai).
4. Bấm **Create repository**.

### 3. Tải các file lên

1. Trong kho vừa tạo, bấm **uploading an existing file**.
2. Giải nén file zip, mở thư mục `chep-kinh-chu-han-site`, chọn **tất cả** file và thư mục bên trong (`index.html`, `muc-luc.html`, `assets`, `scripts`, `README.md`…) rồi kéo thả vào trang.
3. Bấm **Commit changes**.

**Riêng file quy trình tự động** nằm trong thư mục ẩn `.github` nên trình duyệt thường bỏ qua khi kéo thả. Tạo tay như sau:

1. Bấm **Add file → Create new file**.
2. Ô tên file, gõ đúng: `.github/workflows/cap-nhat.yml` (gõ dấu `/` thì GitHub tự tạo thư mục).
3. Mở file `cap-nhat.yml` trong thư mục đã giải nén bằng Notepad, chép toàn bộ nội dung, dán vào.
4. Bấm **Commit changes**.

Làm tương tự với file rỗng `.nojekyll` (tạo file tên `.nojekyll`, để trống nội dung).

### 4. Bật GitHub Pages

**Settings** → **Pages** (cột trái) → mục **Source** chọn **GitHub Actions**.

### 5. Chạy lần đầu

1. Vào tab **Actions**. Nếu GitHub hỏi, bấm nút xác nhận cho phép chạy workflow.
2. Chọn **Cập nhật và đăng website** → **Run workflow** → **Run workflow**.
3. Lần đầu mất khoảng 15–30 phút (kéo hơn 500 bài, tra từng DOI trên Zenodo, tải ảnh bìa). Các lần sau chỉ vài phút vì đã có sẵn.
4. Dấu tích xanh là xong. Website ở `https://<tên-tài-khoản>.github.io/chep-kinh-chu-han/`.

---

## Sau khi cài xong

**Không cần làm gì thêm.** Mỗi sáng thứ Hai website tự cập nhật. Muốn cập nhật ngay sau khi đăng bài mới: tab **Actions** → **Run workflow**.

**Khi nhận email báo lỗi từ GitHub:** thường là blog gốc hoặc Zenodo tạm thời không phản hồi. Đợi một lúc rồi bấm **Re-run jobs**. Nếu blog gốc thật sự mất, website vẫn giữ nguyên bản cuối cùng.

**GitHub có thể tạm ngưng lịch chạy** nếu kho lâu không có hoạt động (60 ngày). GitHub sẽ gửi email báo trước; chỉ cần vào tab **Actions** bấm bật lại.

**Muốn sửa chữ trên trang chủ:** mở `index.html` trên GitHub, bấm biểu tượng bút chì, sửa, **Commit changes**. Website tự đăng lại.

## Gắn tên miền riêng (tùy chọn)

Nếu sau này mua tên miền (ví dụ `chepkinhchuhan.org`): **Settings → Pages → Custom domain**, nhập tên miền, rồi làm theo hướng dẫn của GitHub để thêm bản ghi DNS ở nơi mua tên miền. Đổi tên miền không ảnh hưởng gì tới dữ liệu.

## Dành cho người kỹ thuật

- `scripts/cap_nhat.py`: chỉ dùng thư viện chuẩn Python 3.10+. Nguồn: Blogger JSON feed (`/feeds/posts/default`, `/feeds/pages/default`) và Zenodo REST API (`/api/records/<id>`).
- `data/muc-luc.js` / `muc-luc.json`: dữ liệu mục lục. Dạng `.js` để trang mở được cả khi xem offline (mở thẳng `index.html` trên máy, không cần máy chủ).
- `data/zenodo-dem.json`: bộ nhớ đệm kết quả tra Zenodo; xóa file này để tra lại từ đầu.
- `TAI_ANH=0 python scripts/cap_nhat.py`: chạy mà không tải ảnh.
- `python scripts/cap_nhat.py --mau scripts/mau`: chạy thử với dữ liệu mẫu, không cần mạng.

Giấy phép tài liệu đính âm: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.vi). Chánh văn: CBETA.
