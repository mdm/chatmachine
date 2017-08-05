import sys

def readNumber(file):
	number = 0
	for byte in file.read(4):
		number <<= 8
		number += ord(byte)
	return number

blorb = open(sys.argv[1])
basename = sys.argv[1][:sys.argv[1].rfind('.')]
print(basename)

iff_magic = blorb.read(4)
if (iff_magic != 'FORM'):
	print('Not an IFF file.')
	sys.exit(1)

total_size = readNumber(blorb)
print('Total size: ', total_size)

blorb_magic = blorb.read(4)
if (blorb_magic != 'IFRS'):
	print('Not a blorb file.')
	sys.exit(1)

chunk_magic = blorb.read(4)
if (chunk_magic != 'RIdx'):
	print('Resource index not found.')
	sys.exit(1)

chunk_size = readNumber(blorb)
print('Chunk size: ', chunk_size)

num_resources = readNumber(blorb)
print('# resources: ', num_resources)

resources = []
for i in range(num_resources):
	resources.append((blorb.read(4), readNumber(blorb), readNumber(blorb)))

for i in range(num_resources):
	print("Resource %s, %d starts at %d." % resources[i])
	blorb.seek(resources[i][2])
	res_type = blorb.read(4)
	res_length = readNumber(blorb)
	print(i, res_length)
	resource = blorb.read(res_length)
	print(blorb.tell())
	print(res_type)
	print(basename + '_' + str(i) + '.' + res_type.strip().lower())
	outfile = open(basename + '_' + str(i) + '.' + res_type.strip().lower(), 'wb')
	outfile.write(resource)
	outfile.close()

