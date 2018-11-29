from Crypto.Hash import MD5, SHA256
from Crypto.Cipher import AES
from Crypto.Random import random

#Encryption and decryption needs to have encoded input
class cipher:
	def __init__(self,key,IV,generatedIV=False):
		h = SHA256.new()
		h.update(key.encode())
		self.key = h.digest()
		if not(generatedIV):
			h = MD5.new()
			h.update(IV.encode())
			self.IV = h.digest()
		else:
			self.IV = IV

	def _pad(self,text):
		_padVar = AES.block_size - (len(text) % AES.block_size)
		return text + (_padVar * chr(_padVar).encode())

	def _unpad(self,text):
		return text[:-ord(text[len(text)-1:])]

	def encrypt(self,plaintext, IV=None):
		if IV!=None:
			self.IV = IV
		plaintext = self._pad(plaintext)
		obj = AES.new(self.key,AES.MODE_CBC, self.IV)
		return obj.encrypt(plaintext)

	def decrypt(self,ciphertext, IV=None):
		if IV!=None:
			self.IV = IV
		obj = AES.new(self.key,AES.MODE_CBC,self.IV)
		plaintext = obj.decrypt(ciphertext)
		return self._unpad(plaintext)

def generateIV():
	hash = MD5.new()
	randomNumber = random.getrandbits(AES.block_size*8)
	hash.update(str(randomNumber).encode())
	return hash.digest()