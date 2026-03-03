from markitdown import MarkItDown
import tempfile

with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
    f.write("<html><body><h1>Hello World</h1><p>Test</p></body></html>")
    name = f.name

md = MarkItDown()
print(md.convert(name).text_content)
