tạo ra một pipeline, sau khi upload excel + upload markdown file + input text
=> viết AI prompt trích xuất những thông tin [specification] ngắn gọn từ file yêu cầu
=> lưu vào sqlite database
=> trả về kết quả cho người dùng


- Sau khi bấm button [analysis requirements] => tiến hình lưu query và kết quả vào database  (sqlite)
- Khi init application => load dữ liệu query mới nhất từ database ra để hiển thị cho người dùng


- Khi upload file excel => save file vào folder `uploads` và hiển thị thông tin file cho người dùng
- Lịch sử analysis sẽ lưu thêm file uploads của người dùng.