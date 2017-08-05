import Skype4Py

def OnOnlineStatus(user, status):
	print('OnlineStatus:', user.Handle, 'is now', status)

def OnUserStatus(status):
	print('Current user is now', status)

skype = Skype4Py.Skype()
skype.FriendlyName = 'Skype_Shell'
skype.Attach()
skype.OnOnlineStatus = OnOnlineStatus
skype.OnUserStatus = OnUserStatus

while(True):
	print('>', end=' ')
	cmd = input()
	cmd = cmd.strip()
	if (cmd == 'exit'):
		break
	scmd = skype.Command(cmd, Block=True)
	skype.SendCommand(scmd)
	result = scmd.Reply
	print(result)

