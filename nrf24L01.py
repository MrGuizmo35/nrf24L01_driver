import spidev
import time
import RPi.GPIO as GPIO

class nrf24L01():
	def __init__(self,csn,ce,irq):
		self.CSNpin = csn
		self.CEpin = ce
		self.IRQpin = irq
		GPIO.setup(self.IRQpin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.CEpin,GPIO.OUT)
		GPIO.output(self.CEpin,GPIO.LOW)
		self.spi = spidev.SpiDev()

	def Open(self):
		self.spi.open(0,self.CSNpin)
		self.spi.bits_per_word = 8
		self.spi.max_speed_hz = 10000000
		self.spi.cshigh = False
		self.spi.mode = 0
		self.spi.loop = False
		self.spi.lsbfirst = False
		self.spi.threewire = False

	def Close(self):
		self.spi.close()
		GPIO.cleanup()

	def GetStatus(self):
		[status] = self.spi.xfer2([0xFF])
		return status

	def ClearStatus(self):
		self.spi.xfer2([0x27,0x70])

	def PowerDown(self):
		[status,config] = self.spi.xfer2([0x00,0xFF])
		config = config & 0xFD
		self.spi.xfer2([0x20,config])

	def PowerUp(self):
		[status,config] = self.spi.xfer2([0x00,0xFF])
		config = config | 0x02
		self.spi.xfer2([0x20,config])

	def SetPRX(self):
		[status,config] = self.spi.xfer2([0x00,0xFF])
		config = config | 0x01;
		self.spi.xfer2([0x20,config])

	def SetPTX(self):
		[status,config] = self.spi.xfer2([0x00,0xFF])
		config = config & 0xFE
		self.spi.xfer2([0x20,config])

	def EnableRxAddr(self,pipe):
		[status,Enabled] = self.spi.xfer([0x02,0xFF])
		Enabled = Enabled | (1 << pipe)
		self.spi.xfer([0x22,Enabled])

	def DisableRxAddr(self,pipe):
		[status,Enabled] = self.spi.xfer([0x02,0xFF])
		Enabled = Enabled & ~(1 << pipe)
		self.spi.xfer([0x22,Enabled])

	def EnableAutoAck(self,pipe):
		[status,Enabled] = self.spi.xfer([0x01,0xFF])
		Enabled = Enabled | (1 << pipe)
		self.spi.xfer([0x21,Enabled])

	def DisableAutoAck(self,pipe):
		[status,Enabled] = self.spi.xfer([0x01,0xFF])
		Enabled = Enabled & ~(1 << pipe)
		self.spi.xfer([0x21,Enabled])

	def GetTxAddr(self):
		resp = self.spi.xfer2([0x10,0xFF,0xFF,0xFF,0xFF,0xFF])
		txAddr = resp[1:]
		return txAddr

	def GetRxAddr(self,pipe):
		if(pipe < 2):
			resp = self.spi.xfer2([0x0A + pipe, 0xFF, 0xFF, 0XFF, 0xFF, 0xFF])
			rxAddr = resp[1:]
		else:
			resp = self.spi.xfer2([0x0B, 0xFF, 0xFF, 0XFF, 0xFF, 0xFF])
			[status,r1] = self.spi.xfer2([0X0A + pipe, 0xFF]) 
			rxAddr = resp[1:-1]
			rxAddr.append(r1)
		return rxAddr
	
	def SetTxAddr(self, txAddr):
		toSend = [0x20 + 0x10]
		toSend = toSend + txAddr
		self.spi.xfer2(toSend)

	def SetRxAddr(self,pipe,rxAddr):
		if(pipe < 2):
			toSend = [0x2A + pipe]
			toSend = toSend + rxAddr
			self.spi.xfer2(toSend)
		else:
			toSend = [0x2A+pipe,rxAddr[0]]
			self.spi.xfer2(toSend)

	def IrqIsSet(self):
		return not GPIO.input(self.IRQpin)

	def FlushTx(self):
		self.spi.xfer2([0xE1])

	def FlushRx(self):
		self.spi.xfer2([0xE2])

	def SetRxPayloadWidth(self,pipe,width):
		if(width > 32):
			width = 32
		if(pipe > 5):
			pipe = 5
		self.spi.xfer2([0x31+pipe,width])

	def ReadRxPayloadWidth(self):
		[status,width] = self.spi.xfer2([0x60,0xFF])
		return width

	def ReadRxPayload(self,width):
		toSend = [0x61]
		for i in range(width):
			toSend.append(0xFF)
		resp = self.spi.xfer2(toSend)
		return resp[1:]

	def SetActiveMode(self):
		GPIO.output(self.CEpin,GPIO.HIGH)

	def ResetActiveMode(self):
		GPIO.output(self.CEpin,GPIO.LOW)
	
	def SetDataRate(self,dataRate):
		[status,rfSetup] = self.spi.xfer2([0x06,0xFF])
		rfSetup = rfSetup & 0xD7
		if dataRate == '1MBPS':
			rfSetup == rfSetup | 0
		elif dataRate == '2MBPS':
			rfSetup == rfSetup | 0x08
		elif dataRate == '250KBPS':
			rfSetup = rfSetup | 0x20
		[status,dummy] = self.spi.xfer2([0x26,rfSetup])
		return status

	def SetRFChannel(self,channel):
		self.spi.xfer2([0x25,channel])

	def GetRFChannel(self):
		[status,channel] = self.spi.xfer2([0x05,0xFF])
		return channel

	def SetRetransmit(self,ard_us,arc):
		d = {}
		for i in range(16):
			d[250*(i+1)] = i << 4
		k = min(d, key=lambda x:abs(x-ard_us))
		if arc > 15:
			arc = 15
		retr = d[k] | arc
		self.spi.xfer2([0x24,retr])

	def ResetAllReg(self):
		self.spi.xfer2([0x20,0x08])
		self.spi.xfer2([0x21,0x3F])
		self.spi.xfer2([0x22,0x03])
		self.spi.xfer2([0x23,0x03])
		self.spi.xfer2([0x24,0x03])
		self.spi.xfer2([0x25,0x02])
		self.spi.xfer2([0x26,0x08])
		self.spi.xfer2([0x27,0x70])
		self.spi.xfer2([0x2A,0xE7,0xE7,0xE7,0xE7,0xE7])
		self.spi.xfer2([0x2B,0xC2,0xC2,0xC2,0xC2,0xC2])
		self.spi.xfer2([0x2C,0xC3])
		self.spi.xfer2([0x2D,0xC4])
		self.spi.xfer2([0x2E,0xC5])
		self.spi.xfer2([0x2F,0xC6])
		self.spi.xfer2([0x30,0xE7,0xE7,0xE7,0xE7,0xE7])
		self.spi.xfer2([0x31,0x00])
		self.spi.xfer2([0x32,0x00])
		self.spi.xfer2([0x33,0x00])
		self.spi.xfer2([0x34,0x00])
		self.spi.xfer2([0x35,0x00])
		self.spi.xfer2([0x36,0x00])
		self.spi.xfer2([0x3C,0x00])
		self.spi.xfer2([0x3D,0x00])

	def PrintListHex(resp):
		print '[{}]'.format(', '.join(hex(x) for x in resp))
	PrintListHex = staticmethod(PrintListHex)

if __name__ == "__main__":
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(18,GPIO.OUT)

	GPIO.output(18,GPIO.HIGH)

	nrf = nrf24L01(0,25,24)
	nrf.Open()
	nrf.ResetAllReg()
#	nrf.SetRxAddr(1,[0,1,2,3,12 ])
#	nrf.SetRxAddr(5,[4])
#	nrf.EnableRxAddr(5)
#	nrf.EnableAutoAck(5)
#	for i in range (0,4):
#		nrf.DisableRxAddr(i)
#		nrf.DisableAutoAck(i)
	
	#nrf.SetTxAddr([4,3,2,1,0])
	rxAddr = nrf.GetRxAddr(0)
	print("RX0 Addr:")
	nrf.PrintListHex(rxAddr)
#	print("TX Addr:")
#	txAddr = nrf.GetTxAddr()
#	nrf.PrintListHex(txAddr)
	nrf.FlushRx()
	
	nrf.SetRxPayloadWidth(0,32)
	nrf.SetRFChannel(40)
	print('RF channel: ')
	print(nrf.GetRFChannel())
	nrf.SetDataRate('1MBPS')
	nrf.SetRetransmit(4000,15)
	nrf.SetPRX()
	nrf.PowerUp()
	time.sleep(0.1)
	nrf.SetActiveMode()
	try:
		while(True):
			#print("Status: " + hex(nrf.GetStatus()))
			#print(nrf.IrqIsSet())
			if(not nrf.IrqIsSet()):
				GPIO.output(18,GPIO.HIGH)
			else:
				GPIO.output(18,GPIO.LOW)
				nrf.ResetActiveMode()
				print("Status: " + hex(nrf.GetStatus()))
				width = nrf.ReadRxPayloadWidth()
				print("Rx payload width = "+str(width))
				if(width > 0):
					rxPayload = nrf.ReadRxPayload(width)
					print(''.join(chr(x) for x in rxPayload))
				nrf.ClearStatus()
				nrf.FlushRx()
				nrf.SetActiveMode()
	except KeyboardInterrupt:
		GPIO.output(18,GPIO.LOW)
		nrf.Close()
		print("\r")
