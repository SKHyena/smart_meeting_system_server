class PromptGenerator:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_summarize_prompt(text: str) -> str:
        return f"""
        너는 민원인과 상담자와의 대화를 요약해야해. 대화는 하단의 json의 list로 주어질거야.
        대화가 이루어진 순서대로 json element의 순서가 배열되어있어.
        json 안의 key값들은 timestamp, speaker, text가 들어있어.
        timestamp는 그 대화를 한 시간의 unix time이야. speaker는 그 대화를 한 사람이야. counselor와 complainant라고 적혀있고, counselor는 상담자고 complainant는 민원인이야.
        text는 발화자가 말한 text야.
        대화 json의 시작은 -json-으로 시작하고, 그 하단의 내용을 참조하면 돼.
        
        대화 요약은 2줄 이하로 작성해줘.
        비속어와 같은 안좋은 말은 절대 적어서는 안되고, 되도록 정중하고 나이스한 표현으로 작성해줘.

        -json-
        {text}
        """

    @staticmethod
    def get_categorize_prompt(text: str) -> str:
        return f"""
        너는 민원인과 상담자와의 대화의 종류를 분류해야해. 대화는 하단의 json의 list로 주어질거야.
        대화가 이루어진 순서대로 json element의 순서가 배열되어있어.
        json 안의 key값들은 timestamp, speaker, text가 들어있어.
        timestamp는 그 대화를 한 시간의 unix time이야. speaker는 그 대화를 한 사람이야. counselor와 complainant라고 적혀있고, counselor는 상담자고 complainant는 민원인이야.
        text는 발화자가 말한 text야.

        대화를 분류할 주제는 총 9가지로 다음과 같아.
        비자, 노무, 교육, 의료, 거주, 취업, 창업, 혼인, 법률, 기타
        위 10가지 주제로 대화를 분류해야하며, 이 외의 주제를 절대로 적어서는 안돼.
        답변은 위에 적혀있는 10가지 단어 외에 아무것도 안나오게 해줘. 특수 문자는 반드시 제거해줘.

        -json-
        {text}
        """
