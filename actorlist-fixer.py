import xml.etree.ElementTree as ET, xml.dom.minidom as MD
from sys import exit

try:
    from lists import actors as actorID, objects as objectID, categories as actorCat, objectsNames as objectNames, checkBox, \
        ootEnWonderItemDrop as wonderList, ootEnItem00Drop as item00List, ootEnBoxContent as chestList, subscribe
except:
    print("ERROR: File 'lists.py' is missing. You can find it on Github: https://github.com/Yanis42/actorlist-fixer")
    exit()

try:
    tree = ET.parse('./ActorNames.xml')
except:
    print("ERROR: File 'ActorNames.xml' is missing. You can find it in SO's (1.28) XML folder.")
    exit()

root = tree.getroot()

# --- Process the original file's elements --- #

# Determines how many 0 is needed to get the correct Actor/Object ID from the dictionary
def getIDNumber(i):
    '''Returns a string containing the proper amount of 0 (hex)'''
    if i < 16:
        string = '000'
    elif i > 15 and i < 256:
        string = '00'
    else:
        string = '0'
    string += f'{i:X}'

    return string

# Process Actor IDs
print("INFO: Processing Actor IDs...")

i = 0
for i in range(len(actorID)):
    idNumber = getIDNumber(i)
    for actorNode in root:
        if actorNode.get('Key') == idNumber:
            actorNode.set('ID', actorID.get(idNumber))
            actorNode.set('Name', (actorNode.get('Name') + ' - ' + actorNode.get('ID').replace('ACTOR_','')))

# Process Object IDs
print("INFO: Processing Object IDs...")

i = j = k = 0
tmp2 = []
for i in range(len(objectID)):
    idNumber = getIDNumber(i)

    for actorNode in root.iter('Actor'):
        tmp = actorNode.get('Object')
        
        if tmp == idNumber:
            actorNode.set('ObjectID', objectID.get(idNumber))
            # actorNode.set('ObjectName', objectNames.get(objectID.get(idNumber)))

        elif tmp is not None and tmp.find(',') != -1:
            tmp2 = tmp.split(',')

            for k in range(len(objectID)):
                for j in range(len(tmp2)):
                    if tmp2[j] == getIDNumber(k):
                        tmp2[j] = objectID.get(getIDNumber(k))

            if len(tmp2) == 2: actorNode.set('ObjectID', tmp2[0] + ',' + tmp2[1])
            if len(tmp2) == 3: actorNode.set('ObjectID', tmp2[0] + ',' + tmp2[1] + ',' + tmp2[2])

# Process Categories
print("INFO: Processing Actor categories...")

i = 0
for i in range(len(actorCat)):
    iStr = f"{i}"
    for actorNode in root:
        if actorNode.get('Category') == iStr:
            actorNode.set('Category', actorCat.get(iStr))

# Generate the properties lists
listProp, listProp2, listPropNames, listPropTarget = [], [], [], []
def processProperties(attr):
    '''Creates lists containing properties, names and target'''
    global root
    i = j = 0
    for actorNode in root:
        if attr != 'Properties':
            global listPropNames
            global listPropTarget

            prop = actorNode.get(attr)
            if prop is not None:
                if prop.find(',') == -1:
                    if attr == 'PropertiesNames': listPropNames.append(prop)
                    if attr == 'PropertiesTarget': listPropTarget.append(prop)
                else:
                    tmp = prop.split(',')
                    for j in range(len(tmp)):
                        if tmp[j] == 'Var': tmp[j] = 'Params'
                    if attr == 'PropertiesNames': listPropNames.append(tmp)
                    if attr == 'PropertiesTarget': listPropTarget.append(tmp)
            else:
                if attr == 'PropertiesNames': listPropNames.append("None")
                if attr == 'PropertiesTarget': listPropTarget.append("None")

        elif attr == 'Properties':
            global listProp
            global listProp2

            listProp.append(actorNode.get(attr))
            if i < len(listProp):
                if listProp[i] is not None:
                    strProp = f"{listProp[i]}"

                    if strProp.find(',') != -1:
                        tmp = strProp.split(',')
                        for j in range(len(tmp)):
                            tmp[j] = '0x' + tmp[j]
                        listProp2.append(tmp)
                    else: listProp2.append('0x' + strProp)
                else:
                    listProp2.append('0x0000')
        i += 1

processProperties('Properties')
processProperties('PropertiesNames')
processProperties('PropertiesTarget')

# --- Change the structure of the file --- #

i = j = 0
def genElem(actorNode, string, attr, attr2, name, target, value, j):
    '''This function generates new sub-elements for the XML'''
    propName = propTarget = propValue = ''

    # Looking for lists
    if isinstance(name, list) is False:
        propName = name
        if target == 'None': propTarget = 'None'
        else: propTarget = target
        propValue = value

    elif isinstance(name, list) is True:
        propName = name[j]
        if target != 'None' and j < len(target): propTarget = target[j]
        else: propTarget = 'None'
        propValue = value[j]

    # Actual creation of the sub-element
    if propName.startswith(string) and attr != 'Property':
        i = 1
        if propName != 'None':
            ET.SubElement(actorNode, attr, { 'Mask' : propValue } )
            for elem in actorNode.iter(attr):
                if elem.get('Type') is None:
                    elem.set('Type', attr2)
                    if propTarget != 'None': elem.set('Target', propTarget)
                    if string == 'Switch Flag ' and elem.get('Flag') == propValue: elem.text = propName
                if string.startswith('Switch '):
                    elem.set('Index', f'{i}')
                    i += 1

    # The default name is 'Property'
    elif attr == 'Property':
        k = 1
        if propName != 'None':
            ET.SubElement(actorNode, attr, { attr2 : propValue } )
            for elem in actorNode.iter(attr):
                if elem.get('Name') is None:
                    if propName != 'None': elem.set('Name', propName)
                    if propTarget != 'None': elem.set('Target', propTarget)
                if elem.get('Name') != 'None':
                    elem.set('Index', f'{k}')
                    k += 1

print("INFO: Creating new sub-elements...")
for actorNode in root:
    # Generate the sub-elements
    propName = listPropNames[i]
    isNoneHere = 0 # Need this because of the for loop when handling lists

    if propName != 'None':
        # If the current element is not a list
        if isinstance(propName, list) is False:
            # Generate the sub-elements SwitchFlag, ChestFlag and by default, Property
            if propName == 'Switch Flag': genElem(actorNode, 'Switch Flag', 'Flag', 'Switch', propName, listPropTarget[i], listProp2[i], None)
            elif propName.startswith('Switch Flag '): genElem(actorNode, 'Switch Flag ', 'Flag', 'Switch', propName, listPropTarget[i], listProp2[i], None)
            
            elif propName == 'Chest Flag': genElem(actorNode, 'Chest Flag', 'Flag', 'Chest', propName, listPropTarget[i], listProp2[i], None)
            
            elif propName == 'Collectible Flag': genElem(actorNode, 'Collectible Flag', 'Flag', 'Collectible', propName, listPropTarget[i], listProp2[i], None)
            elif propName.startswith('Collectible Flag '): genElem(actorNode, 'Collectible Flag ', 'Flag', 'Collectible', propName, listPropTarget[i], listProp2[i], None)
            
            elif propName == 'Collectible Item': genElem(actorNode, 'Collectible Item', 'Collectible', 'Drop', propName, listPropTarget[i], listProp2[i], None)            
            elif propName == 'Collectible to Spawn': genElem(actorNode, 'Collectible to Spawn', 'Collectible', 'Drop', propName, listPropTarget[i], listProp2[i], None)
            elif propName == 'Collectible Var': genElem(actorNode, 'Collectible Var', 'Collectible', 'Drop', propName, listPropTarget[i], listProp2[i], None)

            elif propName.startswith('Content'): genElem(actorNode, 'Content', 'Item', 'ChestContent', propName, listPropTarget[i], listProp2[i], None)

            else: 
                ET.SubElement(actorNode, 'Property', { 'Mask' : '0x0000', 'Name' : 'None' } )
                genElem(actorNode, 'Property', 'Property', 'Mask', propName, listPropTarget[i], listProp2[i], None)

        # If the current element is a list
        elif isinstance(propName, list):
            # Generate the same sub-elements but now we're dealing with lists of strings
            for j in range(len(propName)):
                if propName[j] == 'Switch Flag': genElem(actorNode, 'Switch Flag', 'Flag', 'Switch', propName, listPropTarget[i], listProp2[i], j)
                elif propName[j].startswith('Switch Flag '): genElem(actorNode, 'Switch Flag ', 'Flag', 'Switch', propName, listPropTarget[i], listProp2[i], j)
                
                elif propName[j] == 'Chest Flag': genElem(actorNode, 'Chest Flag', 'Flag', 'Chest', propName, listPropTarget[i], listProp2[i], j)
                
                elif propName[j] == 'Collectible Flag': genElem(actorNode, 'Collectible Flag', 'Flag', 'Collectible', propName, listPropTarget[i], listProp2[i], j)
                elif propName[j].startswith('Collectible Flag '): genElem(actorNode, 'Collectible Flag ', 'Flag', 'Collectible', propName, listPropTarget[i], listProp2[i], j)
                
                elif propName[j] == 'Collectible Item': genElem(actorNode, 'Collectible Item', 'Collectible', 'Drop', propName, listPropTarget[i], listProp2[i], j)            
                elif propName[j] == 'Collectible to Spawn': genElem(actorNode, 'Collectible to Spawn', 'Collectible', 'Drop', propName, listPropTarget[i], listProp2[i], j)
                elif propName[j] == 'Collectible Var': genElem(actorNode, 'Collectible Var', 'Collectible', 'Drop', propName, listPropTarget[i], listProp2[i], j)

                elif propName[j].startswith('Content'): genElem(actorNode, 'Content', 'Item', 'ChestContent', propName, listPropTarget[i], listProp2[i], j)                
                
                else: 
                    if isNoneHere == 0:
                        ET.SubElement(actorNode, 'Property', { 'Mask' : '0x0000', 'Name' : 'None' } )
                        isNoneHere = 1
                    genElem(actorNode, 'Property', 'Property', 'Mask', propName, listPropTarget[i], listProp2[i], j)
    i += 1

    # Clean-Up
    for elem in actorNode.iter('Variable'):
        elem.tag = 'Parameter'
        elem.set('Params', elem.get('Var'))
        elem.attrib.pop('Var', None)
        if elem.get('Mask') == '0xFFFF':
            elem.attrib.pop('Mask', None)

    for elem in actorNode:
        if elem.tag == 'Notes':
            # TODO: format the notes properly
            notes = elem.text
            actorNode.remove(elem)
            ET.SubElement(actorNode, 'Notes', {}).text = notes

    actorNode.attrib.pop('Object', None)
    actorNode.attrib.pop('Properties', None)
    actorNode.attrib.pop('PropertiesNames', None)
    actorNode.attrib.pop('PropertiesTarget', None)

# From Property to Bool
i = 0
checkBoxKeys = [key for key in checkBox.keys()]
checkBoxVals = [val.split(',') for val in checkBox.values()]
for actorNode in root:
    if i < len(checkBoxKeys) and actorNode.get('ID') == checkBoxKeys[i]:
        for elem in actorNode:
            if elem.tag == 'Property':
                for j in range(len(checkBoxVals)):
                    for k in range(len(checkBoxVals[j])):
                        if checkBoxVals[j][k] == elem.get('Index'):
                            elem.tag = 'Bool'
        i += 1

# Add tied elements, used to determine which actor needs which props
# Format: <ElemTag Index="1" Mask="0x0010" Name="Toggle" Subscribe=";1,2,3"
i = 0
subKeys = list(subscribe.keys())
for actorNode in root:
    actorID = actorNode.get('ID')
    if i < len(subKeys) and actorID == subKeys[i]:
        j = 0
        keys = list(subscribe[actorID].keys())
        for elemNode in actorNode:
            params = elemNode.get('Params')
            settings = None
            for j in range(len(keys)):
                if params is not None and params == keys[j]:
                    settings = subscribe[actorID][params]
                    elemNode.set('TiedTarget', f'{settings[1]}')
                    elemNode.set('TiedMask', f'{settings[0]}')
        i += 1

# Add additional lists
def addList(name, list):
    root.append(ET.Element('List'))
    for node in root:
        if node.tag == 'List' and node.get('Name') is None:
            node.set('Name', name)
            for i in range(len(list)):
                node.append(ET.Element('Item'))
    for node in root:
        if node.tag == 'List' and node.get('Name') == name:
            i = 0
            for elem in node:
                if i < len(list):
                    elem.set('Name', list[i][0])
                    elem.set('Value', list[i][1])
                    i += 1

addList('En_Wonder_Item Drops', wonderList)
addList('Collectibles', item00List)
addList('Chest Content', chestList)

# --- Write the new file ---
print("INFO: Writing the file...")
# Formatting
xmlStr = MD.parseString(ET.tostring(root)).toprettyxml(indent="  ", encoding='UTF-8')
xmlStr = b'\n'.join([s for s in xmlStr.splitlines() if s.strip()])

# Writing
try:
    with open('./ActorList.xml', 'bw') as f:
        f.write(xmlStr)
except:
    print("ERROR: The file can't be written. Update the permissions, this folder is probably read-only.")
    exit()
