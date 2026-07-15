"""
PHẦN 1: PHÂN TÍCH VÀ ĐỀ XUẤT ĐA GIẢI PHÁP

1.1. Phân tích đầu vào và đầu ra

- Dữ liệu phải được kiểm tra đầu tiên: Course có tồn tại hay không (course_id lấy
  từ path parameter). Nếu không tồn tại, trả về 404 ngay, không cần truy vấn tiếp.
- Điều kiện lọc Enrollment:
    + Enrollment.course_id == course_id.
    + Enrollment.status in ("STUDYING", "COMPLETED"), loại bỏ CANCELLED.
- Điều kiện lọc Student:
    + Student.status == "ACTIVE".
    + Student phải có ít nhất một Enrollment thỏa điều kiện ở trên.
- Loại bỏ sinh viên trùng: một sinh viên có thể có nhiều Enrollment hợp lệ cho
  cùng một khóa học (ví dụ đăng ký lại sau khi hủy). Dùng DISTINCT trên Student.id
  (hoặc gom nhóm bằng dict/set theo student_id nếu xử lý bằng vòng lặp) để đảm bảo
  mỗi sinh viên chỉ xuất hiện một lần trong kết quả.
- Trường hợp trả về danh sách rỗng: Course tồn tại nhưng không có Enrollment nào
  thỏa điều kiện (không có STUDYING/COMPLETED, hoặc sinh viên tương ứng không
  ACTIVE). Đây KHÔNG phải lỗi 404, chỉ là total_students = 0, students = [].

1.2. Đề xuất tối thiểu hai giải pháp

Giải pháp 1 - Truy vấn Enrollment rồi dùng vòng lặp:
    1) Query toàn bộ Enrollment theo course_id và status hợp lệ.
    2) Với mỗi Enrollment, query tiếp Student theo student_id, kiểm tra ACTIVE.
    3) Dùng dict/set theo student_id để loại trùng khi thêm vào danh sách kết quả.
    4) Sắp xếp danh sách bằng sorted() theo full_name sau khi đã gom xong.

Giải pháp 2 - Dùng JOIN giữa Student và Enrollment:
    1) Viết một câu query duy nhất JOIN Student với Enrollment.
    2) Áp toàn bộ điều kiện lọc (course_id, status Enrollment, status Student)
       ngay trong WHERE của câu JOIN.
    3) Dùng DISTINCT trên Student.id để loại sinh viên trùng ngay trong SQL.
    4) Dùng ORDER BY full_name ngay trong câu query, để MySQL xử lý sắp xếp.

PHẦN 2: SO SÁNH VÀ LỰA CHỌN

6.3. Bảng so sánh

| Tiêu chí                  | Vòng lặp                                   | JOIN                                  |
|----------------------------|---------------------------------------------|-----------------------------------------|
| Độ dễ hiểu                | Dễ hình dung với người mới, đọc tuần tự      | Cần biết SQL JOIN, khó hơn lúc đầu      |
| Số câu truy vấn            | N+1 (1 lần lấy Enrollment, N lần lấy Student)| 1 câu truy vấn duy nhất                |
| Tốc độ khi dữ liệu nhỏ     | Chấp nhận được, chênh lệch không đáng kể     | Nhanh, chênh lệch không rõ rệt          |
| Tốc độ khi dữ liệu lớn     | Chậm rõ rệt do nhiều round-trip đến DB        | Nhanh hơn nhiều, DB tối ưu JOIN + index |
| Bộ nhớ sử dụng             | Tốn bộ nhớ Python để gom, lọc trùng thủ công  | DB xử lý DISTINCT, Python chỉ nhận kết quả cuối |
| Khả năng bảo trì           | Logic lọc/loại trùng nằm rải rác trong code   | Logic tập trung trong một câu query    |
| Khả năng mở rộng           | Thêm điều kiện lọc phải sửa vòng lặp Python   | Thêm điều kiện lọc chỉ cần thêm .filter()|

Phân tích:
- Giải pháp vòng lặp dễ hiểu hơn với người mới vì đọc tuần tự từng bước, không
  cần hiểu JOIN.
- Giải pháp vòng lặp tạo nhiều câu truy vấn hơn (N+1), còn JOIN chỉ 1 câu.
- Với 1.000 sinh viên, giải pháp JOIN phù hợp hơn hẳn vì tránh N+1 query,
  vòng lặp sẽ gây ra hàng nghìn round-trip tới database.
- Giải pháp JOIN dễ thêm điều kiện lọc hơn, chỉ cần thêm .filter() vào query.
- Giải pháp vòng lặp có nguy cơ gây chậm API cao nhất khi dữ liệu lớn, do vấn đề
  N+1 query kinh điển.

6.4. Lựa chọn giải pháp

- Giải pháp được chọn: Giải pháp 2 - dùng JOIN.
- Lý do lựa chọn: API danh sách sinh viên theo khóa học là API đọc dữ liệu,
  khả năng được gọi thường xuyên và số sinh viên mỗi khóa có thể lớn theo thời
  gian; JOIN giúp giảm số câu truy vấn xuống còn 1, tận dụng được index và bộ
  máy tối ưu hóa của MySQL, dễ bảo trì và mở rộng thêm điều kiện lọc sau này.
- Bối cảnh giải pháp vòng lặp còn phù hợp: khi dữ liệu rất nhỏ, logic nghiệp vụ
  phức tạp không thể diễn đạt gọn bằng SQL (ví dụ cần gọi thêm service ngoài
  cho từng sinh viên), hoặc khi ưu tiên code dễ đọc cho người mới hơn hiệu năng.
- Đánh đổi khi chọn JOIN: câu query phức tạp hơn, người đọc code cần hiểu SQLAlchemy
  JOIN/DISTINCT, khó debug từng bước hơn so với vòng lặp thuần Python.

PHẦN 3: THIẾT KẾ VÀ TRIỂN KHAI

6.5. Các bước thực hiện (API GET /courses/{course_id}/students)

    1) Tìm Course theo course_id.
    2) Nếu Course không tồn tại -> trả về 404 Not Found.
    3) JOIN Student với Enrollment theo Enrollment.student_id == Student.id.
    4) Lọc Enrollment.course_id == course_id.
    5) Lọc Enrollment.status in (STUDYING, COMPLETED).
    6) Lọc Student.status == ACTIVE.
    7) Áp DISTINCT theo Student.id để loại sinh viên trùng.
    8) Sắp xếp kết quả theo Student.full_name tăng dần.
    9) Đóng gói kết quả: course_id, course_name, total_students, students.
    10) Trả về 200 OK (danh sách rỗng nếu chưa có sinh viên phù hợp).
"""

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

import schema
import course_service
from database import engine, Base, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Course Students API")


@app.get(
    "/courses/{course_id}/students",
    response_model=schema.CourseStudentsResponse
)
def get_course_students(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = course_service.get_course_by_id(db, course_id)
    students = course_service.get_active_students_of_course(db, course_id)

    return {
        "course_id": course.id,
        "course_name": course.name,
        "total_students": len(students),
        "students": students
    }
