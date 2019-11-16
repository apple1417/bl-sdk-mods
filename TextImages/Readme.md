### Text Images
This is a bad idea.

![](https://cdn.discordapp.com/attachments/288382606288879629/644102834803048448/unknown.png)

Using font tags you can colour text any of the normal 256^3 colours.    
You can also resize it to something small to let you fit more colours.    
If you display text in an invalid font then all characters will be displayed as the same "invalid character" character, which'll be (somewhat) monospaced.



So the obvious course of action is to create an image using one invalid character per pixel.

Of course having the game render several megabytes of text is a tad laggy.

#### gen.py
This is not an sdk script. Requires Pillow which the sdk doesn't seem to want to load. Generates the text to draw a specified image, perfectly fitting into a training box.

Could certainly be optimized more but it's not like this is useful in the first place.

#### show.py
A super simple example of how you can display one of these images, doesn't actually do any work.
