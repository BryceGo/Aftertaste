
from tools.dictionary import DEBUG
def exception_handler(error):
	if DEBUG == True:
		raise error
