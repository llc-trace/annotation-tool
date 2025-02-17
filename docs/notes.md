# Notes on further developing the annotation tool


### Adding Gesture annotation

Taken from  Multimodal\_AMR\_Annotation\_Guidelines\_20220914.pdf:

There are three kinds of gestures:

| gesture  | description |
| :------- | :----------- |
| Iconic   | Gestures that model the shape of an object or the motion of an action. |
| Deictic  | Refers to familiar pointing, indicating objects in conversational space. |
| Emblem   | Gestures with standard properties and language-like features. |

Examples:

- a speaker arcs his/her fist to form a cup and drink from it when saying ‘I drink from a cup’ (iconic)
- a speaker says ‘I walked up the stairs’, he/she points upward (deictic)
- the OK sign has a culturally agreed upon meaning; and it is necessary to place the thumb and index finger together in order to form the sign (emblem)

Gestures have an canonical template:

```
(g / [gesture]-GA
  :ARG0 (s / signaler)
  :ARG1 [content]
  :ARG2 (a / actor))
```

ARG0 and ARG2 correspond to the gesturer and addressee. ARG1, the semantic content of the gesture, varies by gesture type.

| gesture         | ARG1        |
| :-------------- | :---------- |
| Iconic gesture  | The object or action being modeled. |
| Deictic gesture | The object or location being pointed to. |
| Emblem          | The conventional, culturally agreed- upon meaning of the gesture. |



### Generalizing action annotation

```
open(Sally, box) -> Sally opened the box.
put(Sally, marble, box) -> Sally put the marble in the box.
close(Sally, box) -> Sally closed the box.
leave(Sally,room) -> Sally left the room.
open(Anne, box) -> Anne opened the box.
move(Anne, marble,box,basket) -> Anne moved the marble from the box to the basket.
close(Anne,box) -> Anne closed the box.
return(Sally,room)-> Sally returned to the room.
open(Sally, box) -> Sally opened the box.
```