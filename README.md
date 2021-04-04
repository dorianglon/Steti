# Project_BPG

## How To Use

```python
from Run_4_Ever import *

monitor_school('Cornell', university=True, college=False, daily_reports=True)
```

Pass in the subreddit of the school we are monitoring, set university to True if its a uni or college to True if its a cc. And set 
daily_reports to True if you want daily pdfs. If daily_reports is False you will be getting weekly pdfs.
The code above will compile an initial database of redditors from Cornell, then it will scan for new redditors that go to Cornell,
and also scan for news posts made by Cornell redditors. It will then analyze the posts and add on to a daily json file. At 12:00am,
we will receive a pdf report for the last 24 hours.
