from fastapi import HTTPException
from sqlalchemy.orm import Session

import models

VALID_ENROLLMENT_STATUSES = ["STUDYING", "COMPLETED"]


def get_course_by_id(db: Session, course_id: int) -> models.Course:
    course = (
        db.query(models.Course)
        .filter(models.Course.id == course_id)
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Khóa học không tồn tại"
        )

    return course


def get_active_students_of_course(db: Session, course_id: int) -> list:
    return (
        db.query(models.Student)
        .join(models.Enrollment, models.Enrollment.student_id == models.Student.id)
        .filter(
            models.Enrollment.course_id == course_id,
            models.Enrollment.status.in_(VALID_ENROLLMENT_STATUSES),
            models.Student.status == "ACTIVE"
        )
        .distinct()
        .order_by(models.Student.full_name.asc())
        .all()
    )
