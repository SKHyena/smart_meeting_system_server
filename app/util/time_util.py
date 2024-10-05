from datetime import datetime, timezone, timedelta


class TimeUtil:
    def __init__(self) -> None:
        pass

    @staticmethod
    def convert_unixtime_to_timestamp(timestamp: int) -> str:
        num_digit = len(str(timestamp))
        digit_diff = 10 - num_digit
        
        timestamp = int((10 ** digit_diff) * timestamp)
        tz = timezone(+timedelta(hours=9))
            
        return datetime.fromtimestamp(timestamp, tz).strftime("%y-%m-%d %H:%M:%S")
