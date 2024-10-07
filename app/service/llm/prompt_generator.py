class PromptGenerator:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_summarize_prompt(text: str) -> str:
        return f"""
        너는 회의록을 요약해야해. 회의에서 나온 발화는 하단의 json의 list로 주어질거야.
        발화가 이루어진 순서대로 json element가 오름차순으로 정렬되어 있어.
        json 안의 key값들은 timestamp, speaker, text가 들어있어.
        timestamp는 그 발언을 한 시간의 unix time이야. speaker는 회의 참석자 중 한명으로, 해당 발언을 한 사람이야.
        text는 발화자가 말한 text야.
        회의록 json의 시작은 -json-으로 시작하고, 그 하단의 내용을 참조하면 돼.
        
        회의록 요약은 10줄 이하로 작성해줘.
        비속어와 같은 안좋은 말은 절대 적어서는 안되고, 되도록 정중하고 나이스한 표현으로 작성해줘.

        -json-
        {text}
        """
