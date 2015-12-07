infname = 'fem.raw'
outfname = 'fem.c'

infile = open(infname, 'rb')
outfile = open(outfname, 'w')

bstr = infile.read(2)
while (len(bstr) > 0):
	data = bstr[0] + (bstr[1] << 8)
	outfile.write(str.format('0x{0:04x},\n', data))
	bstr = infile.read(2)

infile.close()
outfile.close()

# vim: set ft=python ts=4 sts=4 sw=4 ai noexpandtab :
