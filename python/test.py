from pykakasi import kakasi

kks = kakasi()
text = u"かな漢字交じり文"
result = kks.convert(text)

x = [x['hepburn'] for x in result]
x = ' '.join(x)

print(x.capitalize())