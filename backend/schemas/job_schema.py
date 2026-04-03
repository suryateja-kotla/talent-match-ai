from pydantic import BaseModel, Field, AliasChoices, field_validator
from typing import List, Optional

class JobPostingSchema(BaseModel):
    # AliasChoices looks for the snake_case version first, then the camelCase
    jobTitle: str = Field(
        validation_alias=AliasChoices("job_title", "jobTitle"),
        description="The official title of the position"
    )
    department: Optional[str] = Field(
        validation_alias=AliasChoices("department", "dept"),
        description="The department or team name"
    )
    location: str = Field(
        description="City, State or Remote/Hybrid status"
    )
    jobType: Optional[str] = Field(
        validation_alias=AliasChoices("job_type", "jobType"),
        description="Full-time, Part-time, or Contract"
    )
    experienceRequired: str = Field(
        validation_alias=AliasChoices("experience_required", "experienceRequired"),
        description="Years or level of experience needed"
    )
    technicalSkills: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("technical_skills", "technicalSkills"),
        description="List of required technical competencies"
    )

    @field_validator("technicalSkills", mode="before")
    @classmethod
    def ensure_list(cls, v):
        """
        Catches strings like 'Java, Selenium' and converts them to ['Java', 'Selenium']
        before Pydantic throws a validation error.
        """
        if isinstance(v, str):
            # Split by comma and remove extra whitespace
            return [skill.strip() for skill in v.split(",") if skill.strip()]
        return v