
# GQA-opencog converter

This project aims to convert question-answer pairs from GQA
dataset to semi-logical form, usefull for training language models.

For example question 13481535:
Is the horse on the edge of the water both brown and small?


program from the GQA dataset refers to ground truth elements of the scene graph:

```json
[{"argument": "water (447019)",
 "dependencies": [],
 "operation": "select"},
{"argument": "horse,on the edge of,s (447018)",
 "dependencies": [0],
 "operation": "relate"},
{"argument": "brown",
 "dependencies": [1],
 "operation": "verify color"},
{"argument": "small ",
 "dependencies": [1],
 "operation": "verify size"},
{"argument": "", "dependencies": [2, 3], "operation": "and"}]
```

Converter replaces references to concrete vertices like water (447019) with variables to grounded.  
Many complex relations e.g. on the edge of are split in parts, so result looks like this:
```
verify_color(brown, $Y) and on($Y, $Z) and 
edge_of($Z, $X) and object(horse, $Y) and
object(water, $X) and verify_size(small , $Y)
```

Conjunction has higher priority than disjunction, with this assumption all programs from GQA may be represented without using parentheses for priorities.

**readable** contains programs in the this form. In **spaces** it is the same, but without commas and parentheses.

## Examples  
comparison:

15794418:  Which is less healthy, the hot dog or the tomato?
```
cond(healthier($X, $Y), hot_dog, tomato) and object(tomato, $X) and object(hot_dog, $Y)
```
disjunction:

10245604:  Is the man to the right or to the left of the car that is driving down the street?
```
right_of($Z, $Y) and object(man, $Z) and 
on($Y, $X) and activity(driving, $Y) and 
object(car, $Y) and object(street, $X) or 
left_of($Z, $Y) and object(man, $Z) and 
on($Y, $X) and activity(driving, $Y) and 
object(car, $Y) and object(street, $X)
```
grounding of list:

0493354:  Do the animals have different types?
```different(type, list($X)) and object(animal, list($X))```

```json
[{
		"argument": "animal (1757748, 2007952, 2007953, 2007950, 3781150,1705696, 2680556, 3781148, 2680554, 2680558,1872450, 2007954, 2047186)",
		"dependencies": [],
		"operation": "select"
	},
	{
		"argument": "type",
		"dependencies": [0],
		"operation": "different"
	}
]
```
In this example the program refers to a large number of nodes in the scene graph.
In such cases they are  replaced with list($X).


spliting of complex predicates:

00918539:  What is located on top of the toilet the logo is on the surface of?
```query(name, $E) and on_top_of($E, $Y) and on($X, $Z) and surface_of($Z, $Y) and object(toilet, $Y) and object(logo, $X)
```
here the predicate is 'on the surface of', it is split to ```surface_of($Z, $Y) on($X, $Z)```
### todo

Some complex relations are not split yet:
For example 'running through'. Here 'through' characterizes the action of running, while 'running on' can be split to two predicates.  Here we may understand 'on' as referring to the locations of the someone or something running.  'running on' is replaced with ```activity(running, $X) and on($X, $Z)```



