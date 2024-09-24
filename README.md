# A Calculator with Lark

The grammar in traditional CFG notation is

```
Exp -> Exp '+' Exp1                                
Exp1 -> Exp1 '*' Exp2                              
Exp2 -> Number                                         
Exp2 -> '(' Exp ')'    
Exp -> Exp1                                        
Exp1 -> Exp2
```

Install with
```
source setup.sh
```

Run with, for example,
```
python calculator.py "1+2*3"
```
or with
```
python testing.py
```
where the testing data is in `testing-data.txt`. Add your own test cases.

For debugging, and to understand the role of the transformer, you can print `tree` and the `ast` (but this may interfere with `testing.py`).