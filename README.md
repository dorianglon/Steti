# Project_BPG

## How To Use

```python
from Run_4_Ever import *

monitor_school('Cornell', university=True, college=False)
```

Pass in the subreddit of the school we are monitoring, set university to True if its a uni or college to True if its a cc.
The code above will compile an initial database of redditors from Cornell, then it will scan for new redditors that go to Cornell,
and also scan for news posts made by Cornell redditors. It will then analyze the posts and add on to a daily json file. After each iteration of checking the new posts and comments (approx 30 minutes) the pdf for that day will update itself.
