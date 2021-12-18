# Actor List Fixer
Edits SharpOcarina's ActorNames.xml file to make it decomp-friendly, the goal is using the generated XML to improve [Fast64](https://github.com/fast-64/fast64)

# Instructions
Place the ``ActorNames.xml`` file from SharpOcarina in the same folder as these files then run 'actorlist-fixer.py'

Note that this is the original file found in SO's XML folder (v1.30), this script changes the structure of the XML file and it renames stuff

# Contributing
I'm not a great Python dev so I'll take anything that can improve my code, I don't have any instructions for contributions as long as it's working properly.

This was done under Python 3.7.3 on Debian (WSL)

# Credits and stuff
Thanks to [Dragorn](https://github.com/Dragorn421/) for this idea

Thanks to whoever made the ``ActorNames.xml`` file

Thanks to the [OoT Decompilation](https://github.com/zeldaret/oot/) for providing the Actor's and Object's lists
