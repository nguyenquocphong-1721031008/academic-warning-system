class PredictStudentRiskUseCase:
    def __init__(self, student_repo, score_repo, predictor, suggestion_service):
        self.student_repo = student_repo
        self.score_repo = score_repo
        self.predictor = predictor
        self.suggestion_service = suggestion_service

    def execute(self, student_code):
        student = self.student_repo.get_by_code(student_code)

        ai = self.predictor.predict(
            student.gpa, student.failed_subjects, student.total_credits
        )

        scores = self.score_repo.get_by_student(student.id)

        suggestions = self.suggestion_service.suggest_subjects(scores)

        return {
            "student_code": student_code,
            "prediction": "warning" if ai["prediction"] == 1 else "normal",
            "risk_score": ai["risk_score"],
            "risk_level": ai["risk_level"],
            "suggestions": suggestions,
        }
