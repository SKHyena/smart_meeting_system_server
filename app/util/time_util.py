import time

class TimeUtil:
    def __init__(self) -> None:
        pass

    @staticmethod
    def convert_unixtime_to_timestamp(timestamp: int) -> str:
        num_digit = len(str(timestamp))
        digit_diff = 10 - num_digit
        
        timestamp = int((10 ** digit_diff) * timestamp)
        return time.strftime("%y-%m-%d %H:%M:%S", time.localtime(timestamp))
