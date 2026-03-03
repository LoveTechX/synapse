import os, time
from core.realtime_monitor import SmartHandler
from ui.preview_mode import preview_mode as pm

pm.enable()
handler = SmartHandler()

# create test file
test_path = r'D:\TEST_AI\input\test_keyword_assignment.txt'
with open(test_path,'w') as f:
    f.write('This is an assignment for dbms and os topics.')

print('Processing file', test_path)
handler.process(test_path)
print('Preview queue entries:')
for e in pm.preview_queue:
    print(e)

