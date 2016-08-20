## natural_money

Find and convert money amounts in text.

```python
from natural_money import Finder
mf = Finder()
mf.findall("500 EUR $500 and five hundred yen")
# [Money(value=500.0, currency='EUR', matches=['500', 'EUR'], base_amount=500.0, base='EUR', ...),
#  Money(value=500.0, currency='USD', matches=['$', '500'], base_amount=441.462, base='EUR', ...)
#  Money(value=500.0, currency='JPY', matches=['five', 'hundred', 'yen'], base_amount=4.404, ...)]
```

Takes clues to solve ambiguity:

```python
mf.find("In Australia, 500 dollars recently became worth less")
# Money(value=500.0, currency='AUD', matches=['Australia', '500', 'dollars'], base='EUR', base_amount=336.089, ...)
```

## Install

Tested for 2.7 and 3.5:

    pip install natural_money

## Features

- **base_currency**: can be changed using `Finder(base_currency="USD")`
- **conversion_backend**: can use different websites as backends: `Finder(converter=MyClass)`
- **locale**: create your own locales with different behavior
- **thread-safe caching**: can implement different caching schedule: `Finder(converter=MyClass)`
    - Currently implements hourly updates and stores locally in sqlite3
- **ignore_conversions**: `Finder(converter=None)`
- **numeric_to_money**: Force numbers to become money if you know there has to be money mentioned:

> Bot: "How much local money would you like to spend?"

> Answer: "I would not spend more than 500"

```python
mf.find("I would not spend more than 500", numeric_to_money=True)
# Money(value=500.0, currency='EUR', spans=[(28, 31)], matches=['500'], base='EUR', ...)
```

- **accurate**: no false hits:

```python
mf.find("I want to buy 500 apples.")
# None
```


## Contributing

Yes please. There are multiple ways you could help:

1. Implement new functionality, pull requests are very welcome
2. Create a new locale for your language
3. Identify cases that don't work and you think should work, pick one:
    1. Make an issue describing what doesn't work
    2. Make a pull request with an newly added test that does not pass
    3. Make a pull request with a newly added test including a FIX :)
