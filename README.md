Made for python 3.X
assumes sentistrength is available in the current folder, 
i.e.: the folder contains `SentiStrengthCom.jar`. 
The language files should be in folders with 2-letter ISO 
language codes. 

 - AR = Arabic
 - CY = Welsh 
 - DE = German
 - EL = Greek
 - EN = English
 - FA = Persian
 - FR = French
 - IL = Italian
 - NL = Dutch
 - PL = Polish
 - PT = Portuguese
 - RU = Russian
 - SP = Spanish
 - SW = Swedish
 - TU = Turkish

Current language sets (except EN) drawn from https://github.com/felipebravom/StaticTwitterSent/tree/master/extra/SentiStrength

**Sentistrength java file can be obtained from sentistrength.wlv.ac.uk/ by emailing Professor Thelwall (address on website)**

Example use (single-core client):

```python
>>> from senti_client import sentistrength
>>> senti = sentistrength('EN')
>>> res = senti.get_sentiment('I love using sentistrength!')
>>> print(res)

... {'negative': '-1', 'neutral': '1', 'positive': '4'}
```


Example use (multi-core client):

```python
>>> from senti_client import multisent
>>> ms    = multisent('EN')
>>> texts = ['This is great!!'] * 10000
>>> res   = ms.run_stream(texts)
>>> print(res[0])

... {'negative': '-1', 'neutral': '1', 'positive': '4'}
```

Enjoy!

