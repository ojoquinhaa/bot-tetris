import datetime
import json
start_time = datetime.datetime.strptime("17:30", "%H:%M")
end_time = datetime.datetime.strptime("18:00", "%H:%M")
time_interval = datetime.timedelta(minutes=1)

result_array = []

current_time = start_time
while current_time <= end_time:
    formatted_time = current_time.strftime("%H:%M")
    signal = f"M5;AUDJPY;{formatted_time};CALL"
    result_array.append(signal)
    current_time += time_interval


with open('signals.txt', 'w+') as f:
    f.write('\n'.join(result_array))