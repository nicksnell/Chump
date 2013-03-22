from chump import RegionParser

def main(html):
	#parser = RegionParser(tags=['body'],attributes=['data-deploycms'],strict_id=False)
	
	parser = RegionParser(
		tags=['div', 'header', 'footer', 'article', 'aside'],
		classes=['edit-local']
	)
	
	parser.parse(html)
	
	for region in parser:
		#region.set_content('foo')
		print region.id
		
	#print unicode(parser)

def bs_test(html):
	from BeautifulSoup import BeautifulSoup
	
	soup = BeautifulSoup(html)

	# Find the node to replace
	nodes = soup.findAll('div')
	
	for n in nodes:
		print n['id']
	
	
if __name__ == '__main__':
	html = open('example.html', 'r').read().decode('utf8')
	main(html)
	#bs_test(html)
