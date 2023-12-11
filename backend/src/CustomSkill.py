from OpenAIHandler import OpenAI
from model.input import OpenAIConfig, CustomSkillContentIn
from model.output import CustomSkillContentOut
from model.common import CustomSkillContentDataOut, CustomSkillContentRecordOut
from OpenAIHandler import OpenAI


class OpenAICustomSkill(OpenAI):
    def __init__(self, config: OpenAIConfig) -> None:
        super().__init__(config=config)
        
    def question_gen_skill(self, input: CustomSkillContentIn):
        try:
            result = []
            for record in input.values:
                questions = self.generate_question(paragrpah=record.data.text)
                result.append({
                    "recordId": record.recordId,
                    "data": {
                        "questions": questions
                    }
                })
            return result
        except Exception as err:  # TODO: handle this
            print(err)
            raise err
        
    def summary_skill(self, input: CustomSkillContentIn):
        try:
            result = []
            for record in input.values:
                questions = self.summarize_text(paragrpah=record.data.text)
                result.append({
                    "recordId": record.recordId,
                    "data": {
                        "summary": questions
                    }
                })
            return result
        except Exception as err:  # TODO: handle this
            print(err)
            raise err