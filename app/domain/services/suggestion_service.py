class SuggestionService:
    def suggest_subjects(self, scores):
        failed = [s for s in scores if s.score < 4]
        low = [s for s in scores if 4 <= s.score < 5]

        result = []

        for s in failed:
            result.append({"subject": s.subject_name, "reason": f"Rớt môn ({s.score})"})

        for s in low:
            result.append(
                {"subject": s.subject_name, "reason": f"Điểm thấp ({s.score})"}
            )

        return result[:3]
