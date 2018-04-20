import analytics
import uuid
import os

user_id = None
tracking = False

def init_tracking(menu_fn):
  global tracking, user_id
  analytics.write_key = 'xGsvnwEpB4Au5l7gVa6BNjUmgqX9Bp3s'

  if os.path.isfile('analytics_uuid'):
    file = open('analytics_uuid', 'r')
    user_id = file.read()
    file.close()
    tracking = True
  elif not os.path.isfile('analytics_optout'):
    options = [
      'Yes, improve the game based on my use',
      'No, I dont want to be tracked'
    ]
    index = menu_fn('Would you like to share data anonymously?', options, 50)
    if index == 0:
      tracking = True
      file = open('analytics_uuid', 'w')
      user_id = str(uuid.uuid4())
      file.write(user_id)
      file.close()
    else:
      file = open('analytics_optout', 'w')
      file.write('true')
      file.close()

def track(event_name, properties = {}):
  if not tracking:
    return
  analytics.track(user_id, event_name, properties)
