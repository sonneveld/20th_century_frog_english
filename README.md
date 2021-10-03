# 20th Century Frog English Patch

## What is 20th Century Frog

A DOS game from 1988 where you control a frog. There is a unique control
scheme that requires the use of every letter and number on the keyboard.


## The Patch

Open the .exe in ida pro, identify all strings, and save an .idc file.
This will be used to extract offsets and create a .csv file.

Edit the .csv file, adding an extra column with English translations.
Leave any you don't want to translate as "TODO" or remove the line

Originally the patch simply replaced strings with English equivalents
but unfortunately because of how the strings are packed within the .exe,
they could not go outside the original length, which led to some 
truncated strings.

The new version of the patch essentially identifies and pulls apart the
original segments, and adds the longer strings to the end, adjusting the
code to refer to the new position. This seems to work correctly for the
strings that were too long but might not work for all cases.


## Translating Tips

Two sites are very useful:

 - Google Translate : https://translate.google.com/?sl=de&tl=en&op=translate
 - DeepL Translator : https://www.deepl.com/en/translator

You need to be mindful of how you paste in text. Google Translate will
treat new lines as separate sentences, so you may get better results if
you join the text to the translated so it is all on one line.

Some words refer to German brands, so I tried to map to equivalents:
 - "SAT 1" : a German private tv broadcaster -> "David Attenborough Presents..."
 - "infas" : a German statistics organisation -> "Bureau of Statistics"
 - "Steppenbrand" : literally translates to "steppe fire" which is like a grass fire -> "Grass Fire"
 - "frisch frosch fröhlich frei" : title of a racey book, different title in English -> "The Joy of Frogs"
