from Crypto.Hash import MD5, SHA256
from Crypto.Cipher import AES

class cipher:
	def __init__(self,key,IV):
		h = SHA256.new()
		h.update(key.encode())
		self.key = h.digest()

		h = MD5.new()
		h.update(IV.encode())
		self.IV = h.digest()

	def encrypt(self,plaintext):
		obj = AES.new(self.key,AES.MODE_CBC, self.IV)
		return obj.encrypt(plaintext)

	def decrypt(self,ciphertext):
		obj = AES.new(self.key,AES.MODE_CBC,self.IV)
		return obj.decrypt(ciphertext)