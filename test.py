from gen_news import GenerateNewsSQL

gen = GenerateNewsSQL()

#gen.create_story(title="Hello", author="Hrlle", content="Hello", tags="hello")
x = gen.parse_news()

print(x)
