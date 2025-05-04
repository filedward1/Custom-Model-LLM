import pymupdf
doc = pymupdf.open('MODULE5.pdf')
text = ""

for page in doc:
   text+=page.get_text()
# print(text)