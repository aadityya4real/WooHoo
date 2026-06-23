# apply_tracker.py
# exec(open('scripts/apply_tracker.py').read())
# Pushes the new hand_tracker.py code into TD's callback DAT

code = open(project.folder + '/scripts/hand_tracker.py').read()
fixed = 0
for dat in root.findChildren(type=textDAT):
    if 'hand_tracker' in dat.name.lower() and 'callback' in dat.name.lower():
        dat.text = code
        dat.par.syncfile = False
        print('Updated:', dat.path)
        fixed += 1
if fixed == 0:
    print('No hand_tracker callback DAT found!')
else:
    print('Done. Check Textport for MediaPipe Hands initialized OK')
