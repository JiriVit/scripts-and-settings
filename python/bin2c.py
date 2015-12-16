import sys
import getopt

def bin2c(in_filename, out_filename, wordlen, base, signed, columns):
	infile = open(in_filename, 'rb')
	outfile = open(out_filename, 'w')
	
	col = 0
	
	bstr = infile.read(wordlen)
	while (len(bstr) > 0):
		data = bstr[0] + (bstr[1] << 8)
		if (base == 16):
			outfile.write(str.format('0x{0:04x},', data))
		if (base == 10):
			if (signed == 1):
				if (data > pow(2, wordlen * 8 - 1)):
					data = data - pow(2, wordlen * 8)
			outfile.write(str.format('{0},', data))
		col = col + 1
		if (col >= columns):
			outfile.write('\n')
			col = 0
		else:
			outfile.write(' ')
		bstr = infile.read(2)
	
	infile.close()
	outfile.close()

def usage():
	print("bin2c -i <input_file> -o <output_file> -w <word_len> -b <base> -c <columns> -s")

def main(argv):
	infn = 'data.bin'
	outfn = 'data.txt'
	columns = 10
	wordlen = 2
	signed = 0

	try:
		opts, args = getopt.getopt(argv, "hi:o:w:c:b:s", [])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			usage()
			sys.exit()
		elif opt == '-i':
			infn = arg
		elif opt == '-o':
			outfn = arg
		elif opt == '-c':
			columns = int(arg)
		elif opt == '-w':
			wordlen = int(arg)
			if (wordlen != 2):
				print('error: only wordlen = 2 supported')
				sys.exit(2)
		elif opt == '-b':
			base = int(arg)
			if ((base != 10) and (base != 16)):
				print("error: base " + base + " not supported")
				sys.exit(2)
		elif opt == '-s':
			signed = 1

	bin2c(infn, outfn, wordlen, base, signed, columns)

if __name__ == "__main__":
	main(sys.argv[1:])

# vim: set ft=python ts=4 sts=4 sw=4 ai noexpandtab :
