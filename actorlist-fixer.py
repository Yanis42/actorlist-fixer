import xml.etree.ElementTree as ET
import xml.dom.minidom as MD
from lists import actors as actorID, objects as objectID


tree = ET.parse('./ActorNames.xml')
root = tree.getroot()

# TODO: add a subelement for items (chest content, collectibles), rename categories (ex: 5 -> Ennemy)

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
i = 0
for i in range(len(actorID)):
    idNumber = getIDNumber(i)
    for actorNode in root:
        if actorNode.get('Key') == idNumber:
            actorNode.set('ID', actorID.get(idNumber))

# Process Object IDs
i = j = k = 0
tmp2 = []
for i in range(len(objectID)):
    idNumber = getIDNumber(i)

    for actorNode in root.iter('Actor'):
        tmp = actorNode.get('Object')
        
        if tmp == idNumber:
            actorNode.set('ObjectID', objectID.get(idNumber))

        elif tmp is not None and tmp.find(',') != -1:
            tmp2 = tmp.split(',')

            for k in range(len(objectID)):
                for j in range(len(tmp2)):
                    if tmp2[j] == getIDNumber(k):
                        tmp2[j] = objectID.get(getIDNumber(k))

            if len(tmp2) == 2: actorNode.set('ObjectID', tmp2[0] + ',' + tmp2[1])
            if len(tmp2) == 3: actorNode.set('ObjectID', tmp2[0] + ',' + tmp2[1] + ',' + tmp2[2])

# Renaming stuff
for actorNode in root:
    for elem in actorNode.iter('Variable'):
        elem.tag = 'Parameter'
        elem.set('ParamValue', elem.get('Var'))
        elem.attrib.pop('Var', None)

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

    # If j is None then name, target and value aren't lists
    if j is not None and j < len(target):
        propName = name[j]
        propTarget = target[j]
        propValue = value[j]
    elif j is None:
        print("saucisse")
        propName = name
        propTarget = target
        propValue = value

    # Check if propName contains the string from the function's parameters
    if propName.startswith(string) and attr != 'Property':
        ET.SubElement(actorNode, attr, { attr2 : propValue } )
        for elem in actorNode.iter(attr):
            if propTarget != 'None': elem.set('Target', propTarget)
            if string == 'Switch Flag ' and elem.get('Flag') == propValue: elem.text = propName

    # If we're supposed to add a Property
    elif attr == 'Property':
        if propName != 'None': ET.SubElement(actorNode, attr, { attr2 : propValue } )
        for elem in actorNode.iter(attr):
            if elem.get(attr2) == propValue:
                if propName != 'None': elem.set('Name', propName)
                if propTarget != 'None': elem.set('Target', propTarget)

for actorNode in root:
    # Generate the sub-elements
    propName = listPropNames[i]

    if propName != 'None':
        # If the current element is not a list
        if isinstance(propName, list) is False:
            # Generate the sub-elements SwitchFlag, ChestFlag and by default, Property
            if propName == 'Switch Flag': genElem(actorNode, 'Switch Flag', 'SwitchFlag', 'Flag', propName, listPropTarget[i], listProp2[i], None)
            elif propName.startswith('Switch Flag '): genElem(actorNode, 'Switch Flag ', 'SwitchFlag', 'Flag', propName, listPropTarget[i], listProp2[i], None)
            elif propName == 'Chest Flag': genElem(actorNode, 'Chest Flag', 'ChestFlag', 'Flag', propName, listPropTarget[i], listProp2[i], None)
            else: genElem(actorNode, 'Property', 'Property', 'Mask', propName, listPropTarget[i], listProp2[i], None)

        # If the current element is a list
        elif isinstance(propName, list):
            # Generate the same sub-elements but now we're dealing with lists containing strings instead of strings
            for j in range(len(propName)):
                if propName[j] == 'Switch Flag': genElem(actorNode, 'Switch Flag', 'SwitchFlag', 'Flag', propName, listPropTarget[i], listProp2[i], j)
                elif propName[j].startswith('Switch Flag '): genElem(actorNode, 'Switch Flag ', 'SwitchFlag', 'Flag', propName, listPropTarget[i], listProp2[i], j)
                elif propName[j] == 'Chest Flag': genElem(actorNode, 'Chest Flag', 'ChestFlag', 'Flag', propName, listPropTarget[i], listProp2[i], j)
                else: genElem(actorNode, 'Property', 'Property', 'Mask', propName, listPropTarget[i], listProp2[i], j)
    i += 1

for actorNode in root:
    # Move the notes
    for elem in actorNode:
        if elem.find('Notes'):
            notes = elem.text
            actorNode.remove(elem)
            ET.SubElement(actorNode, 'Notes', {}).text = notes

    # Remove the useless attributes
    actorNode.attrib.pop('Key', None)
    actorNode.attrib.pop('Object', None)
    actorNode.attrib.pop('Properties', None)
    actorNode.attrib.pop('PropertiesNames', None)
    actorNode.attrib.pop('PropertiesTarget', None)

# --- Write the new file ---

# Formatting
xmlStr = MD.parseString(ET.tostring(root)).toprettyxml(indent="  ", encoding='UTF-8')
xmlStr = b'\n'.join([s for s in xmlStr.splitlines() if s.strip()])

# Writing
with open('./ActorList.xml', 'bw') as f:
    f.write(xmlStr)
