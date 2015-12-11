import sys
import getopt

def main(argv):
	infname = 'fem.raw'
	outfname = 'fem.c'
	rowlen = 10
	datalen = 2
	signed = 1
	base = 16
	
	infile = open(infname, 'rb')
	outfile = open(outfname, 'w')
	
	col = 0
	
	bstr = infile.read(2)
	while (len(bstr) > 0):
		data = bstr[0] + (bstr[1] << 8)
		if (base == 16):
			outfile.write(str.format('0x{0:04x},', data))
		if (base == 10):
			if (signed == 1):
				if (data > pow(2, datalen * 8 - 1)):
					data = data - pow(2, datalen * 8)
			outfile.write(str.format('{0},', data))
		col = col + 1
		if (col >= rowlen):
			outfile.write('\n')
			col = 0
		else:
			outfile.write(' ')
		bstr = infile.read(2)
	
	infile.close()
	outfile.close()

if __name__ == "__main__":
	main(sys.argv[1:])

# vim: set ft=python ts=4 sts=4 sw=4 ai noexpandtab :
