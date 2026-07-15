from typing import List

from pydantic import BaseModel, ConfigDict


class StudentBrief(BaseModel):
    id: int
    full_name: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class CourseStudentsResponse(BaseModel):
    course_id: int
    course_name: str
    total_students: int
    students: List[StudentBrief]
