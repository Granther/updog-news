# from gen_news import GenerateNewsSQL

# gen = GenerateNewsSQL()

# gen.create_story(title="Hello", author="Hrlle", content="Hello", tags="hello")
# x = gen.parse_news()
# print(gen._is_archived("3pr5xNjKzt2HkLLzM63hRW"))

# from infer import perform_search

# perform_search("Donald trump is a dog", n_results=3)

from reporters import ReportersSQL

auth = ReportersSQL()

print(auth.parse_reporters())