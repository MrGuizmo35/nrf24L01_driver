import spidev
import time
import RPi.GPIO as GPIO

def PrintSpiResp(resp):
	print '[{}]'.format(', '.join(hex(x) for x in resp))

GPIO.setmode(GPIO.BCM)
GPIO.setup(24,GPIO.IN)
GPIO.setup(18,GPIO.OUT)

print(GPIO.input(24))

GPIO.output(18,GPIO.HIGH)
time.sleep(0.1)
GPIO.output(18,GPIO.LOW)

spi = spidev.SpiDev()
spi.open(0,0)
try:
	while True:
		toSend = [0x0A,0xFF,0xFF,0xFF,0xFF,0xFF]
		resp = spi.xfer2(toSend)
		PrintSpiResp(resp)
		time.sleep(0.1)
		toSend = [0x0B,0xFF,0xFF,0xFF,0xFF,0xFF]
		resp = spi.xfer2(toSend)
		PrintSpiResp(resp)
		time.sleep(0.1)
except KeyboardInterrupt:
	spi.close()
	GPIO.cleanup()
	print('\r\n\r\n')


	

