import xml.etree.ElementTree as ET, xml.dom.minidom as MD
from sys import exit
from collections import OrderedDict

try:
    from lists import actors as actorID, objects as objectID, categories as actorCat, objectsNames as objectNames, checkBox, \
        ootElfMsgMessages, ootEnItem00Drop as item00List, ootEnBoxContent as chestList, tiedParams, actionList
except:
    print("ERROR: File 'lists.py' is missing. You can find it on Github: https://github.com/Yanis42/actorlist-fixer")
    exit()

try:
    tree = ET.parse('./ActorNames.xml')
except:
    print("ERROR: File 'ActorNames.xml' is missing. You can find it in SO's (1.30) XML folder.")
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
            actorNode.set('Name', actorNode.get('Name'))
            actorNode.set('Key', (actorNode.get('ID').lower().replace('actor_', '')))

# Process Object IDs
# TODO: fix process time for objects
print("INFO: Processing Object IDs...")

i = j = k = 0
tmp2 = []
for i in range(len(objectID)):
    idNumber = getIDNumber(i)

    for actorNode in root.iter('Actor'):
        tmp = actorNode.get('Object')
        
        if tmp == idNumber:
            actorNode.set('ObjectKey', objectID.get(idNumber).lower().replace('object_', 'obj_'))
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
                    if attr2 is not None: elem.set('Type', attr2)
                    if propTarget != 'None': elem.set('Target', propTarget)
                    if string.endswith('Flag '): elem.set('Name', propName)
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
                if elem.get('Name') is not None:
                    elem.set('Index', f'{k}')
                    k += 1

print("INFO: Creating new sub-elements...")
# Variable -> Parameter, Var -> Params
for actorNode in root:
    for elem in actorNode.iter('Variable'):
        elem.tag = 'Parameter'
        elem.set('Params', elem.get('Var'))
        elem.attrib.pop('Var', None)
        if elem.get('Mask') == '0xFFFF':
            elem.attrib.pop('Mask', None)

# Add <Type>
for actorNode in root:
    for elem in actorNode:
        if elem.tag == 'Parameter':
            mask = elem.get('Mask')
            dict = { 'Index': "1" }
            if mask is not None:
                dict |= { 'Mask': mask }
    for elem in actorNode:
        if elem.tag == 'Parameter':
            ET.SubElement(actorNode, 'Type', dict)
            break

# Add <Item> to <Type>
for actorNode in root:
    for elem in actorNode:
        if elem.tag == 'Parameter':
            params = elem.get('Params')
            dict = {}
            if params is not None:
                dict = { 'Params': params }
            for a in root:
                for e in a:
                    if a.get('ID') == actorNode.get('ID') and e.tag == 'Type':
                        ET.SubElement(e, 'Item', dict).text = elem.text

# Remove <Parameter>
for actorNode in root:
    for elem in actorNode.findall('Parameter'):
        actorNode.remove(elem)

# Generate the sub-elements
for actorNode in root:
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

            elif propName.startswith('Content'): genElem(actorNode, 'Content', 'ChestContent', None, propName, listPropTarget[i], listProp2[i], None)

            else: genElem(actorNode, 'Property', 'Property', 'Mask', propName, listPropTarget[i], listProp2[i], None)

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

                elif propName[j].startswith('Content'): genElem(actorNode, 'Content', 'ChestContent', None, propName, listPropTarget[i], listProp2[i], j)
                
                else: genElem(actorNode, 'Property', 'Property', 'Mask', propName, listPropTarget[i], listProp2[i], j)
    i += 1

    # Clean-Up
    actorNodeID = actorNode.get('ID')
    for elem in actorNode:
        if elem.tag == 'Notes':
            # TODO: format the notes properly
            notes = elem.text
            actorNode.remove(elem)
            ET.SubElement(actorNode, 'Notes', {}).text = notes

    for elem in actorNode:
        if actorNodeID == 'ACTOR_EN_BOX' or \
            actorNodeID == 'ACTOR_EN_RD' or \
            actorNodeID == 'ACTOR_EN_SW' or \
            actorNodeID == 'ACTOR_ELF_MSG' or \
            actorNodeID == 'ACTOR_EN_OKARINA_TAG' or \
            actorNodeID == 'ACTOR_OBJ_TIMEBLOCK' or \
            actorNodeID == 'ACTOR_DOOR_ANA' or \
            actorNodeID == 'ACTOR_OBJ_TSUBO':
            if elem.tag == 'Notes':
                actorNode.remove(elem)

    actorNode.attrib.pop('Object', None)
    actorNode.attrib.pop('Properties', None)
    actorNode.attrib.pop('PropertiesNames', None)
    actorNode.attrib.pop('PropertiesTarget', None)

# From Property to Bool
i = 0
actorKeys = list(checkBox.keys())
for actorNode in root:
    actorID = actorNode.get('ID')
    for i in range(len(actorKeys)):
        if actorID == actorKeys[i]:
            for elem in actorNode:
                if elem.tag == 'Property':
                    index = checkBox[actorID]

                    if index.find(',') != -1:
                        listIndex = index.split(',')
                    else: 
                        listIndex = [index]

                    elemIndex = elem.get('Index')
                    if len(listIndex) == 1 and listIndex[0] == elemIndex:
                        elem.tag = 'Bool'
                    else:
                        for k in range(len(listIndex)):
                            if listIndex[k] == elemIndex:
                                elem.tag = 'Bool'

# Fix Indexes
def fixIndexes():
    for actorNode in root:
        i = j = k = l = 1
        for elem in actorNode:
            if elem.tag == 'Bool':
                elem.set('Index', f'{i}')
                i += 1
            elif elem.tag == 'Property':
                elem.set('Index', f'{j}')
                j += 1
            elif elem.tag == 'Flag':
                elem.set('Index', f'{k}')
                k += 1
            elif elem.tag == 'Collectible':
                elem.set('Index', f'{l}')
                l += 1

fixIndexes()

# Add enums
actionKeys = list(actionList.keys())
for actorNode in root:
    actorID = actorNode.get('ID')
    actorHasEnum = False
    for i in range(len(actionKeys)):
        if actorID == actionKeys[i]:
            listKeys = actionList[actorID].keys()
            lenKeys = len(listKeys) + 1
            for elem in actorNode:
                for j in range(1, lenKeys):
                    name = actionList[actorID][j][0]
                    tag = actionList[actorID][j][1]
                    mask = actionList[actorID][j][2]
                    param = actionList[actorID][j][3]
                    index = actionList[actorID][j][4]
                    target = actionList[actorID][j][5]
                    if elem.tag == tag and elem.get('Index') == index:
                        if param != "":
                            attrib = {'Name': name, 'Index': f'{j}', 'TiedParam': param, 'Target': target, 'Mask': mask}
                        else:
                            attrib = {'Name': name, 'Index': f'{j}', 'Target': target, 'Mask': mask}
                        actorNode.append(ET.Element('Enum', attrib))
                        actorHasEnum = True

            for elem in actorNode:
                elemIndex = elem.get('Index')
                if elem.tag == 'Enum' and elemIndex is not None:
                    for j in range(1, lenKeys):
                        if elemIndex == f'{j}':
                            index = actionList[actorID][j][4]
                            actions = actionList[actorID][j][6]
                            values = actionList[actorID][j][7]
                            for k in range(len(actions)):
                                attrib = {'Name': actions[k], 'Value': values[k]}
                                elem.append(ET.Element('Item', attrib))

            for elem in actorNode:
                if elem.tag == 'Property' and actorHasEnum:
                    actorNode.set('HasEnum', 'True')

    if actorID == 'ACTOR_ELF_MSG' or actorID == 'ACTOR_ELF_MSG2':
        for elem in actorNode:
            if elem.tag == 'Property' and elem.get('Name').startswith('Message'):
                elem.tag = 'Message'

# Remove doublons
for actorNode in root:
    if actorNode.get('HasEnum') == 'True':
        length = '1'
        for elem in actorNode:
            if elem.tag == 'Enum':
                length = elem.get('Index')

        for i in range(int(length)):
            for elem in actorNode:
                if elem.tag != 'Parameter':
                    name1 = elem.get('Name')
                    if elem.tag == 'Enum':
                        for elem2 in actorNode:
                            if elem2.tag != 'Enum' and elem2.tag != 'Parameter':
                                name2 = elem2.get('Name')
                                if name1 == name2:
                                    actorNode.remove(elem2)

fixIndexes()

for actorNode in root:
    for elem in actorNode:
        name = elem.get('Name')
        if elem.tag != 'Enum' and name is not None and name.startswith('Collectible') and (name.endswith('Drop') or name.endswith('Type')):
            elem.tag = 'Collectible'
            elem.set('Type', 'Drop')

fixIndexes()

# Add tied elements, used to determine which actor needs which props
# Format: <ElemTag Index="1" Mask="0x0010" Name="Toggle" Subscribe=";1,2,3"
# Format: <ElemTag Index="1" Mask="0x0010" Name="Toggle" Subscribe=";1,2,3"
i = 0
actorKeys = list(tiedParams.keys())
for actorNode in root:
    actorID = actorNode.get('ID')
    for i in range(len(actorKeys)):
        if actorID == actorKeys[i]:
            listKeys = tiedParams[actorID].keys()
            for elem in actorNode:
                elemIndex = elem.get('Index')
                for j in range(1, len(listKeys) + 1):
                    params = tiedParams[actorID][j][0]
                    tag = tiedParams[actorID][j][1]
                    index = tiedParams[actorID][j][2]

                    if tag.find(',') != -1:
                        listTag = tag.split(',')
                        listIndex = index.split(',')
                    else:
                        listTag = [tag]
                        listIndex = [index]

                    if len(listTag) == 1 and listTag[0] == elem.tag and listIndex[0] == elemIndex:
                        elem.set('TiedParam', params)
                    else:
                        for k in range(len(listTag)):
                            if listIndex[k] == elemIndex and listTag[k] == elem.tag:
                                elem.set('TiedParam', params)

fixIndexes()

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

addList('Elf_Msg Message ID', ootElfMsgMessages)
addList('Collectibles', item00List)
addList('Chest Content', chestList)

# sorting attributes
for actorNode in root:
    if actorNode.tag == 'Actor':
        actorNode.attrib = OrderedDict(sorted(actorNode.attrib.items()))
        for elem in actorNode:
            elem.attrib = OrderedDict(sorted(elem.attrib.items()))

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
