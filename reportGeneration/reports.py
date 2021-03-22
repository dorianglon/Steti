import jinja2
import pdflatex
import os

data = {
	'name': 'Cornell',
	'dateRange': '3/11/2021 - 3/18/2021',
	'users': [
        {
		    'username': 'abc',
		    'severity': 9,
		    'comment': 'goodbye forever'
        },
        {
		    'username': 'zdfaf',
		    'severity': 6,
		    'comment': 'fuck this cruel world'
        },
        {
		    'username': 'yurt',
		    'severity': 8,
		    'comment': 'lol i wanna kms'
        }
	]
}

env = pdflatex.JINJA2_ENV
env['loader'] = jinja2.FileSystemLoader(os.path.abspath('.'))
env = jinja2.Environment(**env)
template = env.get_template('template.tex')

print(vars(pdflatex.PDFLaTeX))
pdfl = pdflatex.PDFLaTeX.from_jinja_template(template, data)
# print(vars(pdfl))
pdf, log, cp = pdfl.create_pdf()

# template = open('template.tex', 'r').read()
# print(template)
# template = Template(template)
# res = template.render(data)
# print(res)


# actual example:
# {
#  "institution": "Cornell",
#  "month": "March",
#  "day": 21,
#  "users": [
#   {
#    "username": "redditor_username",
#    "neg_posts": [
#     [
#      "I want to kms",
#      1600000000,
#      "SuicideWatch",
#      99
#     ],
#     [
#      "KMS",
#      1600000000,
#      "Cornell",
#      91
#     ]
#    ]
#   }
#  ]
# }